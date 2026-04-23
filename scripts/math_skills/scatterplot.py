import math
import random
import sympy as sp
from sympy import symbols, solve, sqrt, Rational
from .core import (
    param_hash, fmt_num, fmt_fn, fmt_fx, fmt_lin_rhs,
    spr_bounds, make_distractors, pick_scenario, validate_math_object,
    PYTH_TRIPLES, LWP_SCENARIOS, PCT_SCENARIOS, RAT_SCENARIOS, PRP_SCENARIOS,
)

# ── Generator: scatterplot_analysis ──────────────────────────────────────────

SCA_SCENARIOS = ["study_hours", "temperature_sales", "height_weight",
                 "age_income", "practice_score"]


def gen_scatterplot_analysis(difficulty: int, rng_obj: random.Random, exclude_params: set,
                              exclude_scenarios: set, **_):
    for _ in range(200):
        scenario = rng_obj.choice([s for s in SCA_SCENARIOS if s not in exclude_scenarios] or SCA_SCENARIOS)
        m = rng_obj.choice([1, 2, -1, -2])
        b_intercept = rng_obj.randint(5, 20)
        x_start = rng_obj.randint(1, 5)
        xs = [x_start + i for i in range(6)]
        ys = [m * x + b_intercept + rng_obj.randint(-2, 2) for x in xs]

        if difficulty == 1:
            idx = rng_obj.randint(0, 5)
            params = {"points": list(zip(xs, ys)), "m": m, "b": b_intercept,
                      "highlight": idx, "scenario": scenario, "d": 1}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(ys[idx])
            diag = {"type": "scatter_plot", "points": [[xs[i], ys[i]] for i in range(6)],
                    "trend_line": None, "xlabel": "X", "ylabel": "Y",
                    "highlight_idx": idx, "outlier_idx": None}
            distractors = make_distractors(ans, [str(ys[idx] + 2), str(ys[idx] - 3), str(xs[idx])])
            return _sca(1, params, ph, ans, diag, distractors, "mcq", scenario)
        elif difficulty == 2:
            direction = "positive" if m > 0 else "negative"
            params = {"points": list(zip(xs, ys)), "m": m, "b": b_intercept,
                      "scenario": scenario, "d": 2}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = direction
            diag = {"type": "scatter_plot", "points": [[xs[i], ys[i]] for i in range(6)],
                    "trend_line": {"slope": m, "intercept": b_intercept},
                    "xlabel": "X", "ylabel": "Y", "highlight_idx": None, "outlier_idx": None}
            other = "negative" if direction == "positive" else "positive"
            d2 = [other, "no correlation", "nonlinear"]
            return _sca(2, params, ph, ans, diag, d2, "mcq", scenario)
        elif difficulty == 3:
            x_query = xs[-1] + 2
            y_est = m * x_query + b_intercept
            params = {"points": list(zip(xs, ys)), "m": m, "b": b_intercept,
                      "x_query": x_query, "scenario": scenario, "d": 3}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(y_est)
            diag = {"type": "scatter_plot", "points": [[xs[i], ys[i]] for i in range(6)],
                    "trend_line": {"slope": m, "intercept": b_intercept},
                    "xlabel": "X", "ylabel": "Y", "highlight_idx": None, "outlier_idx": None}
            distractors = make_distractors(ans, [str(y_est + 3), str(y_est - 4), str(y_est + m)])
            return _sca(3, params, ph, ans, diag, distractors, "mcq", scenario)
        elif difficulty == 4:
            outlier_idx = rng_obj.randint(0, 5)
            ys_with_outlier = list(ys)
            ys_with_outlier[outlier_idx] += rng_obj.choice([-12, -10, 10, 12])
            params = {"points": list(zip(xs, ys_with_outlier)), "m": m, "b": b_intercept,
                      "outlier_idx": outlier_idx, "scenario": scenario, "d": 4}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = f"{xs[outlier_idx]},{ys_with_outlier[outlier_idx]}"
            diag = {"type": "scatter_plot",
                    "points": [[xs[i], ys_with_outlier[i]] for i in range(6)],
                    "trend_line": {"slope": m, "intercept": b_intercept},
                    "xlabel": "X", "ylabel": "Y", "highlight_idx": None, "outlier_idx": outlier_idx}
            other_idx = (outlier_idx + 1) % 6
            d2 = [f"{xs[other_idx]},{ys_with_outlier[other_idx]}",
                  f"{xs[(outlier_idx + 2) % 6]},{ys_with_outlier[(outlier_idx + 2) % 6]}",
                  f"{xs[(outlier_idx + 3) % 6]},{ys_with_outlier[(outlier_idx + 3) % 6]}"]
            return _sca(4, params, ph, ans, diag, d2, "mcq", scenario)
        elif difficulty == 5:
            params = {"points": list(zip(xs, ys)), "m": m, "b": b_intercept,
                      "scenario": scenario, "d": 5}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            # Answer encodes correct interpretation of slope sign
            ans = "positive" if m > 0 else "negative"
            diag = {"type": "scatter_plot", "points": [[xs[i], ys[i]] for i in range(6)],
                    "trend_line": {"slope": m, "intercept": b_intercept},
                    "xlabel": "X", "ylabel": "Y", "highlight_idx": None, "outlier_idx": None}
            other = "negative" if ans == "positive" else "positive"
            d2 = [other, "no relationship", "quadratic relationship"]
            return _sca(5, params, ph, ans, diag, d2, "mcq", scenario)
        raise RuntimeError(f"Could not generate unique params for scatterplot_analysis d{difficulty}")
    raise RuntimeError(f"Could not generate unique params for scatterplot_analysis d{difficulty}")


def _sca(d, params, ph, ans, diag, distractors, qt="mcq", scenario=None):
    return {"skill": "scatterplot_analysis", "difficulty": d, "questionType": "mcq",
            "params": params, "paramHash": ph, "verifiedAnswer": ans,
            "distractors": distractors, "sprMin": None, "sprMax": None,
            "scenarioTag": scenario, "diagramSpec": diag, "questionContext": ""}
