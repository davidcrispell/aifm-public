"""Adapter for the public AI Futures Model used by the BAIS homepage."""
import math
import sys
from dataclasses import fields
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from progress_model import Parameters, ProgressModel, config, load_time_series_data

DOUBLINGS = [n / 2 for n in range(6, 15)]
TASTES = [n / 10 for n in range(12, 37, 3)]
# This is the released config used for upstream's golden trajectory. The bare
# Parameters() constructor has different defaults for taste and CES accuracy.
DEFAULTS = {field.name: config.DEFAULT_PARAMETERS[field.name] for field in fields(Parameters)
            if field.init and field.name in config.DEFAULT_PARAMETERS}
BASE = [DEFAULTS["excess_uplift_doubling_time"], DEFAULTS["ai_research_taste_slope"]]
MILESTONES = {"ac": "AC", "sar": "SAR-level-experiment-selection-skill"}
COMMIT = "1c40ecdb246c25980515441a66571931c5604e11"


@lru_cache(maxsize=1)
def input_data():
    return load_time_series_data(str(ROOT / "inputs/input_data.csv"))


@lru_cache(maxsize=128)
def trajectory(doubling, taste):
    if not (DOUBLINGS[0] <= doubling <= DOUBLINGS[-1] and TASTES[0] <= taste <= TASTES[-1]):
        raise ValueError("Inputs outside the forecast controls")
    settings = dict(DEFAULTS, excess_uplift_doubling_time=doubling, ai_research_taste_slope=taste)
    model = ProgressModel(Parameters(**settings), input_data())
    model.compute_progress_trajectory([2015.0, 2050.0])
    results = model.results
    points = []
    for year, judgment, coding in zip(results["times"], results["ai_research_taste_quantile"],
                                      results["automation_fraction"], strict=True):
        if 2026 <= year <= 2030:
            points.append([round(float(year), 4), round(100 * float(judgment), 7),
                           round(100 * float(coding), 7)])
    dates = {}
    for key, code in MILESTONES.items():
        value = results["milestones"][code]["time"]
        dates[key] = None if value is None or not math.isfinite(value) else float(value)
    return {"points": points, **dates}
