import math
import random
import sympy as sp
from sympy import symbols, solve, sqrt, Rational
from .core import (
    param_hash, fmt_num, fmt_fn, fmt_fx, fmt_lin_rhs,
    spr_bounds, make_distractors, pick_scenario, validate_math_object,
    PYTH_TRIPLES, LWP_SCENARIOS, PCT_SCENARIOS, RAT_SCENARIOS, PRP_SCENARIOS,
)

# ── Generator: special_triangles ─────────────────────────────────────────────

def gen_special_triangles(difficulty: int, rng_obj: random.Random, exclude_params: set, **_):
    import fractions as _frac
    for _ in range(200):
        if difficulty == 1:
            k = rng_obj.randint(2, 8)
            hyp = 2 * k
            short = k
            long_leg = f"{k}\u221a3"
            params = {"k": k, "variant": "30_60_90", "given": "hyp", "d": 1}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(short)
            diag = {"type": "special_triangle", "variant": "30_60_90",
                    "sides": ["?", long_leg, hyp], "angles": [30, 60, 90], "missing": 0}
            distractors = make_distractors(ans, [str(k * 2), str(k + 1), str(k - 1)])
            return _spt(1, params, ph, ans, (None, None), diag, distractors, "mcq")
        elif difficulty == 2:
            k = rng_obj.randint(2, 6)
            short = k
            long_leg = f"{k}\u221a3"
            hyp = 2 * k
            params = {"k": k, "variant": "30_60_90", "given": "short_leg", "d": 2}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = long_leg
            diag = {"type": "special_triangle", "variant": "30_60_90",
                    "sides": [short, "?", hyp], "angles": [30, 60, 90], "missing": 1}
            d2 = [f"{k * 2}\u221a3", f"{k}\u221a2", f"{k + 1}\u221a3"]
            return _spt(2, params, ph, ans, (None, None), diag, d2, "mcq")
        elif difficulty == 3:
            a = rng_obj.randint(2, 8)
            hyp = f"{a}\u221a2"
            params = {"a": a, "variant": "45_45_90", "given": "leg", "d": 3}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = hyp
            diag = {"type": "special_triangle", "variant": "45_45_90",
                    "sides": [a, a, "?"], "angles": [45, 45, 90], "missing": 2}
            d2 = [f"{a * 2}", f"{a}\u221a3", f"{a + 1}\u221a2"]
            return _spt(3, params, ph, ans, (None, None), diag, d2, "mcq")
        elif difficulty == 4:
            k = rng_obj.randint(2, 5)
            long_leg = f"{k}\u221a3"
            short = k
            hyp = 2 * k
            params = {"k": k, "variant": "30_60_90", "given": "long_leg", "d": 4}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(hyp)
            diag = {"type": "special_triangle", "variant": "30_60_90",
                    "sides": [short, long_leg, "?"], "angles": [30, 60, 90], "missing": 2}
            qt = "spr" if rng_obj.random() < 0.4 else "mcq"
            sb = spr_bounds(ans) if qt == "spr" else (None, None)
            distractors = make_distractors(ans, [str(k), str(hyp + 2), str(hyp - 2)])
            return _spt(4, params, ph, ans, sb, diag, distractors, qt)
        elif difficulty == 5:
            a = rng_obj.randint(2, 6)
            hyp_str = f"{a}\u221a2"
            # Area = (1/2)*a*a = a^2/2
            area = _frac.Fraction(a * a, 2)
            params = {"a": a, "variant": "45_45_90", "given": "hyp", "d": 5}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(area)  # e.g. "9/2" or "8"
            diag = {"type": "special_triangle", "variant": "45_45_90",
                    "sides": ["?", "?", hyp_str], "angles": [45, 45, 90], "missing": 0}
            sb = spr_bounds(ans)
            return _spt(5, params, ph, ans, sb, diag, [], "spr")
        raise RuntimeError(f"Could not generate unique params for special_triangles d{difficulty}")
    raise RuntimeError(f"Could not generate unique params for special_triangles d{difficulty}")


def _spt(d, params, ph, ans, spr_val, diag, distractors, qt="mcq"):
    sb = spr_val if qt == "spr" else (None, None)
    return {"skill": "special_triangles", "difficulty": d, "questionType": qt,
            "params": params, "paramHash": ph, "verifiedAnswer": ans,
            "distractors": distractors if qt == "mcq" else [], "sprMin": sb[0], "sprMax": sb[1],
            "scenarioTag": None, "diagramSpec": diag, "questionContext": ""}
