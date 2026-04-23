import math
import random
import sympy as sp
from sympy import symbols, solve, sqrt, Rational
from .core import (
    param_hash, fmt_num, fmt_fn, fmt_fx, fmt_lin_rhs,
    spr_bounds, make_distractors, pick_scenario, validate_math_object,
    PYTH_TRIPLES, LWP_SCENARIOS, PCT_SCENARIOS, RAT_SCENARIOS, PRP_SCENARIOS,
)

# ── Generator: volume_3d ──────────────────────────────────────────────────────

def gen_volume_3d(difficulty: int, rng_obj: random.Random, exclude_params: set) -> dict:
    for _ in range(100):
        if difficulty == 1:
            # d1: rectangular prism OR cube — straightforward integer volumes
            shape_type = rng_obj.choice(["rectangular_prism", "cube"])
            if shape_type == "cube":
                s = rng_obj.randint(2, 8)
                vol = s ** 3
                params = {"shape": "cube", "s": s}
                ph = param_hash(params)
                if ph in exclude_params: continue
                ans = str(vol)
                diag = {"type": "rectangular_prism", "length": s, "width": s, "height": s}
                return _vol(1, params, ph, ans, diag,
                            make_distractors(ans, [str(s*s*3), str(6*s*s), str(vol+s), str(s*3)]),
                            ctx=f"Find the VOLUME of the cube with side {s}. V = s³ = {s}³ = {vol}.")
            else:
                l = rng_obj.randint(2, 10)
                w = rng_obj.randint(2, 8)
                h = rng_obj.randint(2, 8)
                vol = l * w * h
                params = {"shape": "rectangular_prism", "l": l, "w": w, "h": h}
                ph = param_hash(params)
                if ph in exclude_params: continue
                ans = str(vol)
                diag = {"type": "rectangular_prism", "length": l, "width": w, "height": h}
                return _vol(1, params, ph, ans, diag,
                            make_distractors(ans, [str(2*(l*w+l*h+w*h)), str(l*w+l*h+w*h),
                                                   str(vol+l), str(l+w+h)]),
                            ctx=f"Find the VOLUME of the rectangular prism with l={l}, w={w}, h={h}. V = l×w×h = {l}×{w}×{h} = {vol}.")

        elif difficulty == 2:
            # d2: cylinder OR rectangular prism with larger numbers
            shape_type = rng_obj.choice(["cylinder", "rectangular_prism"])
            if shape_type == "cylinder":
                r = rng_obj.randint(2, 7)
                h = rng_obj.randint(2, 10)
                coeff = r * r * h
                params = {"shape": "cylinder", "r": r, "h": h}
                ph = param_hash(params)
                if ph in exclude_params: continue
                ans = f"{coeff}π"
                diag = {"type": "cylinder", "radius": r, "height": h}
                return _vol(2, params, ph, ans, diag,
                            make_distractors(ans, [f"{2*r*h}π", f"{r*h}π",
                                                   f"{coeff*2}π", f"{r*r}π"]),
                            ctx=f"Find the VOLUME of the cylinder with radius {r} and height {h}. V = πr²h = π×{r}²×{h} = {coeff}π.")
            else:
                l = rng_obj.randint(4, 15)
                w = rng_obj.randint(3, 12)
                h = rng_obj.randint(3, 12)
                vol = l * w * h
                params = {"shape": "rectangular_prism", "l": l, "w": w, "h": h}
                ph = param_hash(params)
                if ph in exclude_params: continue
                ans = str(vol)
                diag = {"type": "rectangular_prism", "length": l, "width": w, "height": h}
                return _vol(2, params, ph, ans, diag,
                            make_distractors(ans, [str(2*(l*w+l*h+w*h)), str(l*w+l*h+w*h),
                                                   str(vol+l*w), str(l+w+h)]),
                            ctx=f"Find the VOLUME of the rectangular prism with l={l}, w={w}, h={h}. V = l×w×h = {l}×{w}×{h} = {vol}.")

        elif difficulty == 3:
            # d3: cone OR sphere OR cylinder — all involve π
            shape_type = rng_obj.choice(["cone", "sphere", "cylinder"])
            if shape_type == "cone":
                combos = [(r, h) for r in range(2, 8) for h in range(3, 12, 3)]
                r, h = rng_obj.choice(combos)
                coeff = r * r * h // 3
                if coeff <= 0: continue
                params = {"shape": "cone", "r": r, "h": h}
                ph = param_hash(params)
                if ph in exclude_params: continue
                ans = f"{coeff}π"
                diag = {"type": "cone", "radius": r, "height": h}
                return _vol(3, params, ph, ans, diag,
                            make_distractors(ans, [f"{r*r*h}π", f"{coeff*3}π",
                                                   f"{coeff*2}π", f"{r*h}π"]),
                            ctx=f"Find the VOLUME of the cone with radius {r} and height {h}. V = (1/3)πr²h = (1/3)×π×{r}²×{h} = {coeff}π.")
            elif shape_type == "sphere":
                r = rng_obj.choice([3, 6, 9])
                coeff = (4 * r * r * r) // 3
                params = {"shape": "sphere", "r": r}
                ph = param_hash(params)
                if ph in exclude_params: continue
                ans = f"{coeff}π"
                diag = {"type": "sphere", "radius": r}
                return _vol(3, params, ph, ans, diag,
                            make_distractors(ans, [f"{r*r*r}π", f"{4*r*r*r}π",
                                                   f"{coeff+r*r}π", f"{2*r}π"]),
                            ctx=f"Find the VOLUME of the sphere with radius {r}. V = (4/3)πr³ = (4/3)×π×{r}³ = {coeff}π.")
            else:  # cylinder
                r = rng_obj.randint(2, 7)
                h = rng_obj.randint(2, 10)
                coeff = r * r * h
                params = {"shape": "cylinder", "r": r, "h": h}
                ph = param_hash(params)
                if ph in exclude_params: continue
                ans = f"{coeff}π"
                diag = {"type": "cylinder", "radius": r, "height": h}
                return _vol(3, params, ph, ans, diag,
                            make_distractors(ans, [f"{2*r*h}π", f"{r*h}π",
                                                   f"{coeff*2}π", f"{r*r}π"]),
                            ctx=f"Find the VOLUME of the cylinder with radius {r} and height {h}. V = πr²h = π×{r}²×{h} = {coeff}π.")

        elif difficulty == 4:
            # d4: any shape OR reverse-problem (given volume, find dimension)
            shape_type = rng_obj.choice(["cone", "sphere", "cylinder_missing_h", "cone_large"])
            if shape_type == "cone_large":
                combos = [(r, h) for r in range(4, 12) for h in range(3, 15, 3)]
                r, h = rng_obj.choice(combos)
                coeff = r * r * h // 3
                if coeff <= 0: continue
                params = {"shape": "cone", "r": r, "h": h}
                ph = param_hash(params)
                if ph in exclude_params: continue
                ans = f"{coeff}π"
                diag = {"type": "cone", "radius": r, "height": h}
                return _vol(4, params, ph, ans, diag,
                            make_distractors(ans, [f"{r*r*h}π", f"{coeff*3}π",
                                                   f"{coeff*2}π", f"{r*h}π"]),
                            ctx=f"Find the VOLUME of the cone with radius {r} and height {h}. V = (1/3)πr²h = (1/3)×π×{r}²×{h} = {coeff}π.")
            elif shape_type == "sphere":
                r = rng_obj.choice([3, 6, 9])
                coeff = (4 * r * r * r) // 3
                params = {"shape": "sphere", "r": r}
                ph = param_hash(params)
                if ph in exclude_params: continue
                ans = f"{coeff}π"
                diag = {"type": "sphere", "radius": r}
                return _vol(4, params, ph, ans, diag,
                            make_distractors(ans, [f"{r*r*r}π", f"{4*r*r*r}π",
                                                   f"{coeff+r*r}π", f"{2*r}π"]),
                            ctx=f"Find the VOLUME of the sphere with radius {r}. V = (4/3)πr³ = (4/3)×π×{r}³ = {coeff}π.")
            elif shape_type == "cone":
                combos = [(r, h) for r in range(2, 8) for h in range(3, 12, 3)]
                r, h = rng_obj.choice(combos)
                coeff = r * r * h // 3
                if coeff <= 0: continue
                params = {"shape": "cone", "r": r, "h": h}
                ph = param_hash(params)
                if ph in exclude_params: continue
                ans = f"{coeff}π"
                diag = {"type": "cone", "radius": r, "height": h}
                return _vol(4, params, ph, ans, diag,
                            make_distractors(ans, [f"{r*r*h}π", f"{coeff*3}π",
                                                   f"{coeff*2}π", f"{r*h}π"]),
                            ctx=f"Find the VOLUME of the cone with radius {r} and height {h}. V = (1/3)πr²h = (1/3)×π×{r}²×{h} = {coeff}π.")
            else:  # cylinder_missing_h
                r = rng_obj.randint(2, 6)
                h = rng_obj.randint(3, 10)
                coeff = r * r * h
                params = {"shape": "cylinder_missing_h", "r": r, "vol_coeff": coeff}
                ph = param_hash(params)
                if ph in exclude_params: continue
                ans = str(h)
                diag = {"type": "cylinder", "radius": r, "height": "?"}
                return _vol(4, params, ph, ans, diag,
                            make_distractors(ans, [str(coeff // r), str(h + r),
                                                   str(h - 1), str(coeff)]),
                            ctx=f"A cylinder has radius {r} and volume {coeff}π. Find the HEIGHT. V = πr²h → h = V/(πr²) = {coeff}π/(π×{r}²) = {coeff}/{r*r} = {h}.")

        elif difficulty == 5:
            # d5: reverse-problem (given volume, find missing dimension)
            rev_type = rng_obj.choice(["cylinder_missing_h", "cylinder_missing_r",
                                       "cone_missing_h"])
            if rev_type == "cylinder_missing_h":
                r = rng_obj.randint(2, 6)
                h = rng_obj.randint(3, 12)
                coeff = r * r * h
                params = {"shape": "cylinder_missing_h", "r": r, "vol_coeff": coeff}
                ph = param_hash(params)
                if ph in exclude_params: continue
                ans = str(h)
                diag = {"type": "cylinder", "radius": r, "height": "?"}
                return _vol(5, params, ph, ans, diag,
                            make_distractors(ans, [str(coeff // r), str(h + r),
                                                   str(h - 1), str(coeff)]),
                            ctx=f"A cylinder has radius {r} and volume {coeff}π. Find the HEIGHT. V = πr²h → h = V/(πr²) = {coeff}π/(π×{r}²) = {coeff}/{r*r} = {h}.")
            elif rev_type == "cylinder_missing_r":
                # choose r so r² divides coeff cleanly
                r = rng_obj.randint(2, 6)
                h = rng_obj.randint(3, 10)
                coeff = r * r * h
                params = {"shape": "cylinder_missing_r", "h": h, "vol_coeff": coeff}
                ph = param_hash(params)
                if ph in exclude_params: continue
                ans = str(r)
                diag = {"type": "cylinder", "radius": "?", "height": h}
                return _vol(5, params, ph, ans, diag,
                            make_distractors(ans, [str(r + 1), str(r - 1),
                                                   str(r * 2), str(coeff // h)]),
                            ctx=f"A cylinder has height {h} and volume {coeff}π. Find the RADIUS. V = πr²h → r² = V/(πh) = {coeff}/{h} = {r*r} → r = {r}.")
            else:  # cone_missing_h
                combos = [(r, h) for r in range(3, 8) for h in range(3, 15, 3)]
                r, h = rng_obj.choice(combos)
                coeff = r * r * h // 3
                if coeff <= 0: continue
                params = {"shape": "cone_missing_h", "r": r, "vol_coeff": coeff}
                ph = param_hash(params)
                if ph in exclude_params: continue
                ans = str(h)
                diag = {"type": "cone", "radius": r, "height": "?"}
                return _vol(5, params, ph, ans, diag,
                            make_distractors(ans, [str(h + 3), str(h - 3),
                                                   str(coeff // (r*r)), str(3 * coeff // (r*r))]),
                            ctx=f"A cone has radius {r} and volume {coeff}π. Find the HEIGHT. V = (1/3)πr²h → h = 3V/(πr²) = 3×{coeff}/{r*r} = {h}.")

        else:
            raise NotImplementedError(f"volume_3d d{difficulty} not implemented")
    raise RuntimeError(f"Could not generate unique params for volume_3d d{difficulty}")


def _vol(d, params, ph, ans, diag, distractors, ctx=""):
    shape = (diag or {}).get("type", "solid")
    return {"skill": "volume_3d", "difficulty": d, "questionType": "mcq",
            "params": params, "paramHash": ph, "verifiedAnswer": ans,
            "distractors": distractors, "sprMin": None, "sprMax": None,
            "scenarioTag": None, "diagramSpec": diag, "questionContext": ctx}
