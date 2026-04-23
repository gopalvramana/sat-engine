import math
import random
import sympy as sp
from sympy import symbols, solve, sqrt, Rational
from .core import (
    param_hash, fmt_num, fmt_fn, fmt_fx, fmt_lin_rhs,
    spr_bounds, make_distractors, pick_scenario, validate_math_object,
    PYTH_TRIPLES, LWP_SCENARIOS, PCT_SCENARIOS, RAT_SCENARIOS, PRP_SCENARIOS,
)

# ── Generator: sequences_series ──────────────────────────────────────────────

def gen_sequences_series(difficulty: int, rng_obj: random.Random, exclude_params: set, **_):
    for _ in range(200):
        if difficulty == 1:
            a1 = rng_obj.randint(2, 10)
            d = rng_obj.randint(1, 5)
            n = rng_obj.randint(4, 8)
            an = a1 + (n - 1) * d
            params = {"a1": a1, "d_step": d, "n": n, "seq_type": "arith_nth"}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(an)
            qt = "spr" if rng_obj.random() < 0.3 else "mcq"
            sb = spr_bounds(ans) if qt == "spr" else (None, None)
            distractors = make_distractors(ans, [str(an - d), str(an + d), str(a1 + n * d)])
            return _seq(1, params, ph, ans, sb, distractors, qt)
        elif difficulty == 2:
            d_step = rng_obj.randint(1, 5)
            n = rng_obj.randint(4, 8)
            a1 = rng_obj.randint(2, 10)
            an = a1 + (n - 1) * d_step
            params = {"an": an, "d_step": d_step, "n": n, "seq_type": "arith_a1"}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(a1)
            distractors = make_distractors(ans, [str(a1 - 1), str(a1 + d_step), str(an - n * d_step)])
            return _seq(2, params, ph, ans, (None, None), distractors, "mcq")
        elif difficulty == 3:
            a1 = rng_obj.randint(2, 5)
            r = rng_obj.randint(2, 3)
            n = rng_obj.randint(3, 5)
            an = a1 * (r ** (n - 1))
            params = {"a1": a1, "r": r, "n": n, "seq_type": "geo_nth"}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(an)
            qt = "spr" if rng_obj.random() < 0.3 else "mcq"
            sb = spr_bounds(ans) if qt == "spr" else (None, None)
            distractors = make_distractors(ans, [str(a1 * r ** (n - 2)), str(an * r), str(a1 * n * r)])
            return _seq(3, params, ph, ans, sb, distractors, qt)
        elif difficulty == 4:
            a1 = rng_obj.randint(2, 8)
            d_step = rng_obj.randint(1, 5)
            n = rng_obj.randint(4, 10)
            sn = n * (2 * a1 + (n - 1) * d_step) // 2
            if n * (2 * a1 + (n - 1) * d_step) % 2 != 0:
                continue
            params = {"a1": a1, "d_step": d_step, "n": n, "seq_type": "arith_sum"}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(sn)
            qt = "spr" if rng_obj.random() < 0.4 else "mcq"
            sb = spr_bounds(ans) if qt == "spr" else (None, None)
            distractors = make_distractors(ans, [str(sn - a1), str(sn + d_step * n), str(n * a1)])
            return _seq(4, params, ph, ans, sb, distractors, qt)
        elif difficulty == 5:
            a1 = rng_obj.randint(2, 5)
            r = rng_obj.randint(2, 3)
            n = rng_obj.randint(3, 5)
            sn = a1 * (r ** n - 1) // (r - 1)
            if a1 * (r ** n - 1) % (r - 1) != 0:
                continue
            params = {"a1": a1, "r": r, "n": n, "seq_type": "geo_sum"}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(sn)
            distractors = make_distractors(ans, [str(sn - a1), str(sn + a1 * r ** (n - 1)), str(a1 * r ** n)])
            return _seq(5, params, ph, ans, (None, None), distractors, "mcq")
        raise RuntimeError(f"Could not generate unique params for sequences_series d{difficulty}")
    raise RuntimeError(f"Could not generate unique params for sequences_series d{difficulty}")


def _seq(d, params, ph, ans, spr_val, distractors, qt="mcq"):
    sb = spr_val if qt == "spr" else (None, None)
    return {"skill": "sequences_series", "difficulty": d, "questionType": qt,
            "params": params, "paramHash": ph, "verifiedAnswer": ans,
            "distractors": distractors if qt == "mcq" else [], "sprMin": sb[0], "sprMax": sb[1],
            "scenarioTag": None, "diagramSpec": None, "questionContext": ""}
