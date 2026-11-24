"""Build the offline BAIS forecast explorer or serve it with on-demand model runs."""
import argparse
import base64
import io
import json
import logging
import zipfile
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from engine import BASE, COMMIT, DOUBLINGS, ROOT, TASTES, trajectory

HERE = Path(__file__).resolve().parent
SITE = ROOT.parent if (ROOT.parent / "index.html").is_file() else HERE
PAGE = SITE / "hero-test.html"
TEMPLATE = HERE / "hero-test.template.html"


def engine_archive():
    files = [ROOT / "LICENSE", HERE / "engine.py", ROOT / "inputs/input_data.csv",
             ROOT / "inputs/metr/benchmark_results_1_1.yaml", *sorted((ROOT / "progress_model").glob("*.py"))]
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for path in files:
            info = zipfile.ZipInfo(path.relative_to(ROOT).as_posix())
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED)
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def refresh():
    if BASE[0] not in DOUBLINGS or BASE[1] not in TASTES:
        raise ValueError("Update the forecast controls to include the model baseline")
    runs = {f"{d:.1f}/{s:.1f}": trajectory(d, s) for d in DOUBLINGS for s in TASTES}
    data = {"base": BASE, "doublings": DOUBLINGS, "tastes": TASTES, "commit": COMMIT, "runs": runs}
    payload = json.dumps(data, allow_nan=False, separators=(",", ":"))
    html = TEMPLATE.read_text()
    for marker, value in (("{{AIFP_RUNS}}", payload), ("{{AIFP_ENGINE}}", engine_archive()),
                          ("{{AIFP_WORKER}}", (HERE / "solver-worker.js").read_text())):
        if html.count(marker) != 1:
            raise ValueError(f"Expected one {marker} in template")
        html = html.replace(marker, value)
    pending = PAGE.with_suffix(".html.tmp")
    pending.write_text(html)
    pending.replace(PAGE)
    print(f"Wrote {len(runs)} model trajectories to {PAGE}")


class HeroHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        request = urlsplit(self.path)
        if request.path == "/api/trajectory":
            try:
                query = parse_qs(request.query, strict_parsing=True)
                if set(query) != {"doubling", "taste"} or any(len(v) != 1 for v in query.values()):
                    raise ValueError("Provide one doubling and one taste input")
                run = trajectory(float(query["doubling"][0]), float(query["taste"][0]))
                body = json.dumps(run, allow_nan=False, separators=(",", ":")).encode()
            except (ValueError, OverflowError):
                self.send_error(400, "Invalid model inputs")
                return
            except Exception:
                logging.exception("AIFP trajectory failed")
                self.send_error(500, "Model calculation failed")
                return
            content_type = "application/json"
        elif request.path in ("/", "/hero-test.html"):
            body = PAGE.read_text().replace('data-live="false"', 'data-live="true"', 1).encode()
            content_type = "text/html; charset=utf-8"
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true", help="regenerate the embedded trajectories")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--site-dir", type=Path, default=SITE, help="folder containing the BAIS hero prototype")
    args = parser.parse_args()
    SITE = args.site_dir.resolve()
    PAGE = SITE / "hero-test.html"
    logging.disable(logging.INFO)
    if args.refresh:
        refresh()
    else:
        with HTTPServer(("127.0.0.1", args.port), HeroHandler) as server:
            print(f"BAIS hero preview with live forecasts at http://127.0.0.1:{server.server_port}/", flush=True)
            server.serve_forever()
