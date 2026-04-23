import math
import random
import sympy as sp
from sympy import symbols, solve, sqrt, Rational
from .core import (
    param_hash, fmt_num, fmt_fn, fmt_fx, fmt_lin_rhs,
    spr_bounds, make_distractors, pick_scenario, validate_math_object,
    PYTH_TRIPLES, LWP_SCENARIOS, PCT_SCENARIOS, RAT_SCENARIOS, PRP_SCENARIOS,
)

# ── Generator: probability ───────────────────────────────────────────────────

PRB_SCENARIOS = ["card_deck", "marble_bag", "coin_flip", "dice_roll",
                 "spinner", "survey_data", "class_selection", "colored_tiles"]


def _gcd(a, b):
    while b:
        a, b = b, a % b
    return a


def gen_probability(difficulty: int, rng_obj: random.Random, exclude_params: set,
                    exclude_scenarios: set, **_):
    for _ in range(200):
        scenario = rng_obj.choice([s for s in PRB_SCENARIOS if s not in exclude_scenarios] or PRB_SCENARIOS)
        if difficulty == 1:
            total = rng_obj.choice([4, 5, 6, 8, 10, 12, 20])
            favorable = rng_obj.randint(1, total - 1)
            g = _gcd(favorable, total)
            p_num, p_den = favorable // g, total // g
            params = {"favorable": favorable, "total": total, "scenario": scenario, "d": 1}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = f"{p_num}/{p_den}" if p_den > 1 else str(p_num)
            d2 = make_distractors(ans, [f"{favorable + 1}/{total}", f"{total - favorable}/{total}", f"{favorable}/{total + 1}"])
            return _prb(1, params, ph, ans, d2, "mcq", scenario)
        elif difficulty == 2:
            total = rng_obj.choice([4, 5, 6, 8, 10, 12, 20])
            favorable = rng_obj.randint(1, total - 1)
            comp = total - favorable
            g = _gcd(comp, total)
            p_num, p_den = comp // g, total // g
            params = {"favorable": favorable, "total": total, "scenario": scenario, "d": 2}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = f"{p_num}/{p_den}" if p_den > 1 else str(p_num)
            fav_g = _gcd(favorable, total)
            fav_str = f"{favorable // fav_g}/{total // fav_g}" if total // fav_g > 1 else str(favorable // fav_g)
            d2 = make_distractors(ans, [fav_str, f"{favorable + comp + 1}/{total}", "0"])
            return _prb(2, params, ph, ans, d2, "mcq", scenario)
        elif difficulty == 3:
            total_a = rng_obj.choice([4, 5, 6, 8, 10])
            fav_a = rng_obj.randint(1, total_a - 1)
            total_b = rng_obj.choice([4, 5, 6, 8, 10])
            fav_b = rng_obj.randint(1, total_b - 1)
            num = fav_a * fav_b
            den = total_a * total_b
            g = _gcd(num, den)
            p_num, p_den = num // g, den // g
            params = {"fav_a": fav_a, "total_a": total_a, "fav_b": fav_b, "total_b": total_b,
                      "scenario": scenario, "d": 3}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = f"{p_num}/{p_den}" if p_den > 1 else str(p_num)
            d2 = [f"{fav_a + fav_b}/{total_a * total_b}", f"{fav_a * fav_b + 1}/{den}",
                  f"{(fav_a + fav_b)}/{total_a + total_b}"]
            return _prb(3, params, ph, ans, d2, "mcq", scenario)
        elif difficulty == 4:
            total = rng_obj.choice([10, 12, 15, 20])
            fav_a = rng_obj.randint(1, total // 2)
            fav_b = rng_obj.randint(1, total // 2)
            while fav_a + fav_b > total:
                fav_b = rng_obj.randint(1, total // 2)
            num = fav_a + fav_b
            g = _gcd(num, total)
            p_num, p_den = num // g, total // g
            params = {"fav_a": fav_a, "fav_b": fav_b, "total": total, "scenario": scenario, "d": 4}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = f"{p_num}/{p_den}" if p_den > 1 else str(p_num)
            g2 = _gcd(fav_a, total)
            d2 = [f"{fav_a // g2}/{total // g2}", f"{(fav_a + fav_b - 1)}/{total}",
                  f"{(fav_a * fav_b)}/{total * total}"]
            return _prb(4, params, ph, ans, d2, "mcq", scenario)
        elif difficulty == 5:
            # Conditional probability from 2x2 table
            a = rng_obj.randint(5, 20)
            b = rng_obj.randint(5, 20)
            c = rng_obj.randint(5, 20)
            d_cell = rng_obj.randint(5, 20)
            row1_total = a + b
            g = _gcd(a, row1_total)
            p_num, p_den = a // g, row1_total // g
            params = {"cells": [a, b, c, d_cell], "scenario": scenario, "d": 5}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = f"{p_num}/{p_den}" if p_den > 1 else str(p_num)
            grand = a + b + c + d_cell
            col1 = a + c
            g2 = _gcd(col1, grand)
            d2 = [f"{col1 // g2}/{grand // g2}", f"{b}/{row1_total}", f"{a}/{grand}"]
            return _prb(5, params, ph, ans, d2, "mcq", scenario)
        raise RuntimeError(f"Could not generate unique params for probability d{difficulty}")
    raise RuntimeError(f"Could not generate unique params for probability d{difficulty}")


def _prb(d, params, ph, ans, distractors, qt="mcq", scenario=None):
    return {"skill": "probability", "difficulty": d, "questionType": "mcq",
            "params": params, "paramHash": ph, "verifiedAnswer": ans,
            "distractors": distractors, "sprMin": None, "sprMax": None,
            "scenarioTag": scenario, "diagramSpec": None, "questionContext": ""}
