import math
import random
import sympy as sp
from sympy import symbols, solve, sqrt, Rational
from .core import (
    param_hash, fmt_num, fmt_fn, fmt_fx, fmt_lin_rhs,
    spr_bounds, make_distractors, pick_scenario, validate_math_object,
    PYTH_TRIPLES, LWP_SCENARIOS, PCT_SCENARIOS, RAT_SCENARIOS, PRP_SCENARIOS,
)

# ── Generator: coordinate_geometry ───────────────────────────────────────────

def gen_coordinate_geometry(difficulty: int, rng_obj: random.Random, exclude_params: set) -> dict:
    for _ in range(100):
        if difficulty == 1:
            x1, y1 = rng_obj.randint(-4, 4), rng_obj.randint(-4, 4)
            dx = rng_obj.randint(1, 4)
            m = rng_obj.choice([-3, -2, -1, 1, 2, 3])
            x2, y2 = x1 + dx, y1 + m * dx
            params = {"x1": x1, "y1": y1, "x2": x2, "y2": y2, "question": "slope"}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            assert Rational(y2-y1, x2-x1) == m
            ans = str(m)
            diag = {"type": "coordinate_plane", "points": [[x1, y1], [x2, y2]]}
            return _cge(1, params, ph, ans, diag,
                        make_distractors(ans, [str(m+1), str(-m), str(m-1),
                                               fmt_num(Rational(x2-x1, y2-y1))]),
                        ctx=f"Find the SLOPE of the line through ({x1},{y1}) and ({x2},{y2}). The slope is {ans}.")

        elif difficulty == 2:
            x1, y1 = rng_obj.randint(-6, 6), rng_obj.randint(-6, 6)
            x2, y2 = rng_obj.randint(-6, 6), rng_obj.randint(-6, 6)
            if (x1+x2) % 2 != 0:
                x2 += 1
            if (y1+y2) % 2 != 0:
                y2 += 1
            mx, my = (x1+x2) // 2, (y1+y2) // 2
            params = {"x1": x1, "y1": y1, "x2": x2, "y2": y2, "question": "midpoint_x"}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(mx)
            diag = {"type": "coordinate_plane", "points": [[x1, y1], [x2, y2]],
                    "highlight_point": [mx, my]}
            return _cge(2, params, ph, ans, diag,
                        make_distractors(ans, [str(my), str(mx+1), str(x1), str(x2)]),
                        ctx=f"Find the X-COORDINATE of the midpoint between ({x1},{y1}) and ({x2},{y2}). The midpoint is ({mx},{my}), so the answer is the x-coordinate: {ans}. Do NOT ask for the y-coordinate.")

        elif difficulty == 3:
            dx, dy, dist = rng_obj.choice(PYTH_TRIPLES[:8])
            x1, y1 = rng_obj.randint(-4, 4), rng_obj.randint(-4, 4)
            x2, y2 = x1 + dx, y1 + dy
            params = {"x1": x1, "y1": y1, "x2": x2, "y2": y2, "question": "distance"}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            assert int(sqrt((x2-x1)**2 + (y2-y1)**2)) == dist
            ans = str(dist)
            diag = {"type": "coordinate_plane", "points": [[x1, y1], [x2, y2]]}
            return _cge(3, params, ph, ans, diag,
                        make_distractors(ans, [str(dx+dy), str(dist+1),
                                               str(dist-1), str(max(dx, dy))]),
                        ctx=f"Find the DISTANCE between ({x1},{y1}) and ({x2},{y2}) using the distance formula. The distance is {ans}.")

        elif difficulty == 4:
            x1, y1 = rng_obj.randint(-5, 5), rng_obj.randint(-5, 5)
            mx, my = rng_obj.randint(-3, 3), rng_obj.randint(-3, 3)
            x2, y2 = 2*mx - x1, 2*my - y1
            params = {"x1": x1, "y1": y1, "mx": mx, "my": my,
                      "question": "missing_endpoint_x"}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(x2)
            diag = {"type": "coordinate_plane",
                    "points": [[x1, y1], [mx, my]],
                    "highlight_point": [x2, y2]}
            return _cge(4, params, ph, ans, diag,
                        make_distractors(ans, [str(y2), str(mx),
                                               str(x2+1), str(2*mx+x1)]),
                        ctx=f"Find the X-COORDINATE of the missing endpoint. One endpoint is ({x1},{y1}), the midpoint is ({mx},{my}). The missing endpoint is ({x2},{y2}), so the answer is the x-coordinate: {ans}. Do NOT ask for y-coordinate.")

        elif difficulty == 5:
            x1 = rng_obj.randint(-4, 0)
            x2 = rng_obj.randint(1, 4)
            m = rng_obj.choice([-2, -1, 1, 2, 3])
            b = rng_obj.randint(-5, 5)
            y1, y2 = m*x1 + b, m*x2 + b
            x3 = rng_obj.randint(-6, 6)
            while x3 == x1 or x3 == x2:
                x3 += 1
            k = m * x3 + b
            params = {"x1": x1, "y1": y1, "x2": x2, "y2": y2,
                      "x3": x3, "question": "collinear_y"}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(k)
            diag = {"type": "coordinate_plane",
                    "points": [[x1, y1], [x2, y2], [x3, "?"]],
                    "function": fmt_fn(m, b)}
            return _cge(5, params, ph, ans, diag,
                        make_distractors(ans, [str(k+1), str(k-1),
                                               str(m*x3 - b), str(k+m)]),
                        ctx=f"Points ({x1},{y1}), ({x2},{y2}), ({x3},?) are collinear on {fmt_fn(m, b)}. Find the Y-COORDINATE of the third point when x={x3}. The answer is y={ans}.")

        else:
            raise NotImplementedError(f"coordinate_geometry d{difficulty} not implemented")

    raise RuntimeError(f"Could not generate unique params for coordinate_geometry d{difficulty}")


def _cge(d, params, ph, ans, diag, distractors, ctx=""):
    return {"skill": "coordinate_geometry", "difficulty": d, "questionType": "mcq",
            "params": params, "paramHash": ph, "verifiedAnswer": ans,
            "distractors": distractors, "sprMin": None, "sprMax": None,
            "scenarioTag": None, "diagramSpec": diag, "questionContext": ctx}
