import math
import random
import sympy as sp
from sympy import symbols, solve, sqrt, Rational
from .core import (
    param_hash, fmt_num, fmt_fn, fmt_fx, fmt_lin_rhs,
    spr_bounds, make_distractors, pick_scenario, validate_math_object,
    PYTH_TRIPLES, LWP_SCENARIOS, PCT_SCENARIOS, RAT_SCENARIOS, PRP_SCENARIOS,
)

# ── Generator: quadratic_equations ───────────────────────────────────────────

def gen_quadratic_equations(difficulty: int, rng_obj: random.Random, exclude_params: set) -> dict:
    x = symbols("x")
    for _ in range(100):
        if difficulty == 1:
            r = rng_obj.randint(1, 6)
            params = {"r": r, "form": "perfect_square"}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            sol = solve((x - r) ** 2, x)
            assert sol and sol[0] == r
            ans = str(r)
            return _qeq(1, params, ph, ans, None,
                        make_distractors(ans, [str(r+1), str(-r), str(r-1), str(2*r)]))

        elif difficulty == 2:
            r1 = rng_obj.randint(1, 6)
            r2 = rng_obj.randint(1, 6)
            while r2 == r1:
                r2 = rng_obj.randint(1, 6)
            b_c, c_c = -(r1+r2), r1*r2
            params = {"b": b_c, "c": c_c}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            sol = [int(s) for s in solve(x**2 + b_c*x + c_c, x)]
            assert sorted(sol) == sorted([r1, r2])
            ans = str(max(r1, r2))
            return _qeq(2, params, ph, ans, None,
                        make_distractors(ans, [str(min(r1,r2)), str(b_c),
                                               str(c_c), str(max(r1,r2)+1)]))

        elif difficulty == 3:
            r1 = rng_obj.randint(1, 8)
            r2 = rng_obj.randint(-8, -1)
            b_c, c_c = -(r1+r2), r1*r2
            params = {"b": b_c, "c": c_c}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            sol = [int(s) for s in solve(x**2 + b_c*x + c_c, x)]
            assert sorted(sol) == sorted([r1, r2])
            ans = str(r1)
            return _qeq(3, params, ph, ans, None,
                        make_distractors(ans, [str(r2), str(-r1),
                                               str(r1+r2), str(r1*r2)]))

        elif difficulty == 4:
            a = rng_obj.randint(2, 4)
            r1 = rng_obj.randint(-6, 6) or 3
            r2 = rng_obj.randint(-6, 6) or -2
            b_c, c_c = -a*(r1+r2), a*r1*r2
            params = {"a": a, "b": b_c, "c": c_c}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            sol = [int(s) for s in solve(a*x**2 + b_c*x + c_c, x)]
            assert sorted(sol) == sorted([r1, r2])
            larger = max(r1, r2)
            ans = str(larger)
            qt = "spr" if rng_obj.random() < 0.4 else "mcq"
            sm, sx = spr_bounds(ans) if qt == "spr" else (None, None)
            dist = make_distractors(ans, [str(min(r1,r2)), str(r1+r2),
                                          str(-(r1+r2)), str(larger+1)]) \
                   if qt == "mcq" else []
            return _qeq(4, params, ph, ans, (sm, sx), dist, qt)

        elif difficulty == 5:
            r1 = rng_obj.randint(-8, 8) or 4
            r2 = rng_obj.randint(-8, 8) or -5
            b_c, c_c = -(r1+r2), r1*r2
            params = {"b": b_c, "c": c_c, "question_type": "product_of_roots"}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(c_c)
            return _qeq(5, params, ph, ans, None,
                        make_distractors(ans, [str(r1+r2), str(-c_c),
                                               str(c_c+1), str(b_c)]))

        else:
            raise NotImplementedError(f"quadratic_equations d{difficulty} not implemented")

    raise RuntimeError(f"Could not generate unique params for quadratic_equations d{difficulty}")


def _qeq(d, params, ph, ans, spr, distractors, qt="mcq", ctx=""):
    sm, sx = spr if spr else (None, None)
    return {"skill": "quadratic_equations", "difficulty": d, "questionType": qt,
            "params": params, "paramHash": ph, "verifiedAnswer": ans,
            "distractors": distractors, "sprMin": sm, "sprMax": sx,
            "scenarioTag": None, "diagramSpec": None,
            "questionContext": ctx or f"Solve the quadratic equation. The answer is {ans}."}
