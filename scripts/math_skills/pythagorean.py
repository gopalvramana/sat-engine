import math
import random
import sympy as sp
from sympy import symbols, solve, sqrt, Rational
from .core import (
    param_hash, fmt_num, fmt_fn, fmt_fx, fmt_lin_rhs,
    spr_bounds, make_distractors, pick_scenario, validate_math_object,
    PYTH_TRIPLES, LWP_SCENARIOS, PCT_SCENARIOS, RAT_SCENARIOS, PRP_SCENARIOS,
)

# ── Generator: pythagorean_theorem ───────────────────────────────────────────

def gen_pythagorean_theorem(difficulty: int, rng_obj: random.Random, exclude_params: set) -> dict:
    for _ in range(100):
        if difficulty == 1:
            a, b, c = rng_obj.choice(PYTH_TRIPLES[:6])
            params = {"a": a, "b": b}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            assert a**2 + b**2 == c**2
            ans = str(c)
            diag = {"type": "right_triangle", "legs": [a, b],
                    "hypotenuse": "?", "missing": "hypotenuse"}
            return _pyt(1, params, ph, ans, None, diag,
                        make_distractors(ans, [str(a+b), str(c+1), str(c-1), str(a+b-1)]))

        elif difficulty == 2:
            a, b, c = rng_obj.choice(PYTH_TRIPLES[:8])
            params = {"leg": a, "hyp": c}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            assert a**2 + b**2 == c**2
            ans = str(b)
            diag = {"type": "right_triangle", "legs": [a, "?"],
                    "hypotenuse": c, "missing": "leg"}
            return _pyt(2, params, ph, ans, None, diag,
                        make_distractors(ans, [str(a), str(c-a), str(b+1), str(b-1)]))

        elif difficulty == 3:
            a, b, c = rng_obj.choice(PYTH_TRIPLES)
            k = rng_obj.randint(2, 4)
            a2, b2, c2 = a*k, b*k, c*k
            params = {"a": a2, "b": b2}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            assert a2**2 + b2**2 == c2**2
            ans = str(c2)
            qt = "spr" if rng_obj.random() < 0.4 else "mcq"
            sm, sx = spr_bounds(ans) if qt == "spr" else (None, None)
            diag = {"type": "right_triangle", "legs": [a2, b2],
                    "hypotenuse": "?", "missing": "hypotenuse"}
            dist = make_distractors(ans, [str(a2+b2), str(c2+k),
                                          str(c2-k), str(c)]) if qt == "mcq" else []
            return _pyt(3, params, ph, ans, (sm, sx), diag, make_distractors(ans, [
                str(a2+b2), str(c2+k), str(c2-k), str(c)]) if qt == "mcq" else [], qt)

        elif difficulty == 4:
            a, b, c = rng_obj.choice(PYTH_TRIPLES)
            k = rng_obj.randint(1, 3)
            a2, b2, c2 = a*k, b*k, c*k
            params = {"width": a2, "height": b2}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            assert a2**2 + b2**2 == c2**2
            ans = str(c2)
            qt = "spr" if rng_obj.random() < 0.4 else "mcq"
            sm, sx = spr_bounds(ans) if qt == "spr" else (None, None)
            diag = {"type": "right_triangle", "legs": [a2, b2],
                    "hypotenuse": "?", "missing": "hypotenuse"}
            dist = make_distractors(ans, [str(a2+b2), str(c2+1),
                                          str(c2-1), str(c)]) if qt == "mcq" else []
            return _pyt(4, params, ph, ans, (sm, sx), diag, dist, qt)

        elif difficulty == 5:
            a, b, c = rng_obj.choice(PYTH_TRIPLES[3:])
            k = rng_obj.randint(1, 3)
            a2, b2, c2 = a*k, b*k, c*k
            area = a2 * b2 // 2
            params = {"leg": a2, "hyp": c2, "ask": "area"}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            assert a2**2 + b2**2 == c2**2
            ans = str(area)
            diag = {"type": "right_triangle", "legs": [a2, "?"],
                    "hypotenuse": c2, "missing": "leg"}
            return _pyt(5, params, ph, ans, None, diag,
                        make_distractors(ans, [str(a2*b2), str(area+a2),
                                               str(b2*c2//2), str(area-a2)]))

        else:
            raise NotImplementedError(f"pythagorean_theorem d{difficulty} not implemented")

    raise RuntimeError(f"Could not generate unique params for pythagorean_theorem d{difficulty}")


def _pyt(d, params, ph, ans, spr, diag, distractors, qt="mcq", ctx=""):
    sm, sx = spr if spr else (None, None)
    missing = diag.get("missing", "side") if diag else "side"
    return {"skill": "pythagorean_theorem", "difficulty": d, "questionType": qt,
            "params": params, "paramHash": ph, "verifiedAnswer": ans,
            "distractors": distractors, "sprMin": sm, "sprMax": sx,
            "scenarioTag": None, "diagramSpec": diag,
            "questionContext": ctx or f"Use the Pythagorean theorem to find the missing {missing}. The answer is {ans}."}
