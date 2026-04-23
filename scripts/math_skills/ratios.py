import math
import random
import sympy as sp
from sympy import symbols, solve, sqrt, Rational
from .core import (
    param_hash, fmt_num, fmt_fn, fmt_fx, fmt_lin_rhs,
    spr_bounds, make_distractors, pick_scenario, validate_math_object,
    PYTH_TRIPLES, LWP_SCENARIOS, PCT_SCENARIOS, RAT_SCENARIOS, PRP_SCENARIOS,
)

# ── Generator: ratios_rates ───────────────────────────────────────────────────

def gen_ratios_rates(difficulty: int, rng_obj: random.Random,
                     exclude_params: set, exclude_scenarios: set) -> dict:
    scenario = pick_scenario(RAT_SCENARIOS, exclude_scenarios, rng_obj)
    for _ in range(100):
        if difficulty == 1:
            a, b = rng_obj.randint(1, 5), rng_obj.randint(1, 5)
            k = rng_obj.randint(2, 8)
            total = (a + b) * k
            answer = a * k
            params = {"ratio_a": a, "ratio_b": b, "total": total, "scenario": scenario}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(answer)
            ctx = (f"Two quantities are in the ratio {a}:{b} and their total is {total}. "
                   f"Find the amount corresponding to the first part of the ratio. Answer = {ans}.")
            return _rat(1, params, ph, ans, scenario,
                        make_distractors(ans, [str(b*k), str(total//(a+b)),
                                               str(total//a), str(answer+k)]), ctx)

        elif difficulty == 2:
            unit = rng_obj.randint(2, 10)
            n, m = rng_obj.randint(3, 10), rng_obj.randint(3, 12)
            while m == n:
                m = rng_obj.randint(3, 12)
            answer = unit * m
            params = {"n": n, "cost_n": unit*n, "m": m, "scenario": scenario}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            assert unit * n * m // n == answer
            ans = str(answer)
            ctx = (f"If {n} units cost {unit*n}, find the cost of {m} units using the same unit rate. "
                   f"Answer = {ans}.")
            return _rat(2, params, ph, ans, scenario,
                        make_distractors(ans, [str(unit*n + m), str(unit*(m+1)),
                                               str(answer+unit), str(unit*n)]), ctx)

        elif difficulty == 3:
            a, b, c = rng_obj.randint(1, 4), rng_obj.randint(1, 4), rng_obj.randint(1, 4)
            k = rng_obj.randint(2, 6)
            total = (a + b + c) * k
            answer = a * k
            params = {"ra": a, "rb": b, "rc": c, "total": total, "scenario": scenario}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(answer)
            ctx = (f"Three quantities are in the ratio {a}:{b}:{c} and their total is {total}. "
                   f"Find the value of the first quantity. Answer = {ans}.")
            return _rat(3, params, ph, ans, scenario,
                        make_distractors(ans, [str(b*k), str(c*k),
                                               str(total//3), str(answer+k)]), ctx)

        elif difficulty == 4:
            speed = rng_obj.choice([20, 25, 30, 40, 50, 60])
            time = rng_obj.randint(2, 6)
            distance = speed * time
            params = {"distance": distance, "speed": speed, "scenario": scenario}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(time)
            ctx = (f"Something travels {distance} units at a rate of {speed} units per hour. "
                   f"Find how many hours it takes (time = distance ÷ rate). Answer = {ans}.")
            return _rat(4, params, ph, ans, scenario,
                        make_distractors(ans, [str(time+1), str(time*2),
                                               str(distance-speed), str(distance//speed+1)]), ctx)

        elif difficulty == 5:
            d1 = rng_obj.choice([20, 30, 40, 60, 80, 100, 120])
            d2 = rng_obj.choice([20, 30, 40, 60, 80, 100, 120])
            s1 = rng_obj.choice([20, 30, 40, 50, 60])
            s2 = rng_obj.choice([20, 30, 40, 50, 60])
            while s1 == s2:
                s2 = rng_obj.choice([20, 30, 40, 50, 60])
            if d1 % s1 != 0 or d2 % s2 != 0:
                continue
            t1, t2 = d1 // s1, d2 // s2
            if (d1 + d2) % (t1 + t2) != 0:
                continue
            avg = (d1 + d2) // (t1 + t2)
            params = {"d1": d1, "s1": s1, "d2": d2, "s2": s2, "scenario": scenario}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(avg)
            ctx = (f"A two-leg journey: first {d1} miles at {s1} mph, then {d2} miles at {s2} mph. "
                   f"Find the average speed for the entire trip (total distance ÷ total time). "
                   f"Answer = {ans}. Note: average speed ≠ arithmetic mean of the two speeds.")
            return _rat(5, params, ph, ans, scenario,
                        make_distractors(ans, [str((s1+s2)//2), str(avg+5),
                                               str(avg-5), str((s1+s2+avg)//3)]), ctx)

        else:
            raise NotImplementedError(f"ratios_rates d{difficulty} not implemented")

    raise RuntimeError(f"Could not generate unique params for ratios_rates d{difficulty}")


def _rat(d, params, ph, ans, scenario, distractors, ctx=""):
    return {"skill": "ratios_rates", "difficulty": d, "questionType": "mcq",
            "params": params, "paramHash": ph, "verifiedAnswer": ans,
            "distractors": distractors, "sprMin": None, "sprMax": None,
            "scenarioTag": scenario, "diagramSpec": None,
            "questionContext": ctx or f"Solve the ratio/rate problem. The answer is {ans}."}
