import math
import random
import sympy as sp
from sympy import symbols, solve, sqrt, Rational
from .core import (
    param_hash, fmt_num, fmt_fn, fmt_fx, fmt_lin_rhs,
    spr_bounds, make_distractors, pick_scenario, validate_math_object,
    PYTH_TRIPLES, LWP_SCENARIOS, PCT_SCENARIOS, RAT_SCENARIOS, PRP_SCENARIOS,
)

# ── Generator: linear_eq_word_problems ───────────────────────────────────────

def gen_linear_eq_word_problems(difficulty: int, rng_obj: random.Random,
                                 exclude_params: set, exclude_scenarios: set) -> dict:
    scenario = pick_scenario(LWP_SCENARIOS, exclude_scenarios, rng_obj)
    x = symbols("x")
    for _ in range(100):
        if difficulty == 1:
            rate = rng_obj.randint(1, 5)
            fixed = rng_obj.randint(1, 10)
            answer = rng_obj.randint(1, 5)
            total = rate * answer + fixed
            params = {"rate": rate, "fixed": fixed, "total": total, "scenario": scenario}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            sol = solve(rate * x + fixed - total, x)
            assert sol and sol[0] == answer
            ans = str(answer)
            return _lwp(1, params, ph, ans, scenario,
                        make_distractors(ans, [str(answer+1), str(answer-1),
                                               str(total//rate), str(total-fixed)]))

        elif difficulty == 2:
            rate = rng_obj.randint(2, 8)
            fixed = rng_obj.randint(5, 20)
            answer = rng_obj.randint(2, 9)
            total = rate * answer + fixed
            params = {"rate": rate, "fixed": fixed, "total": total, "scenario": scenario}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            sol = solve(rate * x + fixed - total, x)
            assert sol and sol[0] == answer
            ans = str(answer)
            return _lwp(2, params, ph, ans, scenario,
                        make_distractors(ans, [str(answer+1), str(answer-1),
                                               str(total//rate), fmt_num(Rational(total, rate))]))

        elif difficulty == 3:
            diff = rng_obj.randint(2, 10)
            total = rng_obj.randint(10, 30)
            if (total + diff) % 2 != 0:
                total += 1
            smaller = (total - diff) // 2
            larger = total - smaller
            params = {"total": total, "difference": diff, "scenario": scenario}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            sol = solve(x + (x + diff) - total, x)
            assert sol and sol[0] == smaller
            ans = str(larger)
            return _lwp(3, params, ph, ans, scenario,
                        make_distractors(ans, [str(smaller), str(larger+1),
                                               str(total//2), str(larger-1)]))

        elif difficulty == 4:
            rate1 = rng_obj.randint(2, 8)
            rate2 = rng_obj.randint(2, 8)
            while rate1 == rate2:
                rate2 = rng_obj.randint(2, 8)
            total_items = rng_obj.randint(10, 25)
            answer = rng_obj.randint(3, total_items - 3)
            total_cost = rate1 * answer + rate2 * (total_items - answer)
            params = {"rate1": rate1, "rate2": rate2, "total_items": total_items,
                      "total_cost": total_cost, "scenario": scenario}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            sol = solve(rate1 * x + rate2 * (total_items - x) - total_cost, x)
            assert sol and sol[0] == answer
            ans = str(answer)
            return _lwp(4, params, ph, ans, scenario,
                        make_distractors(ans, [str(total_items - answer),
                                               str(answer+2), str(answer-2),
                                               str(total_cost // rate1)]))

        elif difficulty == 5:
            speed1 = rng_obj.randint(30, 70)
            speed2 = rng_obj.randint(30, 70)
            while speed1 == speed2:
                speed2 = rng_obj.randint(30, 70)
            t = rng_obj.randint(1, 4)
            total_dist = (speed1 + speed2) * t
            params = {"speed1": speed1, "speed2": speed2,
                      "total_dist": total_dist, "scenario": scenario}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            sol = solve(speed1 * x + speed2 * x - total_dist, x)
            assert sol and sol[0] == t
            dist1 = speed1 * t
            ans = str(dist1)
            return _lwp(5, params, ph, ans, scenario,
                        make_distractors(ans, [str(speed2 * t), str(total_dist // 2),
                                               str(dist1 + speed1), str(dist1 - speed1)]))

        else:
            raise NotImplementedError(f"linear_eq_word_problems d{difficulty} not implemented")

    raise RuntimeError(f"Could not generate unique params for linear_eq_word_problems d{difficulty}")


def _lwp(d, params, ph, ans, scenario, distractors, ctx=""):
    return {"skill": "linear_eq_word_problems", "difficulty": d, "questionType": "mcq",
            "params": params, "paramHash": ph, "verifiedAnswer": ans,
            "distractors": distractors, "sprMin": None, "sprMax": None,
            "scenarioTag": scenario, "diagramSpec": None,
            "questionContext": ctx or f"Set up and solve a linear equation word problem. The answer is {ans}."}
