import math
import random
import sympy as sp
from sympy import symbols, solve, sqrt, Rational
from .core import (
    param_hash, fmt_num, fmt_fn, fmt_fx, fmt_lin_rhs,
    spr_bounds, make_distractors, pick_scenario, validate_math_object,
    PYTH_TRIPLES, LWP_SCENARIOS, PCT_SCENARIOS, RAT_SCENARIOS, PRP_SCENARIOS,
)

# ── Generator: circles ───────────────────────────────────────────────────────
# All π-answers stored as strings like "10π"; LLM sees them as MCQ options.

def gen_circles(difficulty: int, rng_obj: random.Random, exclude_params: set) -> dict:
    for _ in range(100):
        if difficulty == 1:
            # Circumference given radius: C = 2πr
            r = rng_obj.randint(2, 12)
            params = {"r": r, "ask": "circumference"}
            ph = param_hash(params)
            if ph in exclude_params: continue
            ans = f"{2*r}π"
            diag = {"type": "circle", "radius": r}
            return _cir(1, params, ph, ans, diag,
                        make_distractors(ans, [f"{r}π", f"{4*r}π", f"{r*r}π"]),
                        ctx=f"Find the CIRCUMFERENCE of a circle with radius {r}. C = 2πr = 2π×{r} = {2*r}π.")

        elif difficulty == 2:
            # Area given radius: A = πr²
            r = rng_obj.randint(2, 10)
            params = {"r": r, "ask": "area"}
            ph = param_hash(params)
            if ph in exclude_params: continue
            ans = f"{r*r}π"
            diag = {"type": "circle", "radius": r}
            return _cir(2, params, ph, ans, diag,
                        make_distractors(ans, [f"{2*r}π", f"{r*r*2}π", f"{r*r+r}π"]),
                        ctx=f"Find the AREA of a circle with radius {r}. A = πr² = π×{r}² = {r*r}π.")

        elif difficulty == 3:
            # Circumference given diameter: C = πd
            d = rng_obj.randint(4, 18)
            if d % 2 != 0: d += 1
            r = d // 2
            params = {"d": d, "ask": "circumference_from_diameter"}
            ph = param_hash(params)
            if ph in exclude_params: continue
            ans = f"{d}π"
            diag = {"type": "circle", "diameter": d}
            return _cir(3, params, ph, ans, diag,
                        make_distractors(ans, [f"{r}π", f"{2*d}π", f"{r*r}π"]),
                        ctx=f"Find the CIRCUMFERENCE of a circle with diameter {d}. C = πd = π×{d} = {d}π.")

        elif difficulty == 4:
            # Arc length: arc = (θ/360) × 2πr  — choose θ and r so result is integer × π
            r = rng_obj.choice([3, 4, 6, 9, 12])
            θ_choices = [(60, 6), (90, 4), (120, 3), (45, 8), (180, 2), (30, 12)]
            θ, divisor = rng_obj.choice(θ_choices)
            arc_coeff = (2 * r) // divisor   # arc = arc_coeff × π
            if arc_coeff <= 0: continue
            params = {"r": r, "theta": θ, "ask": "arc_length"}
            ph = param_hash(params)
            if ph in exclude_params: continue
            ans = f"{arc_coeff}π"
            diag = {"type": "circle", "radius": r, "sector_angle": θ}
            return _cir(4, params, ph, ans, diag,
                        make_distractors(ans, [f"{arc_coeff*2}π", f"{r*r}π",
                                               f"{arc_coeff+1}π", f"{θ}π"]),
                        ctx=f"Find the ARC LENGTH of the sector with radius {r} and central angle {θ}°. Arc = (θ/360)×2πr = ({θ}/360)×{2*r}π = {arc_coeff}π.")

        elif difficulty == 5:
            # Sector area: A = (θ/360) × πr²  — choose θ and r so result is integer × π
            r = rng_obj.choice([3, 4, 6, 9, 12])
            θ_choices = [(90, 4), (60, 6), (120, 3), (180, 2), (45, 8)]
            θ, divisor = rng_obj.choice(θ_choices)
            sec_coeff = (r * r) // divisor
            if sec_coeff <= 0: continue
            params = {"r": r, "theta": θ, "ask": "sector_area"}
            ph = param_hash(params)
            if ph in exclude_params: continue
            ans = f"{sec_coeff}π"
            diag = {"type": "circle", "radius": r, "sector_angle": θ}
            return _cir(5, params, ph, ans, diag,
                        make_distractors(ans, [f"{sec_coeff*2}π", f"{r*r}π",
                                               f"{sec_coeff+r}π", f"{2*r}π"]),
                        ctx=f"Find the SECTOR AREA with radius {r} and central angle {θ}°. A = (θ/360)×πr² = ({θ}/360)×{r*r}π = {sec_coeff}π.")

        else:
            raise NotImplementedError(f"circles d{difficulty} not implemented")
    raise RuntimeError(f"Could not generate unique params for circles d{difficulty}")


def _cir(d, params, ph, ans, diag, distractors, ctx=""):
    return {"skill": "circles", "difficulty": d, "questionType": "mcq",
            "params": params, "paramHash": ph, "verifiedAnswer": ans,
            "distractors": distractors, "sprMin": None, "sprMax": None,
            "scenarioTag": None, "diagramSpec": diag, "questionContext": ctx}
