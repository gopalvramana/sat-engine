import math
import random
import sympy as sp
from sympy import symbols, solve, sqrt, Rational
from .core import (
    param_hash, fmt_num, fmt_fn, fmt_fx, fmt_lin_rhs,
    spr_bounds, make_distractors, pick_scenario, validate_math_object,
    PYTH_TRIPLES, LWP_SCENARIOS, PCT_SCENARIOS, RAT_SCENARIOS, PRP_SCENARIOS,
)

# ── Generator: percentages ────────────────────────────────────────────────────

def gen_percentages(difficulty: int, rng_obj: random.Random,
                    exclude_params: set, exclude_scenarios: set) -> dict:
    scenario = pick_scenario(PCT_SCENARIOS, exclude_scenarios, rng_obj)
    for _ in range(100):
        if difficulty == 1:
            p = rng_obj.choice([10, 20, 25, 50, 75])
            divisor = 100 // math.gcd(p, 100)
            k = rng_obj.randint(1, 10)
            n = divisor * k
            answer = n * p // 100
            if answer == 0:
                continue
            params = {"percent": p, "value": n, "scenario": scenario}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            assert n * p % 100 == 0
            ans = str(answer)
            return _pct(1, params, ph, ans, scenario,
                        make_distractors(ans, [str(answer+p//10+1), str(n-answer),
                                               str(n//p if n % p == 0 else n*p//100+1),
                                               str(answer*2)]))

        elif difficulty == 2:
            p = rng_obj.choice([10, 20, 25, 40, 50])
            # Ensure n * p is exactly divisible by 100 for a clean percent
            divisor = 100 // math.gcd(p, 100)
            k = rng_obj.randint(2, 12)
            n = divisor * k
            part = n * p // 100
            params = {"part": part, "whole": n, "scenario": scenario}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            assert part * 100 // n == p
            ans = str(p)
            return _pct(2, params, ph, ans, scenario,
                        make_distractors(ans, [str(p+10), str(p-10),
                                               str(100-p), str(part)]))

        elif difficulty == 3:
            A = rng_obj.randint(20, 100)
            pct = rng_obj.choice([10, 15, 20, 25, 30, 50])
            direction = rng_obj.choice([1, -1])
            B = A + direction * A * pct // 100
            params = {"original": A, "new_value": B, "scenario": scenario}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            if round(abs(B - A) * 100 / A) != pct:
                continue
            ans = str(pct)
            return _pct(3, params, ph, ans, scenario,
                        make_distractors(ans, [str(pct+5), str(pct-5),
                                               str(100-pct), str(abs(B-A))]))

        elif difficulty == 4:
            p = rng_obj.choice([10, 20, 25, 50])
            answer = rng_obj.randint(20, 100)
            V = answer * (100 + p) // 100
            if V * 100 // (100 + p) != answer:
                continue
            params = {"final_value": V, "percent_increase": p, "scenario": scenario}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(answer)
            return _pct(4, params, ph, ans, scenario,
                        make_distractors(ans, [str(V), str(V-answer),
                                               str(answer+p), str(answer-p)]))

        elif difficulty == 5:
            A = rng_obj.randint(100, 500)
            p1 = rng_obj.choice([10, 20, 25])
            p2 = rng_obj.choice([10, 20, 25])
            after = round(A * (100 + p1) / 100 * (100 - p2) / 100)
            params = {"original": A, "p1": p1, "p2": p2, "scenario": scenario}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(after)
            wrong1 = round(A * (100 + p1 - p2) / 100)
            wrong2 = round(A * (100 + p1) / 100)
            return _pct(5, params, ph, ans, scenario,
                        make_distractors(ans, [str(wrong1), str(wrong2),
                                               str(after+10), str(after-10)]))

        else:
            raise NotImplementedError(f"percentages d{difficulty} not implemented")

    raise RuntimeError(f"Could not generate unique params for percentages d{difficulty}")


def _pct(d, params, ph, ans, scenario, distractors, ctx=""):
    return {"skill": "percentages", "difficulty": d, "questionType": "mcq",
            "params": params, "paramHash": ph, "verifiedAnswer": ans,
            "distractors": distractors, "sprMin": None, "sprMax": None,
            "scenarioTag": scenario, "diagramSpec": None,
            "questionContext": ctx or f"Solve the percentage problem. The answer is {ans}."}
