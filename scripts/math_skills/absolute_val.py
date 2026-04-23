import math
import random
import sympy as sp
from sympy import symbols, solve, sqrt, Rational
from .core import (
    param_hash, fmt_num, fmt_fn, fmt_fx, fmt_lin_rhs,
    spr_bounds, make_distractors, pick_scenario, validate_math_object,
    PYTH_TRIPLES, LWP_SCENARIOS, PCT_SCENARIOS, RAT_SCENARIOS, PRP_SCENARIOS,
)

# ── Generator: absolute_value ─────────────────────────────────────────────────

def gen_absolute_value(difficulty: int, rng_obj: random.Random, exclude_params: set, **_):
    for _ in range(200):
        if difficulty == 1:
            a = rng_obj.randint(1, 12)
            params = {"a": a, "op": "abs_eq_simple"}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(a)
            return _abv(1, params, ph, ans, spr_bounds(ans), None, [], "spr")
        elif difficulty == 2:
            a_shift = rng_obj.randint(-6, 6)
            b_val = rng_obj.randint(2, 10)
            # |x + a_shift| = b_val → x = -a_shift ± b_val
            sol1 = -a_shift + b_val
            sol2 = -a_shift - b_val
            larger = max(sol1, sol2)
            params = {"a": a_shift, "b": b_val, "op": "abs_shift"}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(larger)
            distractors = make_distractors(ans, [str(min(sol1, sol2)), str(b_val), str(-a_shift)])
            diag = {"type": "number_line", "min": min(sol1, sol2) - 2, "max": larger + 2,
                    "boundary": [min(sol1, sol2), larger], "direction": "both",
                    "endpoint": "closed", "shaded_between": False}
            return _abv(2, params, ph, ans, (None, None), diag, distractors, "mcq")
        elif difficulty == 3:
            a_shift = rng_obj.randint(-6, 6)
            b_val = rng_obj.randint(2, 10)
            sol1 = -a_shift + b_val
            sol2 = -a_shift - b_val
            ans_sum = sol1 + sol2  # = -2 * a_shift
            params = {"a": a_shift, "b": b_val, "op": "abs_sum_solutions"}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(ans_sum)
            qt = "spr" if rng_obj.random() < 0.4 else "mcq"
            sb = spr_bounds(ans) if qt == "spr" else (None, None)
            distractors = make_distractors(ans, [str(ans_sum + 2), str(-ans_sum), str(b_val * 2)])
            return _abv(3, params, ph, ans, sb, None, distractors, qt)
        elif difficulty == 4:
            a_coef = rng_obj.randint(2, 4)
            b_shift = rng_obj.randint(-8, 8)
            c_val = rng_obj.randint(2, 12)
            # |a*x + b| = c → x = (c-b)/a or x = (-c-b)/a
            sol1 = (c_val - b_shift)
            sol2 = (-c_val - b_shift)
            if sol1 % a_coef != 0 or sol2 % a_coef != 0:
                continue
            x1 = sol1 // a_coef
            x2 = sol2 // a_coef
            larger = max(x1, x2)
            params = {"a": a_coef, "b": b_shift, "c": c_val, "op": "abs_linear"}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(larger)
            qt = "spr" if rng_obj.random() < 0.4 else "mcq"
            sb = spr_bounds(ans) if qt == "spr" else (None, None)
            distractors = make_distractors(ans, [str(min(x1, x2)), str(larger + 1), str(c_val // a_coef)])
            return _abv(4, params, ph, ans, sb, None, distractors, qt)
        elif difficulty == 5:
            a_center = rng_obj.randint(-5, 5)
            b_radius = rng_obj.randint(2, 8)
            # |x - a_center| < b_radius → width = 2*b_radius
            width = 2 * b_radius
            lo = a_center - b_radius
            hi = a_center + b_radius
            params = {"a": a_center, "b": b_radius, "op": "abs_ineq_width"}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(width)
            qt = "spr" if rng_obj.random() < 0.4 else "mcq"
            sb = spr_bounds(ans) if qt == "spr" else (None, None)
            diag = {"type": "number_line", "min": lo - 2, "max": hi + 2,
                    "boundary": [lo, hi], "direction": "between",
                    "endpoint": "open", "shaded_between": True}
            distractors = make_distractors(ans, [str(b_radius), str(width + 2), str(width - 2)])
            return _abv(5, params, ph, ans, sb, diag, distractors, qt)
        raise RuntimeError(f"Could not generate unique params for absolute_value d{difficulty}")
    raise RuntimeError(f"Could not generate unique params for absolute_value d{difficulty}")


def _abv(d, params, ph, ans, spr_val, diag, distractors, qt="mcq"):
    sb = spr_val if qt == "spr" else (None, None)
    return {"skill": "absolute_value", "difficulty": d, "questionType": qt,
            "params": params, "paramHash": ph, "verifiedAnswer": ans,
            "distractors": distractors if qt == "mcq" else [], "sprMin": sb[0], "sprMax": sb[1],
            "scenarioTag": None, "diagramSpec": diag, "questionContext": ""}
