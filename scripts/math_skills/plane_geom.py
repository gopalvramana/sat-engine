import math
import random
import sympy as sp
from sympy import symbols, solve, sqrt, Rational
from .core import (
    param_hash, fmt_num, fmt_fn, fmt_fx, fmt_lin_rhs,
    spr_bounds, make_distractors, pick_scenario, validate_math_object,
    PYTH_TRIPLES, LWP_SCENARIOS, PCT_SCENARIOS, RAT_SCENARIOS, PRP_SCENARIOS,
)

# ── Generator: plane_geometry ─────────────────────────────────────────────────

def gen_plane_geometry(difficulty: int, rng_obj: random.Random, exclude_params: set) -> dict:
    for _ in range(100):
        if difficulty == 1:
            # Area of parallelogram: A = base × height
            base = rng_obj.randint(4, 14)
            height = rng_obj.randint(3, 10)
            area = base * height
            params = {"shape": "parallelogram", "base": base, "height": height}
            ph = param_hash(params)
            if ph in exclude_params: continue
            ans = str(area)
            diag = {"type": "parallelogram", "base": base, "height": height}
            return _plg(1, params, ph, ans, diag,
                        make_distractors(ans, [str(2*(base+height)), str(area+base),
                                               str(area//2), str(base+height)]),
                        ctx=f"Find the AREA of the parallelogram with base {base} and height {height}. A = base×height = {base}×{height} = {area}.")

        elif difficulty == 2:
            # Area of trapezoid: A = ½(b1+b2)×h
            b1 = rng_obj.randint(4, 14)
            b2 = rng_obj.randint(2, b1-1)
            h = rng_obj.randint(3, 10)
            if (b1 + b2) % 2 != 0: b2 += 1
            if b2 >= b1: continue
            area = (b1 + b2) * h // 2
            params = {"shape": "trapezoid", "b1": b1, "b2": b2, "h": h}
            ph = param_hash(params)
            if ph in exclude_params: continue
            ans = str(area)
            diag = {"type": "trapezoid", "base1": b1, "base2": b2, "height": h}
            return _plg(2, params, ph, ans, diag,
                        make_distractors(ans, [str((b1+b2)*h), str(b1*h//2),
                                               str(area+b2), str(area-h//2)]),
                        ctx=f"Find the AREA of the trapezoid with parallel sides {b1} and {b2}, height {h}. A = ½(b1+b2)×h = ½×{b1+b2}×{h} = {area}.")

        elif difficulty == 3:
            # Parallelogram: given area and base, find height
            base = rng_obj.randint(4, 12)
            height = rng_obj.randint(3, 10)
            area = base * height
            params = {"shape": "parallelogram_missing_h", "base": base, "area": area}
            ph = param_hash(params)
            if ph in exclude_params: continue
            ans = str(height)
            diag = {"type": "parallelogram", "base": base, "height": "?", "area": area}
            return _plg(3, params, ph, ans, diag,
                        make_distractors(ans, [str(area - base), str(area // base + 1),
                                               str(height + 1), str(height - 1)]),
                        ctx=f"A parallelogram has base {base} and area {area}. Find the HEIGHT. h = Area/base = {area}/{base} = {height}.")

        elif difficulty == 4:
            # Trapezoid: given area and both bases, find height
            b1 = rng_obj.randint(6, 14)
            b2 = rng_obj.randint(2, b1-2)
            h = rng_obj.randint(3, 10)
            if (b1 + b2) % 2 != 0: b2 += 1
            if b2 >= b1: continue
            area = (b1 + b2) * h // 2
            params = {"shape": "trapezoid_missing_h", "b1": b1, "b2": b2, "area": area}
            ph = param_hash(params)
            if ph in exclude_params: continue
            ans = str(h)
            diag = {"type": "trapezoid", "base1": b1, "base2": b2, "height": "?", "area": area}
            return _plg(4, params, ph, ans, diag,
                        make_distractors(ans, [str(area // b1), str(h + 1),
                                               str(h - 1), str(2*area // (b1+b2) + 1)]),
                        ctx=f"A trapezoid has parallel sides {b1} and {b2} with area {area}. Find the HEIGHT. h = 2A/(b1+b2) = 2×{area}/({b1}+{b2}) = {2*area}/({b1+b2}) = {h}.")

        elif difficulty == 5:
            # Composite: rectangle + triangle on top (house shape)
            rw = rng_obj.randint(4, 10)
            rh = rng_obj.randint(3, 8)
            th = rng_obj.randint(2, 6)
            area_rect = rw * rh
            area_tri = rw * th // 2
            if (rw * th) % 2 != 0: th += 1
            area_tri = rw * th // 2
            total = area_rect + area_tri
            params = {"shape": "house", "rw": rw, "rh": rh, "th": th}
            ph = param_hash(params)
            if ph in exclude_params: continue
            ans = str(total)
            diag = {"type": "house_shape", "width": rw, "rect_height": rh, "tri_height": th}
            return _plg(5, params, ph, ans, diag,
                        make_distractors(ans, [str(area_rect), str(area_rect + rw*th),
                                               str(total + rw), str(total - rw)]),
                        ctx=f"Find the total area of the composite shape (rectangle {rw}×{rh} plus triangle base {rw} height {th}). Total = {area_rect} + {area_tri} = {total}.")

        else:
            raise NotImplementedError(f"plane_geometry d{difficulty} not implemented")
    raise RuntimeError(f"Could not generate unique params for plane_geometry d{difficulty}")


def _plg(d, params, ph, ans, diag, distractors, ctx=""):
    shape = (diag or {}).get("type", "shape")
    return {"skill": "plane_geometry", "difficulty": d, "questionType": "mcq",
            "params": params, "paramHash": ph, "verifiedAnswer": ans,
            "distractors": distractors, "sprMin": None, "sprMax": None,
            "scenarioTag": None, "diagramSpec": diag, "questionContext": ctx}
