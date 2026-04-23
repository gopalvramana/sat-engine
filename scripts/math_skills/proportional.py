import math
import random
import sympy as sp
from sympy import symbols, solve, sqrt, Rational
from .core import (
    param_hash, fmt_num, fmt_fn, fmt_fx, fmt_lin_rhs,
    spr_bounds, make_distractors, pick_scenario, validate_math_object,
    PYTH_TRIPLES, LWP_SCENARIOS, PCT_SCENARIOS, RAT_SCENARIOS, PRP_SCENARIOS,
)

# ── Generator: proportional_relationships ────────────────────────────────────

def gen_proportional_relationships(difficulty: int, rng_obj: random.Random,
                                    exclude_params: set, exclude_scenarios: set) -> dict:
    scenario = pick_scenario(PRP_SCENARIOS, exclude_scenarios, rng_obj)
    for _ in range(100):
        if difficulty == 1:
            k = rng_obj.randint(2, 10)
            xv = rng_obj.randint(2, 8)
            answer = k * xv
            params = {"k": k, "x_val": xv, "scenario": scenario}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(answer)
            return _prp(1, params, ph, ans, scenario,
                        make_distractors(ans, [str(k+xv), str(answer+k),
                                               str(answer-k), str(k)]))

        elif difficulty == 2:
            x1 = rng_obj.randint(2, 8)
            k = rng_obj.randint(3, 12)
            y1 = k * x1
            x2 = rng_obj.randint(2, 10)
            while x2 == x1:
                x2 = rng_obj.randint(2, 10)
            answer = k * x2
            params = {"x1": x1, "y1": y1, "x2": x2, "scenario": scenario}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(answer)
            return _prp(2, params, ph, ans, scenario,
                        make_distractors(ans, [str(y1+x2), str(x2*x1),
                                               str(answer+k), str(y1*x2//x1+1)]))

        elif difficulty == 3:
            num = rng_obj.randint(1, 5)
            den = rng_obj.randint(2, 6)
            g = math.gcd(num, den)
            num //= g
            den //= g
            xv = den * rng_obj.randint(2, 8)
            answer = num * xv // den
            if num * xv % den != 0:
                continue
            params = {"k_num": num, "k_den": den, "x_val": xv, "scenario": scenario}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(answer)
            return _prp(3, params, ph, ans, scenario,
                        make_distractors(ans, [str(answer+num), str(xv//den),
                                               str(num*xv), str(answer-num)]))

        elif difficulty == 4:
            k = rng_obj.randint(4, 15)
            xv = rng_obj.randint(3, 12)
            yv = k * xv
            params = {"k": k, "y_val": yv, "scenario": scenario}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(xv)
            return _prp(4, params, ph, ans, scenario,
                        make_distractors(ans, [str(k), str(yv//(k+1)),
                                               str(xv+1), str(xv-1)]))

        elif difficulty == 5:
            k = rng_obj.randint(3, 12)
            xs = [rng_obj.randint(1, 5) * i for i in range(1, 5)]
            ys = [k * xi for xi in xs]
            missing_idx = rng_obj.randint(0, 3)
            answer = ys[missing_idx]
            ys_with_missing = ys[:]
            ys_with_missing[missing_idx] = -1
            params = {"k": k, "xs": xs, "ys_with_missing": ys_with_missing,
                      "missing_idx": missing_idx, "scenario": scenario}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(answer)
            return _prp(5, params, ph, ans, scenario,
                        make_distractors(ans, [str(answer+k), str(xs[missing_idx]+k),
                                               str(answer-k), str(answer*2//3)]))

        else:
            raise NotImplementedError(f"proportional_relationships d{difficulty} not implemented")

    raise RuntimeError(f"Could not generate unique params for proportional_relationships d{difficulty}")


def _prp(d, params, ph, ans, scenario, distractors, ctx=""):
    return {"skill": "proportional_relationships", "difficulty": d, "questionType": "mcq",
            "params": params, "paramHash": ph, "verifiedAnswer": ans,
            "distractors": distractors, "sprMin": None, "sprMax": None,
            "scenarioTag": scenario, "diagramSpec": None,
            "questionContext": ctx or f"Solve the proportional relationship problem. The answer is {ans}."}
