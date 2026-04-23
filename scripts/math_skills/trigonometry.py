import math
import random
import sympy as sp
from sympy import symbols, solve, sqrt, Rational
from .core import (
    param_hash, fmt_num, fmt_fn, fmt_fx, fmt_lin_rhs,
    spr_bounds, make_distractors, pick_scenario, validate_math_object,
    PYTH_TRIPLES, LWP_SCENARIOS, PCT_SCENARIOS, RAT_SCENARIOS, PRP_SCENARIOS,
)

# ── Generator: trigonometry ───────────────────────────────────────────────────

PYTH_TRIPLES_TRG = [(3, 4, 5), (5, 12, 13), (8, 15, 17), (7, 24, 25), (6, 8, 10), (9, 12, 15)]


def _gcd(a, b):
    while b:
        a, b = b, a % b
    return a


def gen_trigonometry(difficulty: int, rng_obj: random.Random, exclude_params: set, **_):
    import fractions as _frac
    for _ in range(200):
        trip = rng_obj.choice(PYTH_TRIPLES_TRG)
        opp, adj, hyp = trip
        # Optionally swap opp/adj for variety
        if rng_obj.random() < 0.5:
            opp, adj = adj, opp

        if difficulty == 1:
            # sin(θ) = opp/hyp
            g = _gcd(opp, hyp)
            ans = f"{opp // g}/{hyp // g}"
            params = {"opp": opp, "adj": adj, "hyp": hyp, "ratio": "sin", "d": 1}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            g2 = _gcd(adj, hyp)
            d2 = [f"{adj // g2}/{hyp // g2}", f"{opp // g}/{adj // _gcd(opp,adj)}", f"{hyp}/{opp}"]
            diag = {"type": "right_triangle", "legs": [opp, adj], "hypotenuse": hyp,
                    "missing": None, "label_angle": "\u03b8"}
            return _trg(1, params, ph, ans, (None, None), diag, d2, "mcq")
        elif difficulty == 2:
            # cos(θ) = adj/hyp
            g = _gcd(adj, hyp)
            ans = f"{adj // g}/{hyp // g}"
            params = {"opp": opp, "adj": adj, "hyp": hyp, "ratio": "cos", "d": 2}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            g2 = _gcd(opp, hyp)
            d2 = [f"{opp // g2}/{hyp // g2}", f"{adj}/{opp}", f"{hyp}/{adj}"]
            diag = {"type": "right_triangle", "legs": [opp, adj], "hypotenuse": hyp,
                    "missing": None, "label_angle": "\u03b8"}
            return _trg(2, params, ph, ans, (None, None), diag, d2, "mcq")
        elif difficulty == 3:
            # tan(θ) = opp/adj
            g = _gcd(opp, adj)
            ans = f"{opp // g}/{adj // g}"
            params = {"opp": opp, "adj": adj, "hyp": hyp, "ratio": "tan", "d": 3}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            g2 = _gcd(adj, opp)
            d2 = [f"{adj // g2}/{opp // g2}", f"{opp // g}/{hyp // _gcd(opp, hyp)}", f"{hyp}/{opp}"]
            diag = {"type": "right_triangle", "legs": [opp, adj], "hypotenuse": hyp,
                    "missing": None, "label_angle": "\u03b8"}
            return _trg(3, params, ph, ans, (None, None), diag, d2, "mcq")
        elif difficulty == 4:
            # Given sin(θ) = opp/hyp, find cos(θ) = adj/hyp
            g_sin = _gcd(opp, hyp)
            g_cos = _gcd(adj, hyp)
            ans = f"{adj // g_cos}/{hyp // g_cos}"
            params = {"opp": opp, "adj": adj, "hyp": hyp, "ratio": "cos_from_sin", "d": 4}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            qt = "spr" if rng_obj.random() < 0.4 else "mcq"
            g2 = _gcd(opp, hyp)
            d2 = [f"{opp // g2}/{hyp // g2}", f"{adj}/{opp}", f"{hyp // g_cos}/{adj // g_cos}"]
            sb = spr_bounds(ans) if qt == "spr" else (None, None)
            diag = {"type": "right_triangle", "legs": [opp, adj], "hypotenuse": hyp,
                    "missing": None, "label_angle": "\u03b8"}
            return _trg(4, params, ph, ans, sb, diag, d2, qt)
        elif difficulty == 5:
            # Given angle (30/45/60) and one side, find another side
            angle = rng_obj.choice([30, 45, 60])
            k = rng_obj.randint(2, 8)
            if angle == 30:
                # hyp = 2k, opp = k, adj = k√3
                opp_val = k
                ask = "short_leg"
                ans = str(opp_val)
                params = {"angle": 30, "k": k, "given": "hyp", "find": ask, "d": 5}
                ph = param_hash(params)
                if ph in exclude_params:
                    continue
                distractors = make_distractors(ans, [str(k * 2), str(k + 1), f"{k}\u221a3"])
            elif angle == 45:
                # leg = k, hyp = k√2
                ask = "hyp"
                ans = f"{k}\u221a2"
                params = {"angle": 45, "k": k, "given": "leg", "find": ask, "d": 5}
                ph = param_hash(params)
                if ph in exclude_params:
                    continue
                distractors = [f"{k * 2}", f"{k}\u221a3", f"{k + 1}\u221a2"]
            else:  # 60
                # short = k, hyp = 2k, long = k√3
                ans = f"{k}\u221a3"
                params = {"angle": 60, "k": k, "given": "short_leg", "find": "long_leg", "d": 5}
                ph = param_hash(params)
                if ph in exclude_params:
                    continue
                distractors = [f"{k * 2}\u221a3", f"{k}\u221a2", f"{k + 1}\u221a3"]
            diag = {"type": "special_triangle", "variant": f"{angle}_spec",
                    "sides": [k, f"{k}\u221a3" if angle in [30, 60] else k, 2 * k if angle != 45 else f"{k}\u221a2"],
                    "angles": [30, 60, 90] if angle in [30, 60] else [45, 45, 90], "missing": None}
            return _trg(5, params, ph, ans, (None, None), diag, distractors, "mcq")
        raise RuntimeError(f"Could not generate unique params for trigonometry d{difficulty}")
    raise RuntimeError(f"Could not generate unique params for trigonometry d{difficulty}")


def _trg(d, params, ph, ans, spr_val, diag, distractors, qt="mcq"):
    sb = spr_val if qt == "spr" else (None, None)
    return {"skill": "trigonometry", "difficulty": d, "questionType": qt,
            "params": params, "paramHash": ph, "verifiedAnswer": ans,
            "distractors": distractors if qt == "mcq" else [], "sprMin": sb[0], "sprMax": sb[1],
            "scenarioTag": None, "diagramSpec": diag, "questionContext": ""}
