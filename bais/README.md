# BAIS hero prototype

The “Who builds the next AI?” hero uses the fork’s original `progress_model` Python solver and input series. The built preview is [public/bais/hero-test.html](../public/bais/hero-test.html). Open it directly or serve it as a static file. On a deployment of the fork, its path is `/bais/hero-test.html`.

## Build and run

From the root of this fork:

```sh
python3.14 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python bais/hero.py --refresh --site-dir public/bais
```

The exporter writes one self-contained `hero-test.html`. To rebuild the original BAIS prototype in place, pass the existing BAIS website directory to `--site-dir`. To use native Python for custom runs, launch `python bais/hero.py --site-dir public/bais` and open [the local preview](http://127.0.0.1:8765/).

## Calculations

Each preset pair of slider values has an embedded model run. Fine adjustments enable steps of 0.05. On the first off-grid request, the static preview loads Pyodide 0.29.3, NumPy, SciPy, and PyYAML from jsDelivr in a worker. The page carries the Python solver, inputs, adapter, and upstream MIT license in an embedded archive. The worker checks its baseline AC and SAR dates against the native reference before returning a custom run. All 81 preset runs are available offline. With the native server the same off-grid inputs go to the same Python function over HTTP.

The baseline uses the public release’s `config.DEFAULT_PARAMETERS`, restricted to constructor fields, and `inputs/input_data.csv`. These settings match the upstream default golden trajectory. The model uses the coding-productivity calibration for the automated coder milestone. Each run changes only `excess_uplift_doubling_time` and `ai_research_taste_slope`.

The engine integrates 2015–2050. The plot shows research judgment or coding automation at the model’s 0.1-year intervals from 2026 to 2030. The dates use the solver’s milestone times for `AC` and `SAR-level-experiment-selection-skill`. The dashed curve compares a selected scenario with the baseline. The two milestone dates are conditional outputs.
