import math
import random
import sympy as sp
from sympy import symbols, solve, sqrt, Rational
from .core import (
    param_hash, fmt_num, fmt_fn, fmt_fx, fmt_lin_rhs,
    spr_bounds, make_distractors, pick_scenario, validate_math_object,
    PYTH_TRIPLES, LWP_SCENARIOS, PCT_SCENARIOS, RAT_SCENARIOS, PRP_SCENARIOS,
)

# ── Generator: statistics ─────────────────────────────────────────────────────

STA_SCENARIOS = ["test_scores", "ages_team", "daily_temps", "quiz_grades", "heights_cm"]


def gen_statistics(difficulty: int, rng_obj: random.Random, exclude_params: set, **_):
    import math as _math
    for _ in range(200):
        if difficulty == 1:
            vals = sorted(rng_obj.sample(range(5, 30), 5))
            while sum(vals) % 5 != 0:
                vals = sorted(rng_obj.sample(range(5, 30), 5))
            mean = sum(vals) // 5
            params = {"vals": vals, "d": 1}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(mean)
            distractors = make_distractors(ans, [str(mean - 2), str(mean + 2), str(sum(vals))])
            return _sta(1, params, ph, ans, (None, None), None, distractors, "mcq",
                        f"Data set: {vals}")
        elif difficulty == 2:
            vals = sorted(rng_obj.sample(range(5, 40), 5))
            median = vals[2]
            params = {"vals": vals, "d": 2}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(median)
            distractors = make_distractors(ans, [str(vals[1]), str(vals[3]), str(sum(vals) // 5)])
            return _sta(2, params, ph, ans, (None, None), None, distractors, "mcq",
                        f"Data set: {vals}")
        elif difficulty == 3:
            vals = sorted(rng_obj.sample(range(5, 40), 6))
            mean_val = sum(vals) / 6
            median_val = (vals[2] + vals[3]) / 2
            params = {"vals": vals, "d": 3}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            if mean_val > median_val:
                ans = "mean"
                distractors = ["median", "equal", "cannot be determined"]
            elif median_val > mean_val:
                ans = "median"
                distractors = ["mean", "equal", "cannot be determined"]
            else:
                ans = "equal"
                distractors = ["mean", "median", "cannot be determined"]
            return _sta(3, params, ph, ans, (None, None), None, distractors, "mcq",
                        f"Data set: {vals}. Mean={round(mean_val,2)}, Median={median_val}")
        elif difficulty == 4:
            vals = sorted(rng_obj.sample(range(4, 50), 7))
            q1 = vals[1]   # median of lower half [0..2] = vals[1]
            med = vals[3]
            q3 = vals[5]   # median of upper half [4..6] = vals[5]
            iqr = q3 - q1
            params = {"vals": vals, "d": 4}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(iqr)
            diag = {"type": "box_plot", "min": vals[0], "q1": q1, "median": med,
                    "q3": q3, "max": vals[6]}
            distractors = make_distractors(ans, [str(iqr - 2), str(iqr + 3), str(vals[6] - vals[0])])
            qt = "spr" if rng_obj.random() < 0.4 else "mcq"
            sb = spr_bounds(ans) if qt == "spr" else (None, None)
            return _sta(4, params, ph, ans, sb, diag, distractors, qt,
                        f"Data set: {vals}")
        elif difficulty == 5:
            vals = rng_obj.sample(range(5, 25), 5)
            mean_v = sum(vals) / 5
            variance = sum((x - mean_v) ** 2 for x in vals) / 5
            stddev = round(_math.sqrt(variance), 2)
            params = {"vals": sorted(vals), "d": 5}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(stddev)
            distractors = make_distractors(ans, [
                str(round(stddev + 0.5, 2)),
                str(round(stddev + 1.1, 2)),
                str(round(variance, 2))])
            return _sta(5, params, ph, ans, (None, None), None, distractors, "mcq",
                        f"Data set: {vals}")
        raise RuntimeError(f"Could not generate unique params for statistics d{difficulty}")
    raise RuntimeError(f"Could not generate unique params for statistics d{difficulty}")


def _sta(d, params, ph, ans, spr_val, diag, distractors, qt="mcq", ctx=""):
    sb = spr_val if qt == "spr" else (None, None)
    return {"skill": "statistics", "difficulty": d, "questionType": qt,
            "params": params, "paramHash": ph, "verifiedAnswer": ans,
            "distractors": distractors if qt == "mcq" else [], "sprMin": sb[0], "sprMax": sb[1],
            "scenarioTag": None, "diagramSpec": diag, "questionContext": ctx}
