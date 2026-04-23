import math
import random
import sympy as sp
from sympy import symbols, solve, sqrt, Rational
from .core import (
    param_hash, fmt_num, fmt_fn, fmt_fx, fmt_lin_rhs,
    spr_bounds, make_distractors, pick_scenario, validate_math_object,
    PYTH_TRIPLES, LWP_SCENARIOS, PCT_SCENARIOS, RAT_SCENARIOS, PRP_SCENARIOS,
)

# ── Generator: exponents_radicals ────────────────────────────────────────────

def gen_exponents_radicals(difficulty: int, rng_obj: random.Random, exclude_params: set, **_):
    for _ in range(200):
        if difficulty == 1:
            a = rng_obj.randint(2, 8)
            b = rng_obj.randint(2, 8)
            ans_val = a + b
            params = {"a": a, "b": b, "op": "product_same_base"}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(ans_val)
            return _exr(1, params, ph, ans, spr_bounds(ans), [], "spr")
        elif difficulty == 2:
            a = rng_obj.randint(2, 5)
            b = rng_obj.randint(2, 5)
            ans_val = a * b
            params = {"a": a, "b": b, "op": "power_of_power"}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(ans_val)
            return _exr(2, params, ph, ans, spr_bounds(ans), [], "spr")
        elif difficulty == 3:
            n_int = rng_obj.randint(2, 6)
            m = rng_obj.choice([2, 3, 5, 6, 7])
            n_full = n_int * n_int * m  # sqrt(n_full) = n_int*sqrt(m)
            params = {"radicand": n_full, "outer": n_int, "inner": m, "op": "simplify_sqrt"}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = f"{n_int}\u221a{m}"  # e.g. "3√5"
            distractors = [f"{n_int * n_int}\u221a{m}", f"{n_int}\u221a{m * m}", f"\u221a{n_full}"]
            return _exr(3, params, ph, ans, (None, None), distractors, "mcq")
        elif difficulty == 4:
            # Rational exponents: base^(p/q) = result (integer)
            # base = k^q so result = k^p
            cases = [
                (4,   3, 2,   8),    # 4^(3/2) = 8
                (8,   2, 3,   4),    # 8^(2/3) = 4
                (9,   3, 2,  27),    # 9^(3/2) = 27
                (16,  3, 4,   8),    # 16^(3/4) = 8
                (27,  2, 3,   9),    # 27^(2/3) = 9
                (32,  3, 5,   8),    # 32^(3/5) = 8
                (64,  2, 3,  16),    # 64^(2/3) = 16
                (25,  3, 2, 125),    # 25^(3/2) = 125
                (4,   5, 2,  32),    # 4^(5/2) = 32
                (8,   4, 3,  16),    # 8^(4/3) = 16
                (16,  1, 2,   4),    # 16^(1/2) = 4
                (27,  1, 3,   3),    # 27^(1/3) = 3
                (64,  1, 3,   4),    # 64^(1/3) = 4
                (125, 1, 3,   5),    # 125^(1/3) = 5
                (81,  3, 4,  27),    # 81^(3/4) = 27
                (32,  2, 5,   4),    # 32^(2/5) = 4
                (16,  5, 4,  32),    # 16^(5/4) = 32
                (243, 2, 5,   9),    # 243^(2/5) = 9
                (100, 3, 2, 1000),   # 100^(3/2) = 1000
                (9,   5, 2, 243),    # 9^(5/2) = 243
                (4,   7, 2, 128),    # 4^(7/2) = 128
                (8,   5, 3,  32),    # 8^(5/3) = 32
                (27,  4, 3,  81),    # 27^(4/3) = 81
                (16,  7, 4, 128),    # 16^(7/4) = 128
                (32,  4, 5,  16),    # 32^(4/5) = 16
            ]
            rng_obj.shuffle(cases)
            for base, p, q, result in cases:
                params = {"base": base, "p": p, "q": q, "result": result, "op": "rational_exp"}
                ph = param_hash(params)
                if ph in exclude_params:
                    continue
                ans = str(result)
                # Distractors: wrong application of rational exponent rule
                d1_wrong = str(base * p // q) if base * p % q == 0 else str(base + p)  # multiply instead of exponentiate
                d2_wrong = str(result + q)    # off-by-one type error
                d3_wrong = str(base ** p)     # ignores the root (applies p directly to base)
                distractors = list({d1_wrong, d2_wrong, d3_wrong} - {ans})[:3]
                while len(distractors) < 3:
                    distractors.append(str(result + len(distractors) + 1))
                return _exr(4, params, ph, ans, (None, None), distractors, "mcq",
                            ctx=f"Evaluate {base}^({p}/{q}). The answer is a whole number.")
        elif difficulty == 5:
            # Exponential equation: a^(b*x + c) = a^k, solve for integer x
            a = rng_obj.choice([2, 3, 5])
            x_ans = rng_obj.randint(1, 5)
            b = rng_obj.choice([1, 2, 3])
            c = rng_obj.choice([-2, -1, 1, 2])
            k_exp = b * x_ans + c
            if k_exp < 1 or k_exp > 8:
                continue
            rhs = a ** k_exp
            params = {"base": a, "b": b, "c": c, "rhs": rhs, "op": "exp_equation"}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(x_ans)
            # Distractors: sign error on c, wrong isolation step
            d1_wrong = str(x_ans + 1)
            d2_wrong = str((k_exp + c) // b) if b != 0 else str(x_ans + 2)  # forget to subtract c
            d3_wrong = str(x_ans - 1) if x_ans > 1 else str(x_ans + 2)
            distractors = list({d1_wrong, d2_wrong, d3_wrong} - {ans})[:3]
            while len(distractors) < 3:
                distractors.append(str(x_ans + len(distractors) + 1))
            b_str = "" if b == 1 else str(b)
            c_str = f"+{c}" if c > 0 else str(c)
            return _exr(5, params, ph, ans, (None, None), distractors, "mcq",
                        ctx=f"Solve for x: {a}^({b_str}x{c_str}) = {rhs}. The answer is x = {x_ans}.")
        raise RuntimeError(f"Could not generate unique params for exponents_radicals d{difficulty}")
    raise RuntimeError(f"Could not generate unique params for exponents_radicals d{difficulty}")


def _exr(d, params, ph, ans, spr_val, distractors, qt="mcq", ctx=""):
    sb = spr_val if qt == "spr" else (None, None)
    return {"skill": "exponents_radicals", "difficulty": d, "questionType": qt,
            "params": params, "paramHash": ph, "verifiedAnswer": ans,
            "distractors": distractors if qt == "mcq" else [], "sprMin": sb[0], "sprMax": sb[1],
            "scenarioTag": None, "diagramSpec": None, "questionContext": ctx}
