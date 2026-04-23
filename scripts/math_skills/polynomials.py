import math
import random
import sympy as sp
from sympy import symbols, solve, sqrt, Rational
from .core import (
    param_hash, fmt_num, fmt_fn, fmt_fx, fmt_lin_rhs,
    spr_bounds, make_distractors, pick_scenario, validate_math_object,
    PYTH_TRIPLES, LWP_SCENARIOS, PCT_SCENARIOS, RAT_SCENARIOS, PRP_SCENARIOS,
)

# ── Generator: polynomials ───────────────────────────────────────────────────

PRB_SCENARIOS = ["card_deck", "marble_bag", "coin_flip", "dice_roll",
                 "spinner", "survey_data", "class_selection", "colored_tiles"]


def gen_polynomials(difficulty: int, rng_obj: random.Random, exclude_params: set, **_):
    for _ in range(200):
        if difficulty == 1:
            a = rng_obj.randint(1, 9)
            b = rng_obj.randint(1, 9)
            ans_val = a * b
            params = {"a": a, "b": b, "op": "foil_constant"}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(ans_val)
            distractors = make_distractors(ans, [str(a + b), str(a * b + 1), str(a * b - 1)])
            return _pol(1, params, ph, ans, (None, None), distractors, "mcq")
        elif difficulty == 2:
            a = rng_obj.randint(1, 9)
            b = rng_obj.randint(1, 9)
            ans_val = a + b
            params = {"a": a, "b": b, "op": "foil_linear_coeff"}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(ans_val)
            distractors = make_distractors(ans, [str(a * b), str(a - b), str(a + b + 1)])
            return _pol(2, params, ph, ans, (None, None), distractors, "mcq")
        elif difficulty == 3:
            r1 = rng_obj.randint(1, 7)
            r2 = rng_obj.randint(1, 7)
            b_coef = r1 + r2
            c_coef = r1 * r2
            # x^2 + b*x + c = (x+r1)(x+r2), give one root = -r1
            params = {"b": b_coef, "c": c_coef, "root1": -r1, "root2": -r2, "op": "factor_root"}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(-r1)
            distractors = make_distractors(ans, [str(r1), str(-r2), str(b_coef)])
            return _pol(3, params, ph, ans, (None, None), distractors, "mcq")
        elif difficulty == 4:
            b = rng_obj.randint(-5, 5)
            c = rng_obj.randint(-10, 10)
            v = rng_obj.randint(-3, 4)
            result = v * v + b * v + c
            params = {"b": b, "c": c, "v": v, "op": "evaluate"}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(result)
            qt = "spr" if rng_obj.random() < 0.4 else "mcq"
            sb = spr_bounds(ans) if qt == "spr" else (None, None)
            distractors = make_distractors(ans, [str(result + 1), str(result - 2), str(result * 2)])
            return _pol(4, params, ph, ans, sb, distractors, qt)
        elif difficulty == 5:
            r = rng_obj.randint(1, 5)
            q_const = rng_obj.randint(-5, 5)
            # (x+r)(x+q_const) = x^2 + (r+q_const)x + r*q_const
            b_coef = r + q_const
            c_coef = r * q_const
            # (x^2 + b*x + c) / (x + r) = (x + q_const), remainder 0
            params = {"b": b_coef, "c": c_coef, "divisor_root": r, "quotient_const": q_const, "op": "poly_div"}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(q_const)
            qt = "spr" if rng_obj.random() < 0.4 else "mcq"
            sb = spr_bounds(ans) if qt == "spr" else (None, None)
            distractors = make_distractors(ans, [str(q_const + 1), str(q_const - 1), str(r)])
            return _pol(5, params, ph, ans, sb, distractors, qt)
        raise RuntimeError(f"Could not generate unique params for polynomials d{difficulty}")
    raise RuntimeError(f"Could not generate unique params for polynomials d{difficulty}")


def _pol(d, params, ph, ans, spr_val, distractors, qt="mcq"):
    sb = spr_val if qt == "spr" else (None, None)
    return {"skill": "polynomials", "difficulty": d, "questionType": qt,
            "params": params, "paramHash": ph, "verifiedAnswer": ans,
            "distractors": distractors if qt == "mcq" else [], "sprMin": sb[0], "sprMax": sb[1],
            "scenarioTag": None, "diagramSpec": None, "questionContext": ""}
