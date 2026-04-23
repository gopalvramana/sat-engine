import math
import random
import sympy as sp
from sympy import symbols, solve, sqrt, Rational
from .core import (
    param_hash, fmt_num, fmt_fn, fmt_fx, fmt_lin_rhs,
    spr_bounds, make_distractors, pick_scenario, validate_math_object,
    PYTH_TRIPLES, LWP_SCENARIOS, PCT_SCENARIOS, RAT_SCENARIOS, PRP_SCENARIOS,
)

# ── Generator: area_2d ────────────────────────────────────────────────────────

def gen_area_2d(difficulty: int, rng_obj: random.Random, exclude_params: set) -> dict:
    for _ in range(100):
        if difficulty == 1:
            l, w = rng_obj.randint(2, 12), rng_obj.randint(2, 12)
            area = l * w
            params = {"shape": "rectangle", "length": l, "width": w}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(area)
            diag = {"type": "rectangle", "length": l, "width": w}
            return _ara(1, params, ph, ans, None, diag,
                        make_distractors(ans, [str(2*(l+w)), str(area+l),
                                               str(l+w), str(area+w)]))

        elif difficulty == 2:
            b = rng_obj.randint(4, 16)
            h = rng_obj.randint(3, 12)
            if (b * h) % 2 != 0:
                h += 1
            area = b * h // 2
            params = {"shape": "triangle", "base": b, "height": h}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(area)
            diag = {"type": "triangle", "base": b, "height": h}
            return _ara(2, params, ph, ans, None, diag,
                        make_distractors(ans, [str(b*h), str(area+b),
                                               str(area-h//2), str(b+h)]))

        elif difficulty == 3:
            w = rng_obj.randint(4, 10)
            h1 = rng_obj.randint(3, 8)
            h2 = rng_obj.randint(3, 8)
            half_w = max(w // 2, 2)
            area = w * h1 + half_w * h2
            params = {"shape": "L_shape", "w": w, "h1": h1, "half_w": half_w, "h2": h2}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(area)
            diag = {"type": "composite_rectangle", "w": w, "h1": h1,
                    "half_w": half_w, "h2": h2}
            return _ara(3, params, ph, ans, None, diag,
                        make_distractors(ans, [str(w*(h1+h2)), str(area-half_w*h2//2),
                                               str(area+half_w), str(w*h1)]))

        elif difficulty == 4:
            l = rng_obj.randint(4, 12)
            w = rng_obj.randint(3, 10)
            area = l * w
            params = {"shape": "rectangle", "length": l, "area": area}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(w)
            qt = "spr" if rng_obj.random() < 0.4 else "mcq"
            sm, sx = spr_bounds(ans) if qt == "spr" else (None, None)
            diag = {"type": "rectangle", "length": l, "width": "?", "area": area}
            dist = make_distractors(ans, [str(area-l), str(area//(l+1)),
                                          str(w+1), str(w-1)]) if qt == "mcq" else []
            return _ara(4, params, ph, ans, (sm, sx), diag, dist, qt)

        elif difficulty == 5:
            l, w = rng_obj.randint(3, 8), rng_obj.randint(3, 8)
            k = rng_obj.randint(2, 4)
            orig_area = l * w
            new_area = (l * k) * (w * k)
            params = {"length": l, "width": w, "scale": k}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(new_area)
            diag = {"type": "scaled_rectangle", "orig_length": l,
                    "orig_width": w, "scale": k}
            return _ara(5, params, ph, ans, None, diag,
                        make_distractors(ans, [str(orig_area*k),
                                               str(orig_area + k*(l+w)),
                                               str(new_area+l*k),
                                               str(orig_area*(k+1))]))

        else:
            raise NotImplementedError(f"area_2d d{difficulty} not implemented")

    raise RuntimeError(f"Could not generate unique params for area_2d d{difficulty}")


def _ara(d, params, ph, ans, spr, diag, distractors, qt="mcq", ctx=""):
    sm, sx = spr if spr else (None, None)
    shape = (diag or {}).get("type", "shape")
    return {"skill": "area_2d", "difficulty": d, "questionType": qt,
            "params": params, "paramHash": ph, "verifiedAnswer": ans,
            "distractors": distractors, "sprMin": sm, "sprMax": sx,
            "scenarioTag": None, "diagramSpec": diag,
            "questionContext": ctx or f"Find the area (or missing dimension) of the {shape}. The answer is {ans}."}
