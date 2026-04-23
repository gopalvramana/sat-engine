import math
import random
import sympy as sp
from sympy import symbols, solve, sqrt, Rational
from .core import (
    param_hash, fmt_num, fmt_fn, fmt_fx, fmt_lin_rhs,
    spr_bounds, make_distractors, pick_scenario, validate_math_object,
    PYTH_TRIPLES, LWP_SCENARIOS, PCT_SCENARIOS, RAT_SCENARIOS, PRP_SCENARIOS,
)

# ── Generator: quadratic_functions ───────────────────────────────────────────

def gen_quadratic_functions(difficulty: int, rng_obj: random.Random, exclude_params: set, **_):
    for _ in range(200):
        if difficulty == 1:
            # y = x^2 + bx + c, b even so vertex x = -b/2 is integer
            b = rng_obj.choice([-8, -6, -4, -2, 2, 4, 6, 8])
            c = rng_obj.randint(-10, 10)
            h = -b // 2
            k = h * h + b * h + c
            params = {"a": 1, "b": b, "c": c, "h": h, "k": k, "d": 1}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(h)
            diag = {"type": "parabola", "a": 1, "h": h, "k": k, "vertex": [h, k],
                    "x_intercepts": None, "y_intercept": c}
            distractors = make_distractors(ans, [str(h + 1), str(h - 1), str(-h)])
            return _qfn(1, params, ph, ans, (None, None), diag, distractors, "mcq")
        elif difficulty == 2:
            b = rng_obj.choice([-8, -6, -4, -2, 2, 4, 6, 8])
            c = rng_obj.randint(-10, 10)
            h = -b // 2
            k = h * h + b * h + c
            params = {"a": 1, "b": b, "c": c, "h": h, "k": k, "d": 2}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(h)
            diag = {"type": "parabola", "a": 1, "h": h, "k": k, "vertex": [h, k],
                    "x_intercepts": None, "y_intercept": c}
            return _qfn(2, params, ph, ans, spr_bounds(ans), diag, [], "spr")
        elif difficulty == 3:
            h = rng_obj.randint(-5, 5)
            k = rng_obj.randint(-8, 8)
            params = {"a": 1, "h": h, "k": k, "form": "vertex", "d": 3}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(k)
            diag = {"type": "parabola", "a": 1, "h": h, "k": k, "vertex": [h, k],
                    "x_intercepts": None, "y_intercept": h * h + k}
            distractors = make_distractors(ans, [str(h), str(k + 2), str(-k)])
            return _qfn(3, params, ph, ans, (None, None), diag, distractors, "mcq")
        elif difficulty == 4:
            a = rng_obj.randint(1, 3)
            b = rng_obj.randint(-6, 6)
            c = rng_obj.randint(-10, 10)
            params = {"a": a, "b": b, "c": c, "d": 4}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(c)
            h = -b / (2 * a)
            k_val = a * h * h + b * h + c
            diag = {"type": "parabola", "a": a, "h": round(h, 2), "k": round(k_val, 2),
                    "vertex": [round(h, 2), round(k_val, 2)], "x_intercepts": None, "y_intercept": c}
            return _qfn(4, params, ph, ans, spr_bounds(ans), diag, [], "spr")
        elif difficulty == 5:
            r1 = rng_obj.randint(-5, 3)
            r2 = rng_obj.randint(r1 + 2, 6)
            larger = max(r1, r2)
            b_coef = -(r1 + r2)
            c_coef = r1 * r2
            h = (r1 + r2) / 2
            k_val = (r1 - r2) ** 2 / (-4)
            params = {"r1": r1, "r2": r2, "b": b_coef, "c": c_coef, "d": 5}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(larger)
            diag = {"type": "parabola", "a": 1, "h": h, "k": k_val,
                    "vertex": [h, k_val], "x_intercepts": [r1, r2], "y_intercept": c_coef}
            distractors = make_distractors(ans, [str(min(r1, r2)), str(larger + 1), str(abs(r1 - r2))])
            return _qfn(5, params, ph, ans, (None, None), diag, distractors, "mcq")
        raise RuntimeError(f"Could not generate unique params for quadratic_functions d{difficulty}")
    raise RuntimeError(f"Could not generate unique params for quadratic_functions d{difficulty}")


def _qfn(d, params, ph, ans, spr_val, diag, distractors, qt="mcq"):
    sb = spr_val if qt == "spr" else (None, None)
    return {"skill": "quadratic_functions", "difficulty": d, "questionType": qt,
            "params": params, "paramHash": ph, "verifiedAnswer": ans,
            "distractors": distractors if qt == "mcq" else [], "sprMin": sb[0], "sprMax": sb[1],
            "scenarioTag": None, "diagramSpec": diag, "questionContext": ""}
