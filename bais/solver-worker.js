// The worker runs the same Python entry point as the native server and exporter.
'use strict';
const runtimeURL = 'https://cdn.jsdelivr.net/pyodide/v0.29.3/full/';
let ready, newest = 0, runModel;

async function loadEngine(archive, baseline) {
  importScripts(runtimeURL + 'pyodide.js');
  const py = await loadPyodide({indexURL:runtimeURL});
  await py.loadPackage(['numpy', 'scipy', 'pyyaml']);
  const bytes = Uint8Array.from(atob(archive), char => char.charCodeAt(0));
  py.unpackArchive(bytes, 'zip', {extractDir:'/aifm'});
  runModel = py.runPython([
    'import json, logging, sys',
    'logging.disable(logging.INFO)',
    'sys.path.insert(0, "/aifm/bais")',
    'from engine import trajectory',
    'def run_json(d, t):',
    '    return json.dumps(trajectory(d,t), allow_nan=False)',
    'run_json'
  ].join('\n'));
  // Verify the numerical environment before displaying custom runs.
  const result = JSON.parse(runModel(...baseline.inputs));
  for (const milestone of ['ac','sar']) {
    if (!Number.isFinite(result[milestone]) || Math.abs(result[milestone] - baseline[milestone]) > 0.02) {
      throw new Error('Reference milestone mismatch');
    }
  }
}

self.onmessage = async ({data}) => {
  const id = newest = data.id;
  try {
    if (!ready) ready = loadEngine(data.archive, data.baseline);
    await ready;
    if (id !== newest) return;
    self.postMessage({id, phase:'running'});
    const run = JSON.parse(runModel(...data.pair));
    self.postMessage({id, run});
  } catch (error) {
    // The UI releases the failed worker so a subsequent retry loads a fresh runtime.
    self.postMessage({id, error:String(error)});
  }
};
