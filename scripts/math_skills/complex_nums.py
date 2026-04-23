import math
import random
import sympy as sp
from sympy import symbols, solve, sqrt, Rational
from .core import (
    param_hash, fmt_num, fmt_fn, fmt_fx, fmt_lin_rhs,
    spr_bounds, make_distractors, pick_scenario, validate_math_object,
    PYTH_TRIPLES, LWP_SCENARIOS, PCT_SCENARIOS, RAT_SCENARIOS, PRP_SCENARIOS,
)

# ── Generator: complex_numbers ───────────────────────────────────────────────

PYTH_TRIPLES_CMX = [(3, 4, 5), (5, 12, 13), (8, 15, 17), (6, 8, 10), (9, 12, 15)]


def gen_complex_numbers(difficulty: int, rng_obj: random.Random, exclude_params: set, **_):
    for _ in range(200):
        if difficulty == 1:
            a, b, c, d = [rng_obj.randint(1, 9) for _ in range(4)]
            real_part = a + c
            params = {"a": a, "b": b, "c": c, "d": d, "op": "add_real"}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(real_part)
            distractors = make_distractors(ans, [str(a + c + 1), str(b + d), str(a - c)])
            return _cmx(1, params, ph, ans, (None, None), distractors, "mcq")
        elif difficulty == 2:
            a, b, c, d = [rng_obj.randint(1, 9) for _ in range(4)]
            imag_part = b - d
            params = {"a": a, "b": b, "c": c, "d": d, "op": "sub_imag"}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(imag_part)
            distractors = make_distractors(ans, [str(b + d), str(d - b), str(a - c)])
            return _cmx(2, params, ph, ans, (None, None), distractors, "mcq")
        elif difficulty == 3:
            a, b, c, d = [rng_obj.randint(1, 5) for _ in range(4)]
            real_part = a * c - b * d
            params = {"a": a, "b": b, "c": c, "d": d, "op": "mul_real"}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(real_part)
            distractors = make_distractors(ans, [str(a * c + b * d), str(a * d + b * c), str(a * c)])
            return _cmx(3, params, ph, ans, (None, None), distractors, "mcq")
        elif difficulty == 4:
            # Two template types to prevent structural repetition
            template = rng_obj.choice(["power_i", "power_i_expr"])
            if template == "power_i":
                # i^n — widen n range to 1..40 for more variety
                n = rng_obj.randint(1, 40)
                cycle = {0: "1", 1: "i", 2: "-1", 3: "-i"}
                ans = cycle[n % 4]
                params = {"n": n, "op": "power_i"}
                ph = param_hash(params)
                if ph in exclude_params:
                    continue
                all_vals = ["1", "i", "-1", "-i"]
                distractors = [v for v in all_vals if v != ans]
                ctx = f"Evaluate i^{n}. Recall that i^2 = -1."
                return _cmx(4, params, ph, ans, (None, None), distractors, "mcq", ctx)
            else:
                # (a + bi)^2 — real part of square of complex number
                a = rng_obj.randint(1, 6)
                b = rng_obj.randint(1, 6)
                real_part = a * a - b * b  # Re((a+bi)^2)
                params = {"a": a, "b": b, "op": "square_real"}
                ph = param_hash(params)
                if ph in exclude_params:
                    continue
                ans = str(real_part)
                distractors = make_distractors(ans, [
                    str(a * a + b * b), str(2 * a * b), str(a * a - b * b + 1)
                ])
                ctx = f"Compute the real part of ({a} + {b}i)^2."
                return _cmx(4, params, ph, ans, (None, None), distractors, "mcq", ctx)
        elif difficulty == 5:
            trip = rng_obj.choice(PYTH_TRIPLES_CMX)
            a, b, c = trip
            params = {"a": a, "b": b, "modulus": c, "op": "modulus"}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(c)
            return _cmx(5, params, ph, ans, spr_bounds(ans), [], "spr")
        raise RuntimeError(f"Could not generate unique params for complex_numbers d{difficulty}")
    raise RuntimeError(f"Could not generate unique params for complex_numbers d{difficulty}")


def _cmx(d, params, ph, ans, spr_val, distractors, qt="mcq", ctx=""):
    sb = spr_val if qt == "spr" else (None, None)
    return {"skill": "complex_numbers", "difficulty": d, "questionType": qt,
            "params": params, "paramHash": ph, "verifiedAnswer": ans,
            "distractors": distractors if qt == "mcq" else [], "sprMin": sb[0], "sprMax": sb[1],
            "scenarioTag": None, "diagramSpec": None, "questionContext": ctx}
