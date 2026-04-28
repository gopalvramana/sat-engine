import math as _math
import random
import sympy as sp
from sympy import symbols, solve, sqrt, Rational
from .core import (
    param_hash, fmt_num, fmt_fn, fmt_fx, fmt_lin_rhs,
    spr_bounds, make_distractors, pick_scenario, validate_math_object,
    PYTH_TRIPLES, LWP_SCENARIOS, PCT_SCENARIOS, RAT_SCENARIOS, PRP_SCENARIOS,
)

# ── Helper ────────────────────────────────────────────────────────────────────

def _l2v(d, params, ph, ans, distractors, sm, sx, qt, ctx, diag=None):
    return {"skill": "linear_eq_two_var", "difficulty": d, "questionType": qt,
            "params": params, "paramHash": ph, "verifiedAnswer": ans,
            "distractors": distractors, "sprMin": sm, "sprMax": sx,
            "scenarioTag": None, "diagramSpec": diag, "questionContext": ctx}


def _si(m_rat: Rational, intercept: int) -> str:
    """Format y = (m_rat)x ± intercept with NO parentheses around fractions."""
    mn, md = m_rat.numerator, m_rat.denominator
    if md == 1:
        return fmt_fn(mn, intercept)
    if intercept > 0:
        return f"y = {mn}/{md}x + {intercept}"
    if intercept < 0:
        return f"y = {mn}/{md}x - {abs(intercept)}"
    return f"y = {mn}/{md}x"


# ── d1 template functions ─────────────────────────────────────────────────────

def _d1_read_slope(rng_obj, exclude_params, variant=None):
    """T2 Easy: given y = mx + b, identify the slope m."""
    for _ in range(200):
        m = rng_obj.choice([i for i in range(-4, 5) if i != 0])
        b = rng_obj.choice([i for i in range(-6, 7) if i != 0 and i != m and i != -m])
        # Variant gate
        if variant == "pos_slope" and m < 0:
            continue
        if variant == "neg_slope" and m > 0:
            continue
        sub = variant or ("pos_slope" if m > 0 else "neg_slope")
        params = {"m": m, "b": b, "tpl": "read_slope", "variant": sub}
        ph = param_hash(params)
        if ph in exclude_params:
            continue

        x_sym = sp.Symbol("x")
        assert sp.expand(m * x_sym + b).coeff(x_sym) == m

        eq_str = fmt_fn(m, b)
        ans = str(m)
        distractors = make_distractors(ans, [str(b), str(-m), str(abs(b))])
        ctx = (f"T2 read_slope (Easy). Equation: {eq_str}. "
               f"The slope is the coefficient of x: {m}. "
               f"Answer choices are numbers. Correct: {ans}. "
               f"Distractors: {b} (y-intercept confused for slope), "
               f"{-m} (sign error).")
        result = _l2v(1, params, ph, ans, distractors, None, None, "mcq", ctx, None)
        if validate_math_object(result):
            continue
        return result
    raise RuntimeError("read_slope d1: could not generate unique params")


def _d1_read_y_intercept(rng_obj, exclude_params, variant=None):
    """T2 Easy: given y = mx + b, identify the y-intercept b."""
    for _ in range(200):
        m = rng_obj.choice([i for i in range(-4, 5) if i != 0])
        b = rng_obj.choice([i for i in range(-6, 7) if i != 0 and i != m and i != -m])
        if variant == "pos_intercept" and b < 0:
            continue
        if variant == "neg_intercept" and b > 0:
            continue
        sub = variant or ("pos_intercept" if b > 0 else "neg_intercept")
        params = {"m": m, "b": b, "tpl": "read_y_intercept", "variant": sub}
        ph = param_hash(params)
        if ph in exclude_params:
            continue

        x_sym = sp.Symbol("x")
        assert sp.expand(m * x_sym + b).coeff(x_sym) == m

        eq_str = fmt_fn(m, b)
        ans = str(b)
        distractors = make_distractors(ans, [str(m), str(-b), str(0)])
        ctx = (f"T2 read_y_intercept (Easy). Equation: {eq_str}. "
               f"The y-intercept is the constant term: {b}. "
               f"Answer choices are numbers. Correct: {ans}. "
               f"Distractors: {m} (slope confused for intercept), "
               f"{-b} (sign error).")
        result = _l2v(1, params, ph, ans, distractors, None, None, "mcq", ctx, None)
        if validate_math_object(result):
            continue
        return result
    raise RuntimeError("read_y_intercept d1: could not generate unique params")


def _d1_match_graph_to_equation(rng_obj, exclude_params, variant=None):
    """T8 Easy: graph shown, identify y-intercept as ordered pair."""
    for _ in range(200):
        a = rng_obj.choice([2, 3, 4])
        b = rng_obj.choice([2, 3, 4])
        if a == b:
            continue
        if variant == "shallow_slope" and Rational(b, a) >= 1:
            continue
        if variant == "steep_slope" and Rational(b, a) < 1:
            continue
        sub = variant or ("shallow_slope" if Rational(b, a) < 1 else "steep_slope")

        params = {"a": a, "b": b, "tpl": "match_graph_to_equation", "variant": sub}
        ph = param_hash(params)
        if ph in exclude_params:
            continue

        slope_rat = Rational(-b, a)
        x_sym = sp.Symbol("x")
        line_expr = slope_rat * x_sym + b
        assert line_expr.subs(x_sym, 0) == b
        assert line_expr.subs(x_sym, a) == 0

        offset = rng_obj.choice([2, 3, 4])
        ans = f"(0, {b})"
        distractors = make_distractors(ans, [
            f"({a}, 0)",
            f"(0, {-b})",
            f"(0, {b + offset})",
        ])
        sn, sd = slope_rat.numerator, slope_rat.denominator
        fn_eq = fmt_fn(sn, b) if sd == 1 else f"y = {sn}/{sd}x + {b}"
        diag = {"type": "coordinate_plane", "function": fn_eq, "label": fn_eq, "hideLabel": True}
        ctx = (f"T8 match_graph_to_equation (Easy MCQ). "
               f"Graph shown: line through (0, {b}) and ({a}, 0). "
               f"Slope = {fmt_num(slope_rat)}. "
               f"The y-intercept is where the line crosses the y-axis: (0, {b}). "
               f"Answer choices are ordered pairs. Correct: {ans}. "
               f"Distractors: ({a}, 0) (x-intercept confused), "
               f"(0, {-b}) (sign error), (0, {b + offset}) (offset).")
        result = _l2v(1, params, ph, ans, distractors, None, None, "mcq", ctx, diag)
        if validate_math_object(result):
            continue
        return result
    raise RuntimeError("match_graph_to_equation d1: could not generate unique params")


def _d1_parallel_slope(rng_obj, exclude_params, variant=None):
    """T5 Easy: given y = mx + b, which equation is parallel?"""
    for _ in range(200):
        m = rng_obj.choice([-3, -2, -1, 1, 2, 3])
        b = rng_obj.choice([i for i in range(-6, 7) if i != 0])
        if variant == "neg_slope" and m > 0:
            continue
        if variant == "pos_slope" and m < 0:
            continue
        sub = variant or ("pos_slope" if m > 0 else "neg_slope")

        wrong_slope_pool = [i for i in range(-3, 4) if i != 0 and i != m and i != -m]
        if len(wrong_slope_pool) < 2:
            continue
        w1, w2 = rng_obj.sample(wrong_slope_pool, 2)
        c_ans = rng_obj.choice([i for i in range(-6, 7) if i != 0 and i != b])
        remaining_ints = [i for i in range(-6, 7) if i != 0 and i != c_ans]
        c1, c2, c3 = rng_obj.sample(remaining_ints, 3)

        params = {"m": m, "b": b, "tpl": "parallel_slope", "variant": sub}
        ph = param_hash(params)
        if ph in exclude_params:
            continue

        x_s = sp.Symbol("x")
        assert (m * x_s + b).coeff(x_s) == (m * x_s + c_ans).coeff(x_s) == m

        eq_str = fmt_fn(m, b)
        ans = fmt_fn(m, c_ans)
        distractors = make_distractors(ans, [
            fmt_fn(-m, c1),
            fmt_fn(w1, c2),
            fmt_fn(w2, c3),
        ])
        ctx = (f"T5 parallel_slope (Easy MCQ). "
               f"Given: {eq_str}. Slope = {m}. "
               f"Parallel lines have the same slope. Correct: {ans}. "
               f"Distractors: {fmt_fn(-m, c1)} (slope {-m}: negated), "
               f"{fmt_fn(w1, c2)} (slope {w1}: wrong), "
               f"{fmt_fn(w2, c3)} (slope {w2}: wrong). "
               f"CRITICAL — do NOT state the slope value in the question stem. "
               f"Ask only which equation represents a line parallel to the given line.")
        result = _l2v(1, params, ph, ans, distractors, None, None, "mcq", ctx, None)
        if validate_math_object(result):
            continue
        return result
    raise RuntimeError("parallel_slope d1: could not generate unique params")


def _d1_parallel_from_standard_form(rng_obj, exclude_params, variant=None):
    """T5 Easy: Ax + By = C with integer slope.

    identify_equation   — Which y=mx+b IS parallel to Ax+By=C?
                          (find the equation that shares the slope)
    identify_not_parallel — Which y=mx+b is NOT parallel to Ax+By=C?
                          (3 choices share the slope; 1 has a different slope — find the odd one out)
    """
    sub = variant or rng_obj.choice(["identify_equation", "identify_not_parallel"])
    for _ in range(200):
        B = rng_obj.choice([2, 3, 5])
        factor = rng_obj.choice([1, 2, 3, 4])
        A = B * factor
        C = rng_obj.randint(1, 20)
        slope = -factor

        params = {"A": A, "B": B, "C": C, "tpl": "parallel_from_standard_form", "variant": sub}
        ph = param_hash(params)
        if ph in exclude_params:
            continue

        x_s, y_s = sp.symbols("x y")
        assert sp.solve(sp.Eq(A * x_s + B * y_s, C), y_s)[0].coeff(x_s) == slope

        if sub == "identify_equation":
            # Correct: one equation with slope equal to line j
            # Distractors: negated slope, raw x-coeff as slope, reciprocal slope
            given_yint = Rational(C, B)
            c_ans = rng_obj.choice([i for i in range(-6, 7) if i != 0 and i != given_yint])
            remaining = [i for i in range(-6, 7) if i != 0 and i != c_ans]
            c1, c2, c3 = rng_obj.sample(remaining, 3)

            ans = fmt_fn(slope, c_ans)
            distractors = make_distractors(ans, [
                fmt_fn(-slope, c1),
                fmt_fn(A, c2),
                fmt_fn(Rational(1, factor) if factor != 1 else 2, c3),
            ])
            ctx = (f"T5 parallel_from_standard_form (Easy MCQ, identify_equation). "
                   f"Given: {A}x + {B}y = {C}. Slope = {slope}. "
                   f"Correct: {ans} (same slope {slope}). "
                   f"Distractor {fmt_fn(-slope, c1)}: negated slope. "
                   f"Distractor {fmt_fn(A, c2)}: used x-coeff directly. "
                   f"CRITICAL — do NOT state the slope value in the stem. "
                   f"Ask which equation represents a line parallel to the given line.")

        else:  # identify_not_parallel
            # Correct: one equation whose slope ≠ slope of j (the ODD ONE OUT)
            # Distractors: three equations that ARE parallel (same slope, different intercepts)
            # Student must find the exception — deeper parallel/non-parallel recognition
            non_par_slope = rng_obj.choice(
                [s for s in range(-4, 5) if s not in (0, slope)]
            )
            intercepts = rng_obj.sample([i for i in range(-6, 7) if i != 0], 4)
            c_nonpar, cp1, cp2, cp3 = intercepts

            ans = fmt_fn(non_par_slope, c_nonpar)
            d1  = fmt_fn(slope, cp1)   # parallel — wrong answer (trap)
            d2  = fmt_fn(slope, cp2)   # parallel — wrong answer (trap)
            d3  = fmt_fn(slope, cp3)   # parallel — wrong answer (trap)

            if len({ans, d1, d2, d3}) < 4:
                continue

            distractors = make_distractors(ans, [d1, d2, d3])
            ctx = (f"T5 parallel_from_standard_form (Easy MCQ, identify_not_parallel). "
                   f"Given: {A}x + {B}y = {C}. Slope = {slope}. "
                   f"Three of the four choices have slope {slope} (parallel). "
                   f"Correct: {ans} — slope = {non_par_slope} ≠ {slope}, NOT parallel. "
                   f"Distractors {d1}, {d2}, {d3} all have slope {slope} → parallel (wrong picks). "
                   f"CRITICAL — do NOT state slope values in the stem. "
                   f"Ask which equation does NOT represent a line parallel to the given line.")

        result = _l2v(1, params, ph, ans, distractors, None, None, "mcq", ctx, None)
        if validate_math_object(result):
            continue
        return result
    raise RuntimeError("parallel_from_standard_form d1: could not generate unique params")


# ── d2 template functions ─────────────────────────────────────────────────────

def _d2_slope_from_two_points(rng_obj, exclude_params, variant=None):
    """T2 Medium: slope relationships between two points.

    compute_slope         — Given two (x,y) pairs, find the slope (Δy/Δx).
    find_missing_coordinate — Given slope m, one complete point (x1,y1) and a second
                             x-coordinate x2, find the y-coordinate y2.
                             Inverse of slope calculation: apply slope to find a point.
    """
    sub = variant or rng_obj.choice(["compute_slope", "find_missing_coordinate"])
    for _ in range(200):
        if sub == "compute_slope":
            x1 = rng_obj.randint(-4, 4)
            x2 = rng_obj.randint(-4, 4)
            if x1 == x2:
                continue
            y1 = rng_obj.randint(-6, 6)
            y2 = rng_obj.randint(-6, 6)
            dy, dx = y2 - y1, x2 - x1
            slope = Rational(dy, dx)
            if slope == 0 or abs(slope) > 5:
                continue

            params = {"x1": x1, "y1": y1, "x2": x2, "y2": y2,
                      "tpl": "slope_from_two_points", "variant": sub}
            ph = param_hash(params)
            if ph in exclude_params:
                continue

            ans = fmt_num(slope)
            distractors = make_distractors(ans, [
                str(dy),
                fmt_num(Rational(dx, dy)) if dy != 0 else "0",
                fmt_num(-slope),
            ])
            ctx = (f"T2 slope_from_two_points (Medium MCQ, compute_slope). "
                   f"Points ({x1}, {y1}) and ({x2}, {y2}). "
                   f"slope = ({y2}−{y1}) / ({x2}−{x1}) = {dy}/{dx} = {ans}. "
                   f"Correct: {ans}.")
            result = _l2v(2, params, ph, ans, distractors, None, None, "mcq", ctx, None)

        else:  # find_missing_coordinate
            # Given: integer slope m, point (x1,y1), second x-coordinate x2 → find y2
            m = rng_obj.choice([i for i in range(-4, 5) if i != 0])
            x1 = rng_obj.randint(-3, 3)
            y1 = rng_obj.randint(-5, 5)
            dx = rng_obj.choice([i for i in range(-5, 6) if abs(i) >= 2])
            x2 = x1 + dx
            y2 = m * dx + y1
            if abs(y2) > 20:
                continue

            # Common wrong answers — distinct slope-formula errors
            wrong1 = m * x2 + y1          # used x2 directly instead of Δx
            wrong2 = m * dx - y1           # sign error on y1
            wrong3 = -m * dx + y1          # slope sign error
            if len({y2, wrong1, wrong2, wrong3}) < 4:
                continue

            params = {"m": m, "x1": x1, "y1": y1, "x2": x2,
                      "tpl": "slope_from_two_points", "variant": sub}
            ph = param_hash(params)
            if ph in exclude_params:
                continue

            x_s = sp.Symbol("x")
            assert sp.expand(m * (x_s - x1) + y1).subs(x_s, x2) == y2

            ans = str(y2)
            distractors = make_distractors(
                ans, [str(wrong1), str(wrong2), str(wrong3)]
            )
            use_spr = rng_obj.random() < 0.30
            qt = "spr" if use_spr else "mcq"
            sm, sx = spr_bounds(ans) if use_spr else (None, None)
            if not use_spr:
                distractors = make_distractors(ans, [str(wrong1), str(wrong2), str(wrong3)])
            else:
                distractors = []
            exact_stem = (
                f"A line has a slope of {m} and passes through the point ({x1}, {y1}). "
                f"What is the y-coordinate of the point on the line "
                f"with x-coordinate {x2}?"
            )
            ctx = (f"T2 slope_from_two_points (Medium {'SPR' if use_spr else 'MCQ'}, "
                   f"find_missing_coordinate). "
                   f"Stem (set verbatim): '{exact_stem}'. "
                   f"y2 = {m}·({x2}−{x1}) + {y1} = {m}·{dx} + {y1} = {y2}. "
                   f"Correct: {ans}. "
                   f"Distractor {wrong1}: used x2={x2} directly instead of Δx={dx}. "
                   f"Distractor {wrong2}: sign error on y1. "
                   f"Distractor {wrong3}: slope sign flipped.")
            result = _l2v(2, params, ph, ans, distractors, sm, sx, qt, ctx, None)
            result["exactStem"] = exact_stem

        if validate_math_object(result):
            continue
        return result
    raise RuntimeError("slope_from_two_points d2: could not generate unique params")


def _d2_perpendicular_slope(rng_obj, exclude_params, variant=None):
    """T5 Medium: find slope of perpendicular line."""
    for _ in range(200):
        m_vals = [i for i in range(-6, 7) if i not in {0, 1, -1}]
        m = rng_obj.choice(m_vals)
        perp = Rational(-1, m)

        if variant == "large_m" and abs(m) < 4:
            continue
        if variant == "small_m" and abs(m) >= 4:
            continue
        sub = variant or ("large_m" if abs(m) >= 4 else "small_m")

        params = {"m": m, "tpl": "perpendicular_slope", "variant": sub}
        ph = param_hash(params)
        if ph in exclude_params:
            continue

        assert Rational(-1, m) == perp
        ans = fmt_num(perp)
        distractors = make_distractors(ans, [
            fmt_num(Rational(1, m)),
            fmt_num(-m),
            fmt_num(m),
        ])
        ctx = (f"T5 perpendicular_slope (Medium). "
               f"A line has slope {m}. Perpendicular slope = −1 ÷ {m} = {ans}. "
               f"Answer choices are fractions/numbers. Correct: {ans}.")
        result = _l2v(2, params, ph, ans, distractors, None, None, "mcq", ctx, None)
        if validate_math_object(result):
            continue
        return result
    raise RuntimeError("perpendicular_slope d2: could not generate unique params")


def _d2_slope_from_standard_form(rng_obj, exclude_params, variant=None):
    """T2 Medium: Ax + By = C → find slope −A/B."""
    for _ in range(200):
        A = rng_obj.choice([2, 3, 4, 5, 6])
        B = rng_obj.choice([2, 3, 4, 5])
        if A == B:
            continue
        C = rng_obj.randint(1, 20)
        slope = Rational(-A, B)

        if variant == "neg_frac" and (slope > 0 or slope.denominator == 1):
            continue
        if variant == "neg_large" and (slope > -2 or slope.denominator == 1):
            continue
        sub = variant or ("neg_large" if slope <= -2 else "neg_frac")

        params = {"A": A, "B": B, "C": C, "tpl": "slope_from_standard_form", "variant": sub}
        ph = param_hash(params)
        if ph in exclude_params:
            continue

        x_s, y_s = sp.symbols("x y")
        y_expr = sp.solve(sp.Eq(A * x_s + B * y_s, C), y_s)[0]
        assert y_expr.coeff(x_s) == slope

        ans = fmt_num(slope)
        distractors = make_distractors(ans, [
            fmt_num(Rational(A, B)),
            fmt_num(Rational(-B, A)),
            fmt_num(Rational(B, A)),
        ])
        ctx = (f"T2 slope_from_standard_form (Medium). "
               f"Equation: {A}x + {B}y = {C}. "
               f"Rewrite: y = (−{A}/{B})x + {C}/{B}. Slope = {ans}. "
               f"Answer choices are fractions. Correct: {ans}.")
        result = _l2v(2, params, ph, ans, distractors, None, None, "mcq", ctx, None)
        if validate_math_object(result):
            continue
        return result
    raise RuntimeError("slope_from_standard_form d2: could not generate unique params")


def _d2_find_y_intercept_std(rng_obj, exclude_params, variant=None):
    """T7 Medium: Ax + By = C → find y-intercept C/B."""
    for _ in range(200):
        A = rng_obj.choice([2, 3, 4, 5])
        B = rng_obj.choice([2, 3, 4, 5])
        if A == B:
            continue
        mult = rng_obj.randint(1, 8)
        C = B * mult
        y_int = mult

        if variant == "small_intercept" and y_int >= 5:
            continue
        if variant == "large_intercept" and y_int < 5:
            continue
        sub = variant or ("large_intercept" if y_int >= 5 else "small_intercept")

        params = {"A": A, "B": B, "C": C, "tpl": "find_y_intercept_std", "variant": sub}
        ph = param_hash(params)
        if ph in exclude_params:
            continue

        x_s, y_s = sp.symbols("x y")
        y_int_check = sp.solve(sp.Eq(A * x_s + B * y_s, C).subs(x_s, 0), y_s)[0]
        assert y_int_check == y_int

        ans = str(y_int)
        distractors = make_distractors(ans, [
            str(C),
            fmt_num(Rational(C, A)),
            str(-y_int),
        ])
        ctx = (f"T7 find_y_intercept_std (Medium). "
               f"Equation: {A}x + {B}y = {C}. "
               f"Set x = 0: {B}y = {C} → y = {y_int}. "
               f"y-intercept = {ans}. Answer choices are numbers. Correct: {ans}.")
        result = _l2v(2, params, ph, ans, distractors, None, None, "mcq", ctx, None)
        if validate_math_object(result):
            continue
        return result
    raise RuntimeError("find_y_intercept_std d2: could not generate unique params")


def _d2_match_graph_to_equation(rng_obj, exclude_params, variant=None):
    """T8 Medium: graph shown, identify equation in slope-intercept form."""
    for _ in range(200):
        m = rng_obj.choice([-3, -2, 2, 3])
        b = rng_obj.choice([i for i in range(-4, 5) if abs(i) >= 2])

        if variant == "neg_slope" and m > 0:
            continue
        if variant == "pos_slope" and m < 0:
            continue
        sub = variant or ("pos_slope" if m > 0 else "neg_slope")

        params = {"m": m, "b": b, "tpl": "match_graph_to_equation", "variant": sub}
        ph = param_hash(params)
        if ph in exclude_params:
            continue

        x_s = sp.Symbol("x")
        expr = m * x_s + b
        assert expr.coeff(x_s) == m
        assert expr.subs(x_s, 0) == b

        ans = fmt_fn(m, b)
        distractors = make_distractors(ans, [
            fmt_fn(-m, b),
            fmt_fn(m, -b),
            fmt_fn(-m, -b),
        ])
        fn_eq = ans
        diag = {"type": "coordinate_plane", "function": fn_eq, "label": fn_eq, "hideLabel": True}
        ctx = (f"T8 match_graph_to_equation (Medium MCQ). "
               f"Graph shown: {fn_eq}. Slope = {m}, y-intercept = {b}. "
               f"Correct: {ans}. "
               f"Distractors: {fmt_fn(-m, b)} (wrong slope sign), "
               f"{fmt_fn(m, -b)} (wrong intercept sign), "
               f"{fmt_fn(-m, -b)} (both signs wrong).")
        result = _l2v(2, params, ph, ans, distractors, None, None, "mcq", ctx, diag)
        if validate_math_object(result):
            continue
        return result
    raise RuntimeError("match_graph_to_equation d2: could not generate unique params")


def _d2_parallel_slope(rng_obj, exclude_params, variant=None):
    """T5 Medium: given Ax + By = C, which standard-form equation is parallel?"""
    for _ in range(200):
        A = rng_obj.choice([2, 3, 4, 5])
        B = rng_obj.choice([2, 3, 4, 5])
        if A == B or 2 * A == B or A == 2 * B:
            continue
        C = rng_obj.randint(5, 20)
        D = rng_obj.choice([i for i in range(5, 21) if i != C])
        slope = Rational(-A, B)

        if variant == "proper_frac" and abs(slope) >= 1:
            continue
        if variant == "improper_frac" and abs(slope) < 1:
            continue
        sub = variant or ("proper_frac" if abs(slope) < 1 else "improper_frac")

        params = {"A": A, "B": B, "C": C, "D": D, "tpl": "parallel_slope", "variant": sub}
        ph = param_hash(params)
        if ph in exclude_params:
            continue

        x_s, y_s = sp.symbols("x y")
        s_given = sp.solve(sp.Eq(A * x_s + B * y_s, C), y_s)[0].coeff(x_s)
        s_ans   = sp.solve(sp.Eq(A * x_s + B * y_s, D), y_s)[0].coeff(x_s)
        assert s_given == s_ans == Rational(-A, B)

        ans = f"{A}x + {B}y = {D}"
        d1_str = f"{B}x + {A}y = {D}"
        d2_str = f"{A}x + {2 * B}y = {D}"
        d3_str = f"{2 * A}x + {B}y = {D}"
        distractors = make_distractors(ans, [d1_str, d2_str, d3_str])
        ctx = (f"T5 parallel_slope (Medium MCQ). "
               f"Given: {A}x + {B}y = {C}. Slope = -{A}/{B}. "
               f"A parallel line must have the same slope -{A}/{B}. "
               f"Correct: {ans} (slope -{A}/{B} ✓). "
               f"Distractor {d1_str}: slope -{B}/{A} ✗ (A,B swapped). "
               f"Distractor {d2_str}: slope -{A}/{2 * B} ✗ (B doubled). "
               f"Distractor {d3_str}: slope -{2 * A}/{B} ✗ (A doubled). "
               f"CRITICAL — do NOT state the slope in the question stem. "
               f"Ask which equation has a graph that is parallel to the given line.")
        result = _l2v(2, params, ph, ans, distractors, None, None, "mcq", ctx, None)
        if validate_math_object(result):
            continue
        return result
    raise RuntimeError("parallel_slope d2: could not generate unique params")


def _d2_parallel_from_standard_form(rng_obj, exclude_params, variant=None):
    """T5 Medium: Ax + By = C with fractional slope.

    identify_parallel      — Which y=mx+b is parallel to Ax+By=C?  (slope = -A/B)
    identify_perpendicular — Which y=mx+b is perpendicular to Ax+By=C?  (slope = B/A)
                             Tests the negative-reciprocal relationship; the parallel
                             equation is a deliberate strong distractor.
    """
    sub = variant or rng_obj.choice(["identify_parallel", "identify_perpendicular"])
    for _ in range(200):
        A = rng_obj.choice([2, 3, 4, 5])
        B = rng_obj.choice([2, 3, 4, 5])
        if A == B or A % B == 0 or B % A == 0:
            continue
        C = rng_obj.randint(1, 20)
        par_slope  = Rational(-A, B)   # parallel slope
        perp_slope = Rational(B, A)    # perpendicular slope (negative reciprocal)

        params = {"A": A, "B": B, "C": C, "tpl": "parallel_from_standard_form", "variant": sub}
        ph = param_hash(params)
        if ph in exclude_params:
            continue

        x_s, y_s = sp.symbols("x y")
        assert sp.solve(sp.Eq(A * x_s + B * y_s, C), y_s)[0].coeff(x_s) == par_slope

        c_ans = rng_obj.choice([i for i in range(-6, 7) if i != 0])
        remaining = [i for i in range(-6, 7) if i != 0 and i != c_ans]
        c1, c2, c3 = rng_obj.sample(remaining, 3)

        if sub == "identify_parallel":
            ans = _si(par_slope, c_ans)
            distractors = make_distractors(ans, [
                _si(Rational(A, B), c1),    # dropped negative sign
                _si(perp_slope, c2),        # perpendicular (common confusion)
                _si(Rational(B, A) * -1, c3),  # -B/A: negated perpendicular
            ])
            ctx = (f"T5 parallel_from_standard_form (Medium MCQ, identify_parallel). "
                   f"Given: {A}x + {B}y = {C}. Slope = -{A}/{B}. "
                   f"Correct: {ans} (same slope -{A}/{B}). "
                   f"Distractor {_si(Rational(A, B), c1)}: dropped negative sign. "
                   f"Distractor {_si(perp_slope, c2)}: perpendicular slope {B}/{A} (strong trap). "
                   f"CRITICAL — do NOT state the slope value in the stem. "
                   f"Ask which equation represents a line parallel to the given line.")
        else:  # identify_perpendicular
            ans = _si(perp_slope, c_ans)
            distractors = make_distractors(ans, [
                _si(par_slope, c1),          # parallel slope (strongest trap)
                _si(-perp_slope, c2),        # negated perpendicular (sign error)
                _si(Rational(A, B), c3),     # dropped both negatives
            ])
            ctx = (f"T5 parallel_from_standard_form (Medium MCQ, identify_perpendicular). "
                   f"Given: {A}x + {B}y = {C}. Slope of j = -{A}/{B}. "
                   f"Perpendicular slope = negative reciprocal = {B}/{A}. "
                   f"Correct: {ans}. "
                   f"Distractor {_si(par_slope, c1)}: parallel slope (strongest trap). "
                   f"Distractor {_si(-perp_slope, c2)}: sign error on perpendicular. "
                   f"Distractor {_si(Rational(A, B), c3)}: dropped both signs. "
                   f"CRITICAL — do NOT state the slope value in the stem. "
                   f"Ask which equation represents a line perpendicular to the given line.")

        result = _l2v(2, params, ph, ans, distractors, None, None, "mcq", ctx, None)
        if validate_math_object(result):
            continue
        return result
    raise RuntimeError("parallel_from_standard_form d2: could not generate unique params")


# ── d3 template functions ─────────────────────────────────────────────────────

def _d3_function_shift(rng_obj, exclude_params, variant=None):
    """T9A Hard: graph of y = f(x)+k shown; identify f(x)."""
    for _ in range(200):
        m = rng_obj.choice([-3, -2, -1, 1, 2, 3])
        b = rng_obj.choice([i for i in range(-12, 13) if i != 0])
        k = rng_obj.choice([i for i in range(-12, 15) if i != 0])
        visible_b = b + k
        if abs(visible_b) < 2 or abs(visible_b) > 4:
            continue
        if len({b, visible_b, visible_b + k}) < 3:
            continue
        if b == visible_b or b == visible_b + k:
            continue

        if variant == "shift_down" and k >= 0:
            continue
        if variant == "shift_up" and k < 0:
            continue
        sub = variant or ("shift_down" if k < 0 else "shift_up")

        params = {"m": m, "b": b, "k": k, "tpl": "function_shift", "variant": sub}
        ph = param_hash(params)
        if ph in exclude_params:
            continue

        assert sp.Integer(visible_b) - sp.Integer(k) == b

        ans = fmt_fx(m, b)
        distractors = make_distractors(ans, [
            fmt_fx(m, visible_b),
            fmt_fx(m, visible_b + k),
            fmt_fx(-m, b),
        ])
        k_label = f"+ {k}" if k >= 0 else f"− {abs(k)}"
        fn_label = f"y = f(x) {k_label}"
        m_str = "" if m == 1 else ("-" if m == -1 else str(m))
        if visible_b == 0:
            fn_eq = f"y = {m_str}x"
        elif visible_b > 0:
            fn_eq = f"y = {m_str}x + {visible_b}"
        else:
            fn_eq = f"y = {m_str}x - {abs(visible_b)}"

        ctx = (f"T9A function_shift (Hard MCQ). "
               f"Graph shown: {fn_label} — slope {m}, y-intercept {visible_b}. "
               f"f(x) = (graphed line) − ({k}) → y-intercept = {visible_b} − ({k}) = {b}. "
               f"Correct: {ans}. "
               f"Ask: 'The graph of {fn_label} is shown. Which equation defines f?' "
               f"ALL choices MUST use f(x) = ... format (never y = ...). "
               f"CRITICAL — do NOT state the slope or y-intercept in the question stem. "
               f"The stem must only say the graph is shown and ask which equation defines f. "
               f"The student must read slope and intercept from the graph — do not hand them those values in text.")
        diag = {"type": "coordinate_plane", "function": fn_eq, "label": fn_label, "hideLabel": False}
        result = _l2v(3, params, ph, ans, distractors, None, None, "mcq", ctx, diag)
        if validate_math_object(result):
            continue
        return result
    raise RuntimeError("function_shift d3: could not generate unique params")


def _d3_translate_intercept(rng_obj, exclude_params, variant=None):
    """T9B Hard: Ax - By = C translated down k; find x-intercept (SPR)."""
    for _ in range(200):
        A = rng_obj.randint(2, 12)
        B = rng_obj.randint(2, 12)
        if A == B:
            continue
        k = rng_obj.randint(2, 6)
        mult = rng_obj.randint(1, 6)
        rem = rng_obj.randint(1, A - 1) if A > 1 else 1
        C = A * mult + rem

        C_new = C + B * k
        x_int = Rational(C_new, A)
        x_s, y_s = sp.symbols("x y")
        x_int_check = sp.solve(sp.Eq(A * x_s - B * y_s, C_new).subs(y_s, 0), x_s)[0]
        assert x_int_check == x_int

        if x_int == int(x_int):
            continue

        if variant == "small_k" and k >= 4:
            continue
        if variant == "large_k" and k < 4:
            continue
        sub = variant or ("small_k" if k < 4 else "large_k")

        ans = fmt_num(x_int)
        sm, sx = spr_bounds(ans)

        params = {"A": A, "B": B, "C": C, "k": k, "tpl": "translate_intercept", "variant": sub}
        ph = param_hash(params)
        if ph in exclude_params:
            continue

        exact_stem = (f"The graph of {A}x - {B}y = {C} is translated down "
                      f"{k} units in the xy-plane. What is the x-coordinate "
                      f"of the x-intercept of the resulting graph?")
        ctx = (f"T9B translate_intercept (Hard SPR). "
               f"Derivation: translate {A}x - {B}y = {C} down {k} units → "
               f"replace y with (y+{k}) → {A}x - {B}y = {C_new} → "
               f"x-intercept: x = {C_new}/{A} = {ans}. "
               f"The questionStem is set by exactStem — do not rewrite it.")
        result = _l2v(3, params, ph, ans, [], sm, sx, "spr", ctx, None)
        result["exactStem"] = exact_stem
        if validate_math_object(result):
            continue
        return result
    raise RuntimeError("translate_intercept d3: could not generate unique params")


def _d3_slope_complex_expr(rng_obj, exclude_params, variant=None):
    """T2 Hard: find slope from a composed linear expression.

    single_fraction    — g(x) = (1/q)(ax + b) + cx
                         Distribute one fraction, combine x-terms.
    two_fraction_terms — g(x) = (Ax + B)/p + (Cx + D)/r
                         Simplify each fraction separately, then add x-coefficients.
    """
    sub = variant or rng_obj.choice(["single_fraction", "two_fraction_terms"])
    x_sym = sp.Symbol("x")

    for _ in range(200):
        if sub == "single_fraction":
            q = rng_obj.choice([2, 3, 4])
            factor_a = rng_obj.randint(2, 6)
            a = q * factor_a
            b_inner = rng_obj.choice([q * i for i in range(1, 5)])
            c = rng_obj.randint(2, 6)
            slope = factor_a + c

            if len({slope, factor_a, a, a + c}) < 4:
                continue

            params = {"q": q, "a": a, "b_inner": b_inner, "c": c,
                      "tpl": "slope_complex_expr", "variant": sub}
            ph = param_hash(params)
            if ph in exclude_params:
                continue

            expr = sp.Rational(1, q) * (a * x_sym + b_inner) + c * x_sym
            assert sp.expand(expr).coeff(x_sym) == slope

            ans = str(slope)
            distractors = make_distractors(ans, [str(factor_a), str(a), str(a + c)])
            ctx = (f"T2 slope_complex_expr (Hard MCQ, single_fraction). "
                   f"g(x) = (1/{q})({a}x + {b_inner}) + {c}x. "
                   f"Distribute: (1/{q})·{a}x = {factor_a}x; constant = {b_inner//q}. "
                   f"Combine: ({factor_a} + {c})x + {b_inner//q} = {slope}x + {b_inner//q}. "
                   f"Slope = {ans}. Correct: {ans}. "
                   f"Distractor {factor_a}: only first term's x-coeff, ignored +{c}x. "
                   f"Distractor {a}: used raw numerator {a} without dividing by {q}. "
                   f"Distractor {a + c}: added raw {a} and {c} without simplifying fraction.")

        else:  # two_fraction_terms
            # g(x) = (Ax + B)/p + (Cx + D)/r
            # slope = A/p + C/r = fa + fc  (both integer by construction)
            p, r = rng_obj.sample([2, 3, 4], 2)   # distinct denominators
            fa = rng_obj.randint(2, 5)
            fc = rng_obj.randint(2, 5)
            if fa == fc:
                continue
            A = p * fa          # A/p = fa (integer)
            C = r * fc          # C/r = fc (integer)
            B = p * rng_obj.randint(1, 4)
            D = r * rng_obj.randint(1, 4)
            slope = fa + fc

            # guard: slope distinct from all natural wrong answers;
            # also skip when both numerators are equal (visually confusing)
            if len({slope, fa, fc, A, C, A + C}) < 5:
                continue
            if A == C:
                continue

            params = {"p": p, "r": r, "A": A, "B": B, "C": C, "D": D,
                      "tpl": "slope_complex_expr", "variant": sub}
            ph = param_hash(params)
            if ph in exclude_params:
                continue

            expr = sp.Rational(A, p) * x_sym + sp.Rational(B, p) \
                 + sp.Rational(C, r) * x_sym + sp.Rational(D, r)
            assert sp.expand(expr).coeff(x_sym) == slope

            ans = str(slope)
            distractors = make_distractors(ans, [
                str(fa),          # only simplified first term's slope
                str(A + C),       # added raw numerators without dividing
                str(A),           # used first numerator directly
            ])
            ctx = (f"T2 slope_complex_expr (Hard MCQ, two_fraction_terms). "
                   f"g(x) = ({A}x + {B})/{p} + ({C}x + {D})/{r}. "
                   f"Simplify first term: {A}x/{p} = {fa}x; constant {B}/{p} = {B//p}. "
                   f"Simplify second term: {C}x/{r} = {fc}x; constant {D}/{r} = {D//r}. "
                   f"Combine x-terms: ({fa} + {fc})x = {slope}x. "
                   f"Slope = {ans}. Correct: {ans}. "
                   f"Distractor {fa}: simplified only first fraction's x-term, missed second. "
                   f"Distractor {A + C}: added raw numerators {A}+{C} without dividing. "
                   f"Distractor {A}: used first numerator {A} directly without dividing by {p}.")

        result = _l2v(3, params, ph, ans, distractors, None, None, "mcq", ctx, None)
        if validate_math_object(result):
            continue
        return result
    raise RuntimeError("slope_complex_expr d3: could not generate unique params")


def _d3_match_graph_to_equation(rng_obj, exclude_params, variant=None):
    """T8 Hard: line through two given intercepts; which standard-form eq has R > 0?"""
    for _ in range(200):
        a = rng_obj.choice([2, 3, 4, 5])
        b = rng_obj.choice([2, 3, 4, 5])
        if a == b:
            continue
        k = rng_obj.choice([2, 3, 4, 5])
        FIXED = k * b
        R_val = k * a
        C = k * a * b
        if FIXED == R_val:
            continue

        if variant == "small_intercepts" and (a >= 4 or b >= 4):
            continue
        if variant == "large_intercepts" and (a < 4 and b < 4):
            continue
        sub = variant or ("large_intercepts" if (a >= 4 or b >= 4) else "small_intercepts")

        params = {"a": a, "b": b, "k": k, "tpl": "match_graph_to_equation", "variant": sub}
        ph = param_hash(params)
        if ph in exclude_params:
            continue

        x_s, y_s = sp.symbols("x y")
        lhs = FIXED * x_s + R_val * y_s
        assert lhs.subs(x_s, a).subs(y_s, 0) == C
        assert lhs.subs(x_s, 0).subs(y_s, b) == C

        ans = f"{FIXED}x + Ry = {C}"
        distractors = make_distractors(ans, [
            f"Rx + {FIXED}y = {C}",
            f"Rx - {FIXED}y = {C}",
            f"{FIXED}x - Ry = {C}",
        ])
        slope_rat = Rational(-b, a)
        sn, sd = slope_rat.numerator, slope_rat.denominator
        fn_eq = fmt_fn(sn, b) if sd == 1 else f"y = {sn}/{sd}x + {b}"
        diag = {"type": "coordinate_plane", "function": fn_eq, "label": fn_eq, "hideLabel": True}
        exact_stem = (
            f"The graph of a line in the xy-plane passes through the point "
            f"(0, {b}) and the point ({a}, 0). Which of the following equations "
            f"represents this line, where R is a positive constant?"
        )
        ctx = (f"T8 match_graph_to_equation (Hard MCQ). "
               f"Stem (set verbatim — do NOT rewrite): '{exact_stem}'. "
               f"Standard form: {FIXED}x + Ry = {C}. "
               f"Sub (0, {b}): R·{b} = {C} → R = {R_val} > 0. ✓ "
               f"Distractor 'Rx + {FIXED}y = {C}': "
               f"sub (0, {b}) → {FIXED}·{b} = {FIXED * b} ≠ {C}. ✗ "
               f"Distractor '{FIXED}x - Ry = {C}': "
               f"sub (0, {b}) → -R·{b} = {C} → R = {-C // b} < 0. ✗ "
               f"Correct: {ans}.")
        result = _l2v(3, params, ph, ans, distractors, None, None, "mcq", ctx, diag)
        result["exactStem"] = exact_stem
        if validate_math_object(result):
            continue
        return result
    raise RuntimeError("match_graph_to_equation d3: could not generate unique params")


def _d3_parallel_from_standard_form(rng_obj, exclude_params, variant=None):
    """T5 Hard: parallel lines in standard form.

    find_y_coeff         — Line k: Dx + ny = F; solve for the y-coefficient n.
                           30% SPR, 70% MCQ (random, not a separate variant).
    which_equation_parallel — Given line j, which of 4 full equations is parallel to it?
                           Tests slope-ratio recognition across complete equations.
    """
    sub = variant or rng_obj.choice(["find_y_coeff", "which_equation_parallel"])
    for _ in range(200):
        A = rng_obj.choice([2, 3, 4, 5, 6])
        B = rng_obj.choice([2, 3, 4, 5])
        if A == B:
            continue
        C = rng_obj.randint(3, 20)
        g = _math.gcd(A, B)
        x_s, y_s = sp.symbols("x y")

        if sub == "find_y_coeff":
            # Line j: Ax + By = C  (slope = -A/B)
            # Line k: Dx + ny = F  → -D/n = -A/B  ⟹  n = B·D/A
            F = rng_obj.randint(3, 20)
            step = A // g
            D = rng_obj.choice([step * i for i in range(1, 6)])
            n_ans = (B * D) // A
            if n_ans < 2 or n_ans == B or n_ans == D or n_ans == A:
                continue

            params = {"A": A, "B": B, "D": D, "C": C, "F": F,
                      "tpl": "parallel_from_standard_form", "variant": sub}
            ph = param_hash(params)
            if ph in exclude_params:
                continue

            slope1 = sp.solve(sp.Eq(A * x_s + B * y_s, C), y_s)[0].coeff(x_s)
            slope2 = sp.solve(sp.Eq(D * x_s + n_ans * y_s, F), y_s)[0].coeff(x_s)
            assert slope1 == slope2

            ans = str(n_ans)
            distractors = make_distractors(ans, [str(B), str(D), str(B + D)])
            exact_stem = (
                f"Line j is defined by {A}x + {B}y = {C} in the xy-plane. "
                f"Line k is defined by {D}x + ny = {F}, where n is a constant. "
                f"If line k is parallel to line j, what is the value of n?"
            )
            ctx = (f"T5 parallel_from_standard_form (Hard find_y_coeff). "
                   f"Stem (set verbatim — do NOT rewrite): '{exact_stem}'. "
                   f"Slope of line j: -{A}/{B}. "
                   f"Set slopes equal: -{D}/n = -{A}/{B} → n = {B}·{D}/{A} = {n_ans}. "
                   f"Correct: {ans}. "
                   f"Distractor {B}: y-coeff of line j used directly. "
                   f"Distractor {D}: x-coeff of line k used directly. "
                   f"Distractor {B + D}: added the two known coefficients.")
            use_spr = rng_obj.random() < 0.30
            if use_spr:
                sm, sx = spr_bounds(ans)
                result = _l2v(3, params, ph, ans, [], sm, sx, "spr", ctx, None)
            else:
                result = _l2v(3, params, ph, ans, distractors, None, None, "mcq", ctx, None)

        else:  # which_equation_parallel
            # Line j: Ax + By = C  (slope = -A/B)
            # Correct answer: (k·A)x + (k·B)y = R  where R ≠ k·C  (same slope, different intercept)
            # Distractors:
            #   d1: Bx + Ay = R1   — coefficients swapped → slope = -B/A  (perpendicular; A≠B guaranteed)
            #   d2: Ax − By = R2   — y-sign flipped → slope = A/B  (not −A/B since A>0, B>0)
            #   d3: (A+1)x + By = R3 — x-coeff shifted → slope = −(A+1)/B
            k = rng_obj.choice([2, 3])
            R_vals = rng_obj.sample(range(3, 25), 4)
            R_correct, R1, R2, R3 = R_vals
            if R_correct == k * C:   # would be the same line
                continue

            pA, pB = k * A, k * B
            ans = f"{pA}x + {pB}y = {R_correct}"
            d1  = f"{B}x + {A}y = {R1}"
            d2  = f"{A}x - {B}y = {R2}"
            d3  = f"{A + 1}x + {B}y = {R3}"

            if len({ans, d1, d2, d3}) < 4:
                continue

            # SymPy verify: correct has same slope, all distractors have different slope
            slope_j   = sp.solve(sp.Eq(A * x_s + B * y_s, C), y_s)[0].coeff(x_s)
            slope_ans = sp.solve(sp.Eq(pA * x_s + pB * y_s, R_correct), y_s)[0].coeff(x_s)
            slope_d1  = sp.solve(sp.Eq(B * x_s + A * y_s, R1), y_s)[0].coeff(x_s)
            slope_d2  = sp.solve(sp.Eq(A * x_s - B * y_s, R2), y_s)[0].coeff(x_s)
            slope_d3  = sp.solve(sp.Eq((A + 1) * x_s + B * y_s, R3), y_s)[0].coeff(x_s)
            if slope_ans != slope_j:
                continue
            if any(s == slope_j for s in (slope_d1, slope_d2, slope_d3)):
                continue

            params = {"A": A, "B": B, "C": C, "k": k, "R": R_correct,
                      "tpl": "parallel_from_standard_form", "variant": sub}
            ph = param_hash(params)
            if ph in exclude_params:
                continue

            distractors = make_distractors(ans, [d1, d2, d3])
            exact_stem = (
                f"Line j is defined by {A}x + {B}y = {C} in the xy-plane. "
                f"Which of the following equations represents a line parallel to line j?"
            )
            ctx = (f"T5 parallel_from_standard_form (Hard MCQ, which_equation_parallel). "
                   f"Stem (set verbatim — do NOT rewrite): '{exact_stem}'. "
                   f"Slope of line j: -{A}/{B}. "
                   f"Correct {ans}: slope = -{pA}/{pB} = -{A}/{B} ✓, intercept ≠ line j → parallel. "
                   f"Distractor {d1}: coefficients swapped → slope = -{B}/{A} ✗. "
                   f"Distractor {d2}: y-sign flipped → slope = {A}/{B} ✗. "
                   f"Distractor {d3}: x-coeff off by 1 → slope = -{A+1}/{B} ✗.")
            result = _l2v(3, params, ph, ans, distractors, None, None, "mcq", ctx, None)

        result["exactStem"] = exact_stem
        if validate_math_object(result):
            continue
        return result
    raise RuntimeError("parallel_from_standard_form d3: could not generate unique params")


# ── Scenario pools for word-problem and interpretation templates ──────────────

_L2V_WP_D1_SCENARIOS = [
    # (b_label, m_label, context_fmt, m_pool, b_pool)
    ("handling fee",    "per-item charge",
     "A delivery service charges a {b}-dollar handling fee plus {m} dollars per item.",
     [2, 3, 4, 5], [5, 8, 10, 12]),
    ("base charge",     "per-hour rate",
     "A repair shop charges a {b}-dollar base charge plus {m} dollars per hour.",
     [15, 20, 25], [30, 40, 50]),
    ("registration fee", "per-session cost",
     "A fitness center charges a {b}-dollar registration fee and {m} dollars per class.",
     [10, 15, 20], [20, 25, 30]),
    ("starting savings", "monthly deposit",
     "A student starts with {b} dollars in savings and deposits {m} dollars each month.",
     [25, 30, 40, 50], [50, 75, 100]),
    ("base fare",       "per-mile charge",
     "A rideshare service charges a {b}-dollar base fare plus {m} dollars per mile.",
     [2, 3, 4], [3, 4, 5, 6]),
]

_L2V_WP_D2_SCENARIOS = [
    # (b_label, m_label, context_fmt, m_pool, b_pool, x_label, y_label)
    ("setup fee", "monthly fee",
     "A software subscription costs {b} dollars to set up and {m} dollars per month.",
     [10, 15, 20], [25, 30, 40, 50], "months", "total cost in dollars"),
    ("activation fee", "per-gigabyte charge",
     "A data plan charges a {b}-dollar activation fee and {m} dollars per gigabyte.",
     [3, 4, 5], [10, 15, 20], "gigabytes used", "total charge in dollars"),
    ("deposit", "daily rate",
     "A car rental requires a {b}-dollar deposit plus {m} dollars per day.",
     [20, 25, 30], [50, 75, 100], "days rented", "total cost in dollars"),
    ("flat fee", "per-item charge",
     "An online store charges a {b}-dollar flat shipping fee plus {m} dollars per item.",
     [2, 3, 4, 5], [6, 8, 10], "items ordered", "total shipping cost in dollars"),
]

_L2V_INTERP_SCENARIOS = [
    # (x_sym, x_label, y_label, context_fmt, slope_interp, intercept_interp)
    ("n", "items sold", "total earnings in dollars",
     "n = number of items sold and E = total earnings in dollars. E = {m}n + {b}.",
     "the earnings, in dollars, per item sold",
     "the total earnings, in dollars, when no items are sold"),
    ("h", "hours worked", "total pay in dollars",
     "h = hours worked and C = total pay in dollars. C = {m}h + {b}.",
     "the pay, in dollars, for each hour worked",
     "the base pay, in dollars, before working any hours"),
    ("t", "weeks elapsed", "total savings in dollars",
     "t = number of weeks and W = total savings in dollars. W = {m}t + {b}.",
     "the amount added to savings, in dollars, each week",
     "the initial savings, in dollars, before any weeks have elapsed"),
    ("d", "miles driven", "total fuel cost in dollars",
     "d = miles driven and F = total fuel cost in dollars. F = {m}d + {b}.",
     "the fuel cost, in dollars, per mile driven",
     "the fixed cost, in dollars, regardless of miles driven"),
    ("x", "sessions attended", "total program cost in dollars",
     "x = sessions attended and y = total program cost in dollars. y = {m}x + {b}.",
     "the cost, in dollars, per session attended",
     "the enrollment fee, in dollars, before attending any sessions"),
]


# ── New d1 template functions ─────────────────────────────────────────────────

def _d1_word_problem_setup(rng_obj, exclude_params, variant=None):
    """T1 Easy: real-world y = mx + b model; given one variable find the other (SPR/MCQ)."""
    sub = variant or rng_obj.choice(["find_y", "find_x"])
    for _ in range(200):
        sc = rng_obj.choice(_L2V_WP_D1_SCENARIOS)
        b_label, m_label, ctx_fmt, m_pool, b_pool = sc
        m = rng_obj.choice(m_pool)
        b = rng_obj.choice(b_pool)
        xv = rng_obj.randint(3, 10)
        yv = m * xv + b
        assert yv > 0

        if sub == "find_y":
            params = {"m": m, "b": b, "xv": xv, "tpl": "word_problem_setup", "variant": sub}
            ans = str(yv)
            wrong = str(xv)
        else:  # find_x
            params = {"m": m, "b": b, "yv": yv, "tpl": "word_problem_setup", "variant": sub}
            ans = str(xv)
            wrong = str(yv)

        ph = param_hash(params)
        if ph in exclude_params:
            continue

        assert m * xv + b == yv

        use_spr = rng_obj.random() < 0.35
        qt = "spr" if use_spr else "mcq"
        sm, sx = spr_bounds(ans) if use_spr else (None, None)
        distractors = make_distractors(ans, [str(m), str(b), wrong]) if not use_spr else []

        ctx_desc = ctx_fmt.format(m=m, b=b)
        _wp_banned = ("BANNED WORDS in stem: 'slope', 'y-intercept', 'equation', "
                      "'linear', 'line', 'model', 'function', 'graph'.")
        if sub == "find_y":
            ctx = (f"T1 word_problem_setup (Easy {'SPR' if use_spr else 'MCQ'}). "
                   f"USE THIS PROSE IN THE STEM: {ctx_desc} "
                   f"INTERNAL MATH ONLY (never put in stem): rate={m}, fixed={b}; "
                   f"answer = {m}×{xv} + {b} = {yv}. "
                   f"STEM must: use the scenario prose, state there are {xv} units, "
                   f"and ask for the total. {_wp_banned} "
                   f"CRITICAL: do not state the answer ({yv}) in the stem.")
        else:
            ctx = (f"T1 word_problem_setup (Easy {'SPR' if use_spr else 'MCQ'}). "
                   f"USE THIS PROSE IN THE STEM: {ctx_desc} "
                   f"INTERNAL MATH ONLY (never put in stem): rate={m}, fixed={b}; "
                   f"solve {m}x+{b}={yv} → x={xv}. "
                   f"STEM must: use the scenario prose, state the total is {yv}, "
                   f"and ask how many units. {_wp_banned} "
                   f"CRITICAL: do not state the answer ({xv}) in the stem.")

        result = _l2v(1, params, ph, ans, distractors, sm, sx, qt, ctx, None)
        if validate_math_object(result):
            continue
        return result
    raise RuntimeError("word_problem_setup d1: could not generate unique params")


def _d1_interpret_slope_in_context(rng_obj, exclude_params, variant=None):
    """T4 Easy: given y = mx + b with real context, what does m represent?"""
    for _ in range(200):
        sc_idx = rng_obj.randint(0, len(_L2V_INTERP_SCENARIOS) - 1)
        sc = _L2V_INTERP_SCENARIOS[sc_idx]
        x_sym, x_label, y_label, ctx_fmt, slope_correct, intercept_wrong = sc

        if variant == "rate_per_unit" and x_label not in ("items sold", "hours worked", "sessions attended"):
            continue
        if variant == "cost_per_item" and x_label not in ("miles driven", "items sold"):
            continue
        sub = variant or ("rate_per_unit" if x_label in ("items sold", "hours worked", "sessions attended") else "cost_per_item")

        m = rng_obj.choice([2, 3, 4, 5, 8, 10, 12, 15])
        b = rng_obj.choice([10, 15, 20, 25, 30, 40, 50])
        if m == b:
            continue

        params = {"m": m, "b": b, "sc_idx": sc_idx, "tpl": "interpret_slope_in_context", "variant": sub}
        ph = param_hash(params)
        if ph in exclude_params:
            continue

        ctx_desc = ctx_fmt.format(m=m, b=b)
        ans = slope_correct
        d1 = intercept_wrong
        d2 = f"the total {y_label} after {m} {x_label}"
        d3 = f"the number of {x_label} per unit of {y_label}"
        if len({ans, d1, d2, d3}) < 4:
            continue

        distractors = make_distractors(ans, [d1, d2, d3])
        ctx = (f"T4 interpret_slope_in_context (Easy MCQ). "
               f"Context: {ctx_desc} "
               f"Question: which best describes what {m} represents in this context? "
               f"Correct: '{ans}'. "
               f"Distractor (intercept confusion): '{d1}'. "
               f"Distractor (function value confusion): '{d2}'. "
               f"Distractor (inverted rate): '{d3}'. "
               f"Do NOT include the equation in the stem — describe the context in words only. "
               f"Present all 4 choices verbatim as answer options.")

        result = _l2v(1, params, ph, ans, distractors, None, None, "mcq", ctx, None)
        if validate_math_object(result):
            continue
        return result
    raise RuntimeError("interpret_slope_in_context d1: could not generate unique params")


def _d1_interpret_intercept_in_context(rng_obj, exclude_params, variant=None):
    """T4 Easy: given y = mx + b with real context, what does b represent?"""
    for _ in range(200):
        sc_idx = rng_obj.randint(0, len(_L2V_INTERP_SCENARIOS) - 1)
        sc = _L2V_INTERP_SCENARIOS[sc_idx]
        x_sym, x_label, y_label, ctx_fmt, slope_wrong, intercept_correct = sc

        if variant == "initial_value" and x_label not in ("weeks elapsed", "sessions attended"):
            continue
        if variant == "fixed_fee" and x_label not in ("hours worked", "miles driven", "items sold"):
            continue
        sub = variant or ("initial_value" if x_label in ("weeks elapsed", "sessions attended") else "fixed_fee")

        m = rng_obj.choice([2, 3, 4, 5, 8, 10, 12, 15])
        b = rng_obj.choice([10, 15, 20, 25, 30, 40, 50])
        if m == b:
            continue

        params = {"m": m, "b": b, "sc_idx": sc_idx, "tpl": "interpret_intercept_in_context", "variant": sub}
        ph = param_hash(params)
        if ph in exclude_params:
            continue

        ctx_desc = ctx_fmt.format(m=m, b=b)
        ans = intercept_correct
        d1 = slope_wrong
        d2 = f"the total {y_label} when {x_sym} equals {m}"
        d3 = f"the maximum possible {y_label}"
        if len({ans, d1, d2, d3}) < 4:
            continue

        distractors = make_distractors(ans, [d1, d2, d3])
        ctx = (f"T4 interpret_intercept_in_context (Easy MCQ). "
               f"Context: {ctx_desc} "
               f"Question: which best describes what {b} represents in this context? "
               f"Correct: '{ans}'. "
               f"Distractor (slope confusion): '{d1}'. "
               f"Distractor (function value confusion): '{d2}'. "
               f"Distractor (maximum confusion): '{d3}'. "
               f"Do NOT include the equation in the stem — describe the context in words only. "
               f"Present all 4 choices verbatim as answer options.")

        result = _l2v(1, params, ph, ans, distractors, None, None, "mcq", ctx, None)
        if validate_math_object(result):
            continue
        return result
    raise RuntimeError("interpret_intercept_in_context d1: could not generate unique params")


def _d1_write_equation_slope_intercept(rng_obj, exclude_params, variant=None):
    """T6 Easy: given slope m and y-intercept b as values, which equation is correct?"""
    for _ in range(200):
        m = rng_obj.choice([i for i in range(-4, 5) if i not in (0, 1, -1)])
        b = rng_obj.choice([i for i in range(-6, 7) if i not in (0, m, -m)])

        if variant == "pos_slope" and m < 0:
            continue
        if variant == "neg_slope" and m > 0:
            continue
        sub = variant or ("pos_slope" if m > 0 else "neg_slope")

        params = {"m": m, "b": b, "tpl": "write_equation_slope_intercept", "variant": sub}
        ph = param_hash(params)
        if ph in exclude_params:
            continue

        x_s = sp.Symbol("x")
        assert sp.expand(m * x_s + b).coeff(x_s) == m
        assert sp.expand(m * x_s + b).subs(x_s, 0) == b

        ans = fmt_fn(m, b)
        d1 = fmt_fn(-m, b)     # wrong slope sign
        d2 = fmt_fn(m, -b)     # wrong intercept sign
        d3 = fmt_fn(b, m)      # slope and intercept swapped

        distractors = make_distractors(ans, [d1, d2, d3])
        m_word = f"positive {abs(m)}" if m > 0 else f"negative {abs(m)}"
        b_word = f"positive {abs(b)}" if b > 0 else f"negative {abs(b)}"

        ctx = (f"T6 write_equation_slope_intercept (Easy MCQ). "
               f"A line has slope {m} and y-intercept {b}. "
               f"Correct equation: {ans}. "
               f"Distractor {d1}: wrong slope sign (negated). "
               f"Distractor {d2}: wrong intercept sign (negated). "
               f"Distractor {d3}: slope and intercept values swapped. "
               f"The stem must state the slope as {m_word} and y-intercept as {b_word}. "
               f"CRITICAL: do NOT show the correct equation or its form in the stem.")

        result = _l2v(1, params, ph, ans, distractors, None, None, "mcq", ctx, None)
        if validate_math_object(result):
            continue
        return result
    raise RuntimeError("write_equation_slope_intercept d1: could not generate unique params")


def _d1_table_to_equation(rng_obj, exclude_params, variant=None):
    """T3 Easy: given 3-row (x, y) table with integer values, which equation matches?"""
    for _ in range(200):
        m = rng_obj.choice([i for i in range(-4, 5) if i != 0])
        b = rng_obj.choice([i for i in range(-5, 6)])

        if variant == "integer_slope" and m < 0:
            continue
        if variant == "integer_neg_slope" and m > 0:
            continue
        sub = variant or ("integer_slope" if m > 0 else "integer_neg_slope")

        x_vals = sorted(rng_obj.sample(range(-2, 8), 3))
        y_vals = [m * x + b for x in x_vals]

        params = {"m": m, "b": b, "tpl": "table_to_equation", "variant": sub}
        ph = param_hash(params)
        if ph in exclude_params:
            continue

        for xv, yv in zip(x_vals, y_vals):
            assert m * xv + b == yv

        ans = fmt_fn(m, b)
        b_delta = rng_obj.choice([i for i in range(-3, 4) if i != 0])
        b_wrong = b + b_delta
        # exclude 0, m, and -m so d2 can never collide with d3
        m_wrong = rng_obj.choice([i for i in range(-4, 5) if i not in (0, m, -m)])

        d1 = fmt_fn(m, b_wrong)     # same slope, wrong intercept
        d2 = fmt_fn(m_wrong, b)     # wrong slope, same intercept
        d3 = fmt_fn(-m, b)          # negated slope

        distractors = make_distractors(ans, [d1, d2, d3])
        table_rows = " | ".join([f"({xv}, {yv})" for xv, yv in zip(x_vals, y_vals)])

        ctx = (f"T3 table_to_equation (Easy MCQ). "
               f"Table rows: x={x_vals[0]},y={y_vals[0]}; "
               f"x={x_vals[1]},y={y_vals[1]}; x={x_vals[2]},y={y_vals[2]}. "
               f"Slope = ({y_vals[1]}-{y_vals[0]})/({x_vals[1]}-{x_vals[0]}) = {m}. "
               f"Intercept b = {y_vals[0]} - {m}×{x_vals[0]} = {b}. "
               f"Correct: {ans}. "
               f"Distractor {d1}: same slope, intercept off by {b_delta}. "
               f"Distractor {d2}: wrong slope {m_wrong}. "
               f"Distractor {d3}: slope sign wrong. "
               f"STEM FORMAT: Write a sentence that presents the three ordered pairs inline, "
               f"e.g. 'The table shows three (x, y) pairs: "
               f"({x_vals[0]}, {y_vals[0]}), ({x_vals[1]}, {y_vals[1]}), "
               f"and ({x_vals[2]}, {y_vals[2]}).' "
               f"Do NOT use markdown table syntax (pipes/dashes) — the renderer does not support it. "
               f"Ask which equation is satisfied by all values. "
               f"CRITICAL: do NOT reveal slope or intercept value in the stem.")

        result = _l2v(1, params, ph, ans, distractors, None, None, "mcq", ctx, None)
        if validate_math_object(result):
            continue
        return result
    raise RuntimeError("table_to_equation d1: could not generate unique params")


# ── New d2 template functions ─────────────────────────────────────────────────

def _d2_word_problem_rate_model(rng_obj, exclude_params, variant=None):
    """T1 Medium: setup + per-unit rate model; solve for quantity or total (SPR/MCQ)."""
    sub = variant or rng_obj.choice(["solve_quantity", "solve_cost"])
    for _ in range(200):
        sc = rng_obj.choice(_L2V_WP_D2_SCENARIOS)
        b_label, m_label, ctx_fmt, m_pool, b_pool, x_label, y_label = sc
        m = rng_obj.choice(m_pool)
        b = rng_obj.choice(b_pool)
        xv = rng_obj.randint(3, 15)
        yv = m * xv + b
        assert yv > 0

        x_s = sp.Symbol("x")
        assert sp.solve(sp.Eq(m * x_s + b, yv), x_s)[0] == xv

        ctx_desc = ctx_fmt.format(m=m, b=b)
        _wp_banned = ("BANNED WORDS in stem: 'slope', 'y-intercept', 'equation', "
                      "'linear', 'line', 'model', 'function', 'graph'.")

        if sub == "solve_quantity":
            params = {"m": m, "b": b, "yv": yv, "tpl": "word_problem_rate_model", "variant": sub}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(xv)
            use_spr = rng_obj.random() < 0.40
            qt = "spr" if use_spr else "mcq"
            sm, sx = spr_bounds(ans) if use_spr else (None, None)
            distractors = make_distractors(ans, [str(xv + 1), str(xv - 1), str(yv), str(b)]) if not use_spr else []
            ctx = (f"T1 word_problem_rate_model (Medium {'SPR' if use_spr else 'MCQ'}, solve_quantity). "
                   f"USE THIS PROSE IN THE STEM: {ctx_desc} "
                   f"INTERNAL MATH ONLY (never put in stem): rate={m}, fixed={b}; "
                   f"solve {m}x+{b}={yv} → x={xv}. "
                   f"STEM must: use the scenario prose, state the total is {yv} dollars, "
                   f"and ask how many {x_label}. {_wp_banned} "
                   f"CRITICAL: do not state the answer ({xv}) in the stem.")
        else:  # solve_cost
            params = {"m": m, "b": b, "xv": xv, "tpl": "word_problem_rate_model", "variant": sub}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(yv)
            use_spr = rng_obj.random() < 0.30
            qt = "spr" if use_spr else "mcq"
            sm, sx = spr_bounds(ans) if use_spr else (None, None)
            distractors = make_distractors(ans, [str(m * xv), str(yv + m), str(yv - b), str(b)]) if not use_spr else []
            ctx = (f"T1 word_problem_rate_model (Medium {'SPR' if use_spr else 'MCQ'}, solve_cost). "
                   f"USE THIS PROSE IN THE STEM: {ctx_desc} "
                   f"INTERNAL MATH ONLY (never put in stem): rate={m}, fixed={b}; "
                   f"answer = {m}×{xv}+{b} = {yv}. "
                   f"STEM must: use the scenario prose, state there are {xv} {x_label}, "
                   f"and ask for the {y_label}. {_wp_banned} "
                   f"CRITICAL: do not state the answer ({yv}) in the stem.")

        result = _l2v(2, params, ph, ans, distractors, sm, sx, qt, ctx, None)
        if validate_math_object(result):
            continue
        return result
    raise RuntimeError("word_problem_rate_model d2: could not generate unique params")


def _d2_write_equation_slope_point(rng_obj, exclude_params, variant=None):
    """T6 Medium: given slope m and point (x0, y0) not on y-axis, find slope-intercept eq."""
    for _ in range(200):
        m = rng_obj.choice([i for i in range(-4, 5) if i != 0])
        x0 = rng_obj.choice([i for i in range(-4, 5) if i != 0])
        b = rng_obj.choice([i for i in range(-6, 7)])
        y0 = m * x0 + b

        if variant == "pos_slope" and m < 0:
            continue
        if variant == "neg_slope" and m > 0:
            continue
        sub = variant or ("pos_slope" if m > 0 else "neg_slope")

        params = {"m": m, "x0": x0, "y0": y0, "tpl": "write_equation_slope_point", "variant": sub}
        ph = param_hash(params)
        if ph in exclude_params:
            continue

        assert y0 - m * x0 == b

        ans = fmt_fn(m, b)
        d1 = fmt_fn(m, y0)              # used y0 directly as intercept
        d2 = fmt_fn(m, -(m * x0 - y0)) # sign error in b calculation
        d3 = fmt_fn(-m, b)              # negated slope

        distractors = make_distractors(ans, [d1, d2, d3])
        ctx = (f"T6 write_equation_slope_point (Medium MCQ). "
               f"Given: slope = {m}, passes through ({x0}, {y0}). "
               f"b = {y0} − {m}×{x0} = {y0} − ({m * x0}) = {b}. "
               f"Correct: {ans}. "
               f"Distractor {d1}: used y0 = {y0} directly as y-intercept (forgot to subtract {m}×{x0}). "
               f"Distractor {d3}: negated slope. "
               f"CRITICAL: do NOT state the y-intercept value in the stem. "
               f"Stem must give only slope = {m} and the point ({x0}, {y0}).")

        result = _l2v(2, params, ph, ans, distractors, None, None, "mcq", ctx, None)
        if validate_math_object(result):
            continue
        return result
    raise RuntimeError("write_equation_slope_point d2: could not generate unique params")


def _d2_write_equation_two_points(rng_obj, exclude_params, variant=None):
    """T6 Medium: given two (x, y) pairs, write the slope-intercept equation."""
    for _ in range(200):
        m = rng_obj.choice([i for i in range(-4, 5) if i != 0])
        b = rng_obj.choice([i for i in range(-6, 7)])
        x1 = rng_obj.randint(-4, 3)
        x2 = x1 + rng_obj.randint(2, 5)
        y1 = m * x1 + b
        y2 = m * x2 + b

        if variant == "pos_slope" and m < 0:
            continue
        if variant == "neg_slope" and m > 0:
            continue
        sub = variant or ("pos_slope" if m > 0 else "neg_slope")

        params = {"x1": x1, "y1": y1, "x2": x2, "y2": y2, "tpl": "write_equation_two_points", "variant": sub}
        ph = param_hash(params)
        if ph in exclude_params:
            continue

        assert Rational(y2 - y1, x2 - x1) == m
        assert y1 - m * x1 == b

        ans = fmt_fn(m, b)
        b_delta = rng_obj.choice([i for i in range(-3, 4) if i != 0])
        # exclude 0, m, and -m so d2 can never collide with d3
        m_wrong = rng_obj.choice([i for i in range(-4, 5) if i not in (0, m, -m)])

        d1 = fmt_fn(m, b + b_delta)     # correct slope, wrong intercept
        d2 = fmt_fn(m_wrong, b)         # wrong slope, correct intercept
        d3 = fmt_fn(-m, b)              # negated slope

        distractors = make_distractors(ans, [d1, d2, d3])
        ctx = (f"T6 write_equation_two_points (Medium MCQ). "
               f"Points: ({x1}, {y1}) and ({x2}, {y2}). "
               f"slope = ({y2}−{y1}) / ({x2}−{x1}) = {y2 - y1}/{x2 - x1} = {m}. "
               f"b = {y1} − {m}×{x1} = {y1 - m * x1} = {b}. "
               f"Correct: {ans}. "
               f"Distractor {d1}: slope correct, intercept off by {b_delta}. "
               f"Distractor {d2}: slope wrong ({m_wrong} instead of {m}). "
               f"Distractor {d3}: slope sign wrong. "
               f"CRITICAL: do NOT state slope or intercept in the stem. "
               f"Stem must give only the two coordinate pairs and ask for the equation.")

        result = _l2v(2, params, ph, ans, distractors, None, None, "mcq", ctx, None)
        if validate_math_object(result):
            continue
        return result
    raise RuntimeError("write_equation_two_points d2: could not generate unique params")


def _d2_find_x_intercept_standard_form(rng_obj, exclude_params, variant=None):
    """T7 Medium: Ax + By = C → find x-intercept (set y = 0, solve for x)."""
    for _ in range(200):
        A = rng_obj.choice([2, 3, 4, 5])
        B = rng_obj.choice([2, 3, 4, 5])
        if A == B:
            continue

        if variant == "integer_result":
            mult = rng_obj.randint(2, 8)
            C = A * mult
            x_int = Rational(C, A)
        elif variant == "frac_result":
            C = rng_obj.randint(3, 20)
            if C % A == 0:
                continue
            x_int = Rational(C, A)
        else:
            C = rng_obj.randint(3, 20)
            x_int = Rational(C, A)
        sub = variant or ("integer_result" if x_int.denominator == 1 else "frac_result")

        params = {"A": A, "B": B, "C": C, "tpl": "find_x_intercept_standard_form", "variant": sub}
        ph = param_hash(params)
        if ph in exclude_params:
            continue

        x_s, y_s = sp.symbols("x y")
        x_int_check = sp.solve(sp.Eq(A * x_s + B * y_s, C).subs(y_s, 0), x_s)[0]
        assert x_int_check == x_int

        ans = fmt_num(x_int)
        use_spr = rng_obj.random() < 0.40
        qt = "spr" if use_spr else "mcq"
        sm, sx = spr_bounds(ans) if use_spr else (None, None)
        distractors = make_distractors(ans, [
            fmt_num(Rational(C, B)),    # set x=0 instead (y-intercept error)
            fmt_num(Rational(-C, A)),   # sign error
            fmt_num(Rational(A, C)),    # inverted
        ]) if not use_spr else []

        ctx = (f"T7 find_x_intercept_standard_form (Medium {'SPR' if use_spr else 'MCQ'}). "
               f"Equation: {A}x + {B}y = {C}. "
               f"Set y = 0: {A}x = {C} → x = {C}/{A} = {ans}. "
               f"Correct: {ans}. "
               f"Distractor {fmt_num(Rational(C, B))}: set x=0 instead — finds y-intercept. "
               f"CRITICAL: do NOT say 'set y = 0' in the stem. "
               f"Ask only for the x-coordinate of the x-intercept of the graph.")

        result = _l2v(2, params, ph, ans, distractors, sm, sx, qt, ctx, None)
        if validate_math_object(result):
            continue
        return result
    raise RuntimeError("find_x_intercept_standard_form d2: could not generate unique params")


# ── New d3 template functions ─────────────────────────────────────────────────

def _d3_word_problem_hard(rng_obj, exclude_params, variant=None):
    """T1 Hard: complex real-world model; find unknown value (SPR) or identify equation (MCQ)."""
    _HARD_SCENARIOS = [
        # (prose_fmt, eq_hint_fmt, m_pool, b_pool, x_label, y_label, two_pt_fmt)
        # prose_fmt    → spr_value: Haiku uses this in the stem (no equation)
        # eq_hint_fmt  → kept for documentation only; NOT injected into ctx
        # two_pt_fmt   → mcq_equation: two data points, no m/b visible to student
        ("A concert venue earns {m} dollars per ticket sold plus a fixed sponsor fee of {b} dollars.",
         "R = {m}t + {b}",
         [15, 20, 25, 30], [500, 750, 1000], "tickets sold", "total revenue in dollars",
         "When {t1} tickets are sold, the total revenue is {y1} dollars. "
         "When {t2} tickets are sold, the total revenue is {y2} dollars."),
        ("A factory produces {m} units per hour and already has {b} units in stock.",
         "S = {m}h + {b}",
         [40, 50, 60, 80], [100, 150, 200], "hours of production", "total units in stock",
         "After {t1} hours of production, the factory has {y1} units in stock. "
         "After {t2} hours of production, it has {y2} units in stock."),
        ("A marathon runner adds {m} miles to their weekly training distance each week "
         "and currently runs {b} miles per week.",
         "D = {m}w + {b}",
         [2, 3, 4, 5], [10, 12, 15, 18], "weeks of training", "weekly mileage in miles",
         "After {t1} weeks of training, the runner's weekly mileage is {y1} miles. "
         "After {t2} weeks of training, it is {y2} miles."),
        ("A nature reserve starts with {b} trees and plants {m} new trees every year.",
         "T = {m}y + {b}",
         [30, 40, 50, 60], [200, 300, 400, 500], "years", "total number of trees",
         "After {t1} years, the reserve has {y1} trees. "
         "After {t2} years, it has {y2} trees."),
    ]
    sub = variant or rng_obj.choice(["spr_value", "mcq_equation"])
    for _ in range(200):
        sc = rng_obj.choice(_HARD_SCENARIOS)
        prose_fmt, _eq_hint_fmt, m_pool, b_pool, x_label, y_label, two_pt_fmt = sc
        m = rng_obj.choice(m_pool)
        b = rng_obj.choice(b_pool)

        if sub == "spr_value":
            xv = rng_obj.randint(5, 20)
            yv = m * xv + b
            x_s = sp.Symbol("x")
            assert sp.expand(m * x_s + b).subs(x_s, xv) == yv

            prose = prose_fmt.format(m=m, b=b)
            params = {"m": m, "b": b, "yv": yv, "tpl": "word_problem_hard", "variant": sub}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(xv)
            sm, sx = spr_bounds(ans)
            # No equation hint in ctx — the prose alone is enough, and injecting
            # "S = mh + b" was causing Haiku to generate algebra questions instead
            # of word problems (see SP-L2V-072).
            ctx = (f"T1 word_problem_hard (Hard SPR). "
                   f"USE THIS PROSE IN THE STEM: {prose} "
                   f"STEM must: describe the scenario in plain English, state that "
                   f"{y_label} has reached {yv}, and ask how many {x_label} are needed. "
                   f"Answer: {xv}. "
                   f"BANNED WORDS in stem: 'slope', 'y-intercept', 'x-intercept', "
                   f"'linear', 'equation', 'line y =', 'graph', 'function'. "
                   f"Do NOT write any equation or formula in the stem.")
            result = _l2v(3, params, ph, ans, [], sm, sx, "spr", ctx, None)

        else:  # mcq_equation
            # Two-point presentation: give (t1,y1) and (t2,y2); student derives m and b.
            # Do NOT use prose_fmt (it contains the exact m and b values, leaking the answer).
            t1 = rng_obj.choice([2, 3, 4])
            t2 = t1 + rng_obj.choice([2, 3, 4])
            y1 = m * t1 + b
            y2 = m * t2 + b

            params = {"m": m, "b": b, "t1": t1, "t2": t2,
                      "tpl": "word_problem_hard", "variant": sub}
            ph = param_hash(params)
            if ph in exclude_params:
                continue

            ans = fmt_fn(m, b)
            b2 = b + rng_obj.choice([m, -m, 2 * m])
            m2 = m + rng_obj.choice([5, 10, -5, 15])
            d1 = fmt_fn(m, b2)
            d2 = fmt_fn(m2, b)
            d3 = fmt_fn(m + m2, b)
            if len({ans, d1, d2, d3}) < 4:
                continue
            distractors = make_distractors(ans, [d1, d2, d3])

            two_pt_prose = two_pt_fmt.format(t1=t1, y1=y1, t2=t2, y2=y2)
            ctx = (f"T1 word_problem_hard (Hard MCQ). "
                   f"USE THIS PROSE IN THE STEM: {two_pt_prose} "
                   f"THEN define: let x = {x_label}, y = {y_label}. "
                   f"Ask which equation correctly models the relationship between x and y. "
                   f"INTERNAL MATH ONLY (never in stem): slope = {m}, intercept = {b}; "
                   f"correct equation = {ans}. "
                   f"CRITICAL — do NOT state the rate ({m}) or starting value ({b}) in the stem. "
                   f"Distractors: {d1} (wrong intercept), {d2} (wrong slope), "
                   f"{d3} (wrong both).")
            result = _l2v(3, params, ph, ans, distractors, None, None, "mcq", ctx, None)

        if validate_math_object(result):
            continue
        return result
    raise RuntimeError("word_problem_hard d3: could not generate unique params")


def _d3_table_to_equation_hard(rng_obj, exclude_params, variant=None):
    """T3 Hard: table with fractional slope → which equation matches all (x, y) pairs?"""
    for _ in range(200):
        if variant == "neg_frac_slope":
            num = rng_obj.choice([-1, -2, -3])
        else:  # frac_slope (positive)
            num = rng_obj.choice([1, 2, 3])
        den = rng_obj.choice([2, 3, 4])
        m = Rational(num, den)
        sn, sd = m.numerator, m.denominator
        sub = variant or ("neg_frac_slope" if num < 0 else "frac_slope")

        # Use x multiples of den so y-values remain integers
        b = rng_obj.choice([i for i in range(-4, 5)])
        x_bases = sorted(rng_obj.sample(range(1, 6), 3))
        x_vals = [xb * den for xb in x_bases]
        y_vals = [int(m * x + b) for x in x_vals]

        if any(m * xv + b != yv for xv, yv in zip(x_vals, y_vals)):
            continue

        params = {"sn": sn, "sd": sd, "b": b, "tpl": "table_to_equation_hard", "variant": sub}
        ph = param_hash(params)
        if ph in exclude_params:
            continue

        # Verify slope from first two table points
        slope_check = Rational(y_vals[1] - y_vals[0], x_vals[1] - x_vals[0])
        assert slope_check == m

        def _feq(n, d, ib):
            """Format y = n/d * x ± ib."""
            if ib > 0:
                return f"y = {n}/{d}x + {ib}"
            if ib < 0:
                return f"y = {n}/{d}x - {abs(ib)}"
            return f"y = {n}/{d}x"

        b_delta = rng_obj.choice([i for i in range(-3, 4) if i != 0])
        ans = _feq(sn, sd, b)
        d1 = _feq(sn, sd, b + b_delta)    # same slope, wrong intercept
        d2 = _feq(-sn, sd, b)             # negated slope numerator
        d3 = _feq(sd, abs(sn), b)         # inverted fraction (note: abs(sn) to keep positive denom)

        if len({ans, d1, d2, d3}) < 4:
            continue

        distractors = make_distractors(ans, [d1, d2, d3])
        ctx = (f"T3 table_to_equation_hard (Hard MCQ). "
               f"Table: x={x_vals[0]},y={y_vals[0]}; "
               f"x={x_vals[1]},y={y_vals[1]}; x={x_vals[2]},y={y_vals[2]}. "
               f"slope = ({y_vals[1]}-{y_vals[0]})/({x_vals[1]}-{x_vals[0]}) = {sn}/{sd}. "
               f"b = {y_vals[0]} - ({sn}/{sd})×{x_vals[0]} = {b}. "
               f"Correct: {ans}. "
               f"Distractor {d1}: correct slope, intercept off by {b_delta}. "
               f"Distractor {d2}: slope sign flipped. "
               f"Distractor {d3}: slope fraction inverted. "
               f"STEM FORMAT: Write a sentence that presents the three ordered pairs inline, "
               f"e.g. 'The table shows three (x, y) pairs: "
               f"({x_vals[0]}, {y_vals[0]}), ({x_vals[1]}, {y_vals[1]}), "
               f"and ({x_vals[2]}, {y_vals[2]}).' "
               f"Do NOT use markdown table syntax (pipes/dashes) — the renderer does not support it. "
               f"CRITICAL: do NOT reveal slope or intercept values in the stem.")

        result = _l2v(3, params, ph, ans, distractors, None, None, "mcq", ctx, None)
        if validate_math_object(result):
            continue
        return result
    raise RuntimeError("table_to_equation_hard d3: could not generate unique params")


# ── New templates: T2e / T3 / T4b / T5-full / T7c ────────────────────────────

# Term-interpretation strings for _d2_interpret_term_in_context
_L2V_TERM_INTERP = {
    "items sold":        "the total earnings, in dollars, from all items sold",
    "hours worked":      "the total pay, in dollars, for all hours worked",
    "weeks elapsed":     "the total amount added to savings, in dollars, over all weeks",
    "miles driven":      "the total fuel cost, in dollars, for all miles driven",
    "sessions attended": "the total program cost, in dollars, from all sessions attended",
}


def _d2_slope_from_table(rng_obj, exclude_params, variant=None):
    """T2e Medium: compute slope from two rows of an (x, y) table."""
    for _ in range(200):
        dx = rng_obj.choice([1, 2, 3, 4])
        dy = rng_obj.choice([i for i in range(-10, 11) if i != 0])
        slope_rat = Rational(dy, dx)
        sub = variant or ("integer_slope" if slope_rat.denominator == 1 else "frac_slope")
        if sub == "integer_slope" and slope_rat.denominator != 1:
            continue
        if sub == "frac_slope" and slope_rat.denominator == 1:
            continue

        x1 = rng_obj.choice(range(-4, 5))
        x2 = x1 + dx
        y1 = rng_obj.randint(-8, 8)
        y2 = y1 + dy
        assert Rational(y2 - y1, x2 - x1) == slope_rat

        params = {"x1": x1, "y1": y1, "x2": x2, "y2": y2,
                  "tpl": "slope_from_table", "variant": sub}
        ph = param_hash(params)
        if ph in exclude_params:
            continue

        ans      = fmt_num(slope_rat)
        d_recip  = fmt_num(Rational(dx, dy))
        d_neg    = fmt_num(-slope_rat)
        d_dy     = str(dy)
        if len({ans, d_recip, d_neg, d_dy}) < 4:
            continue

        distractors = make_distractors(ans, [d_recip, d_neg, d_dy])
        ctx = (f"T2e slope_from_table (Medium MCQ). "
               f"Table rows: x={x1},y={y1}; x={x2},y={y2}. "
               f"slope = ({y2}−{y1})/({x2}−{x1}) = {dy}/{dx} = {ans}. "
               f"Correct: {ans}. "
               f"Distractor {d_recip}: Δx/Δy reciprocal error. "
               f"Distractor {d_neg}: negated slope. "
               f"Distractor {d_dy}: used only Δy. "
               f"STEM FORMAT: Write a sentence that presents the two ordered pairs inline, "
               f"e.g. 'The table shows two (x, y) pairs: ({x1}, {y1}) and ({x2}, {y2}).' "
               f"Do NOT use markdown table syntax (pipes/dashes) — the renderer does not support it. "
               f"Ask for the slope of the line through these two points. "
               f"CRITICAL: do NOT reveal the slope value in the stem.")
        result = _l2v(2, params, ph, ans, distractors, None, None, "mcq", ctx)
        if validate_math_object(result):
            continue
        return result
    raise RuntimeError("slope_from_table d2: could not generate unique params")


def _d2_match_equation_to_table(rng_obj, exclude_params, variant=None):
    """T3 Medium: given y = mx + b, which set of (x, y) pairs satisfies it?"""
    for _ in range(200):
        m = rng_obj.choice([i for i in range(-4, 5) if i not in (0, 1, -1)])
        b = rng_obj.choice([i for i in range(-6, 7)])
        if variant == "pos_slope" and m < 0:
            continue
        if variant == "neg_slope" and m > 0:
            continue
        sub = variant or ("pos_slope" if m > 0 else "neg_slope")

        x_vals = sorted(rng_obj.sample([-2, -1, 0, 1, 2, 3], 3))
        y_vals = [m * x + b for x in x_vals]

        def fmt_table(xs, ys):
            return "; ".join(f"({x}, {y})" for x, y in zip(xs, ys))

        ans = fmt_table(x_vals, y_vals)

        # Wrong choice 1: one y-value off by +1
        err_idx  = rng_obj.randint(0, 2)
        w1_ys    = y_vals.copy()
        w1_ys[err_idx] += 1
        w1 = fmt_table(x_vals, w1_ys)

        # Wrong choice 2: wrong slope (m ± 1, keep ≠ 0)
        m2   = m + 1 if m + 1 != 0 else m - 1
        w2   = fmt_table(x_vals, [m2 * x + b for x in x_vals])

        # Wrong choice 3: wrong intercept
        b3   = b + rng_obj.choice([i for i in range(-3, 4) if i != 0])
        w3   = fmt_table(x_vals, [m * x + b3 for x in x_vals])

        if len({ans, w1, w2, w3}) < 4:
            continue

        params = {"m": m, "b": b, "x0": x_vals[0],
                  "tpl": "match_equation_to_table", "variant": sub}
        ph = param_hash(params)
        if ph in exclude_params:
            continue

        distractors = make_distractors(ans, [w1, w2, w3])
        eq_str = fmt_fn(m, b)
        exact  = (f"Which of the following sets of (x, y) values satisfies the equation {eq_str}?")
        ctx = (f"T3 match_equation_to_table (Medium MCQ). "
               f"Equation: {eq_str}. "
               f"Correct: {ans}. "
               f"Distractor (off-by-1 at x={x_vals[err_idx]}): {w1}. "
               f"Distractor (wrong slope m={m2}): {w2}. "
               f"Distractor (wrong intercept b={b3}): {w3}. "
               f"CRITICAL — stem is locked (exactStem). "
               f"Present each choice as a list of ordered pairs (x, y).")
        result = _l2v(2, params, ph, ans, distractors, None, None, "mcq", ctx)
        result["exactStem"] = exact
        if validate_math_object(result):
            continue
        return result
    raise RuntimeError("match_equation_to_table d2: could not generate unique params")


def _d2_interpret_term_in_context(rng_obj, exclude_params, variant=None):
    """T4b Medium: given y = mx + b with real context, what does the term mx represent?"""
    for _ in range(200):
        sc_idx = rng_obj.randint(0, len(_L2V_INTERP_SCENARIOS) - 1)
        sc     = _L2V_INTERP_SCENARIOS[sc_idx]
        x_sym, x_label, y_label, ctx_fmt, slope_interp, intercept_interp = sc

        if variant == "revenue_term" and x_label not in ("items sold", "sessions attended"):
            continue
        if variant == "cost_term" and x_label not in ("hours worked", "miles driven"):
            continue
        sub = variant or (
            "revenue_term" if x_label in ("items sold", "sessions attended") else "cost_term"
        )

        m = rng_obj.choice([2, 3, 4, 5, 8, 10, 12, 15])
        b = rng_obj.choice([10, 15, 20, 25, 30, 40, 50])
        if m == b:
            continue

        term_interp = _L2V_TERM_INTERP.get(
            x_label, f"the total {y_label} from {x_label}"
        )
        ans = term_interp
        d1  = slope_interp           # just the per-unit rate (m alone)
        d2  = intercept_interp       # the fixed/initial value (b alone)
        d3  = f"the {y_label}, including both fixed and variable portions"
        if len({ans, d1, d2, d3}) < 4:
            continue

        params = {"m": m, "b": b, "sc_idx": sc_idx,
                  "tpl": "interpret_term_in_context", "variant": sub}
        ph = param_hash(params)
        if ph in exclude_params:
            continue

        ctx_desc    = ctx_fmt.format(m=m, b=b)
        distractors = make_distractors(ans, [d1, d2, d3])
        ctx = (f"T4b interpret_term_in_context (Medium MCQ). "
               f"Context: {ctx_desc} "
               f"Question: which best describes what the term {m}{x_sym} represents? "
               f"Correct: '{ans}'. "
               f"Distractor (rate only): '{d1}'. "
               f"Distractor (intercept): '{d2}'. "
               f"Distractor (full equation): '{d3}'. "
               f"Do NOT include the equation in the stem — describe the context in words only. "
               f"Ask what the term containing {x_sym} represents (not just the coefficient). "
               f"Present all 4 choices verbatim as answer options.")
        result = _l2v(2, params, ph, ans, distractors, None, None, "mcq", ctx)
        if validate_math_object(result):
            continue
        return result
    raise RuntimeError("interpret_term_in_context d2: could not generate unique params")


def _d2_write_parallel_eq_through_point(rng_obj, exclude_params, variant=None):
    """T5 Medium: given reference line and a point, write equation of the parallel line through that point."""
    for _ in range(200):
        m  = rng_obj.choice([i for i in range(-4, 5) if i not in (0, 1, -1)])
        b0 = rng_obj.choice([i for i in range(-5, 6)])
        x0 = rng_obj.choice([i for i in range(-4, 5) if i != 0])
        # y0 must NOT lie on the reference line
        y0_offset = rng_obj.choice([i for i in range(-4, 5) if i != 0])
        y0        = m * x0 + b0 + y0_offset
        b_new     = y0 - m * x0          # b_new = b0 + y0_offset
        assert b_new != b0

        if variant == "pos_slope" and m < 0:
            continue
        if variant == "neg_slope" and m > 0:
            continue
        sub = variant or ("pos_slope" if m > 0 else "neg_slope")

        params = {"m": m, "b0": b0, "x0": x0, "y0": y0,
                  "tpl": "write_parallel_eq_through_point", "variant": sub}
        ph = param_hash(params)
        if ph in exclude_params:
            continue

        ans = fmt_fn(m, b_new)
        d1  = fmt_fn(m, b0)          # original reference line (parallel but wrong)
        d2  = fmt_fn(m, b_new + 1)   # correct slope, intercept off by 1
        d3  = fmt_fn(-m, b_new)      # negated slope, correct intercept
        if len({ans, d1, d2, d3}) < 4:
            continue

        ref_str     = fmt_fn(m, b0)
        distractors = make_distractors(ans, [d1, d2, d3])
        exact = (f"Line l is defined by {ref_str}. Line k is parallel to line l and passes "
                 f"through the point ({x0}, {y0}). Which equation defines line k?")
        ctx = (f"T5 write_parallel_eq_through_point (Medium MCQ). "
               f"Reference: {ref_str}. Point: ({x0},{y0}). "
               f"Parallel → same slope m={m}. New intercept: {y0}−({m})×({x0}) = {b_new}. "
               f"Correct: {ans}. "
               f"Distractor (original line): {d1}. "
               f"Distractor (intercept off by 1): {d2}. "
               f"Distractor (negated slope): {d3}. "
               f"CRITICAL — stem is locked (exactStem). Do NOT rewrite it.")
        result = _l2v(2, params, ph, ans, distractors, None, None, "mcq", ctx)
        result["exactStem"] = exact
        if validate_math_object(result):
            continue
        return result
    raise RuntimeError("write_parallel_eq_through_point d2: could not generate unique params")


def _d3_find_intercept_from_slope_and_x_int(rng_obj, exclude_params, variant=None):
    """T7c Hard: given slope m and x-intercept r, find the y-intercept."""
    for _ in range(200):
        m = rng_obj.choice([i for i in range(-5, 6) if i not in (0, 1, -1)])
        r = rng_obj.choice([i for i in range(-6, 7) if i != 0])
        y_int = -m * r

        if y_int == 0:
            continue
        if variant == "pos_y_int" and y_int <= 0:
            continue
        if variant == "neg_y_int" and y_int >= 0:
            continue
        sub = variant or ("pos_y_int" if y_int > 0 else "neg_y_int")

        params = {"m": m, "r": r, "tpl": "find_intercept_from_slope_and_x_int", "variant": sub}
        ph = param_hash(params)
        if ph in exclude_params:
            continue

        # Line: y = m(x − r).  At x=0: y = −mr
        assert m * (0 - r) == y_int

        ans = str(y_int)
        d1  = str(m * r)     # sign error: +mr instead of −mr
        d2  = str(m + r)     # adds slope + x-intercept
        d3  = str(r)         # returns x-intercept as y-intercept
        if len({ans, d1, d2, d3}) < 4:
            continue

        distractors = make_distractors(ans, [d1, d2, d3])
        exact = (f"In the xy-plane, a line has slope {m} and x-intercept {r}. "
                 f"What is the y-intercept of the line?")
        ctx = (f"T7c find_intercept_from_slope_and_x_int (Hard MCQ). "
               f"Slope m={m}, x-intercept r={r}. "
               f"Line: y = {m}(x − {r}) = {m}x − {m*r}. "
               f"y-intercept (x=0): y = {m}(0 − {r}) = {y_int}. "
               f"Correct: {ans}. "
               f"Distractor {d1}: sign error — used +mr. "
               f"Distractor {d2}: added slope and x-intercept. "
               f"Distractor {d3}: confused x-intercept for y-intercept. "
               f"CRITICAL — stem is locked (exactStem). Do NOT rewrite it.")
        result = _l2v(3, params, ph, ans, distractors, None, None, "mcq", ctx)
        result["exactStem"] = exact
        if validate_math_object(result):
            continue
        return result
    raise RuntimeError("find_intercept_from_slope_and_x_int d3: could not generate unique params")


# ── Routing dicts ─────────────────────────────────────────────────────────────

_D1 = {
    "read_slope":                    {"fn": _d1_read_slope,                    "variants": ["pos_slope", "neg_slope"]},
    "read_y_intercept":              {"fn": _d1_read_y_intercept,              "variants": ["pos_intercept", "neg_intercept"]},
    "match_graph_to_equation":       {"fn": _d1_match_graph_to_equation,       "variants": ["shallow_slope", "steep_slope"]},
    "parallel_slope":                {"fn": _d1_parallel_slope,                "variants": ["neg_slope", "pos_slope"]},
    "parallel_from_standard_form":   {"fn": _d1_parallel_from_standard_form,   "variants": ["identify_equation", "identify_not_parallel"]},
    # NEW T1/T3/T4/T6 coverage
    "word_problem_setup":            {"fn": _d1_word_problem_setup,            "variants": ["find_y", "find_x"]},
    "interpret_slope_in_context":    {"fn": _d1_interpret_slope_in_context,    "variants": ["rate_per_unit", "cost_per_item"]},
    "interpret_intercept_in_context":{"fn": _d1_interpret_intercept_in_context,"variants": ["initial_value", "fixed_fee"]},
    "write_equation_slope_intercept":{"fn": _d1_write_equation_slope_intercept,"variants": ["pos_slope", "neg_slope"]},
    "table_to_equation":             {"fn": _d1_table_to_equation,             "variants": ["integer_slope", "integer_neg_slope"]},
}

_D2 = {
    "slope_from_two_points":         {"fn": _d2_slope_from_two_points,         "variants": ["compute_slope", "find_missing_coordinate"]},
    "perpendicular_slope":           {"fn": _d2_perpendicular_slope,           "variants": ["large_m", "small_m"]},
    "slope_from_standard_form":      {"fn": _d2_slope_from_standard_form,      "variants": ["neg_frac", "neg_large"]},
    "find_y_intercept_std":          {"fn": _d2_find_y_intercept_std,          "variants": ["small_intercept", "large_intercept"]},
    "match_graph_to_equation":       {"fn": _d2_match_graph_to_equation,       "variants": ["neg_slope", "pos_slope"]},
    "parallel_slope":                {"fn": _d2_parallel_slope,                "variants": ["proper_frac", "improper_frac"]},
    "parallel_from_standard_form":   {"fn": _d2_parallel_from_standard_form,   "variants": ["identify_parallel", "identify_perpendicular"]},
    # NEW T1/T6/T7 coverage
    "word_problem_rate_model":        {"fn": _d2_word_problem_rate_model,        "variants": ["solve_quantity", "solve_cost"]},
    "write_equation_slope_point":     {"fn": _d2_write_equation_slope_point,     "variants": ["pos_slope", "neg_slope"]},
    "write_equation_two_points":      {"fn": _d2_write_equation_two_points,      "variants": ["pos_slope", "neg_slope"]},
    "find_x_intercept_standard_form": {"fn": _d2_find_x_intercept_standard_form, "variants": ["integer_result", "frac_result"]},
    # NEW T2e/T3/T4b/T5-full coverage
    "slope_from_table":               {"fn": _d2_slope_from_table,               "variants": ["integer_slope", "frac_slope"]},
    "match_equation_to_table":        {"fn": _d2_match_equation_to_table,        "variants": ["pos_slope", "neg_slope"]},
    "interpret_term_in_context":      {"fn": _d2_interpret_term_in_context,      "variants": ["revenue_term", "cost_term"]},
    "write_parallel_eq_through_point":{"fn": _d2_write_parallel_eq_through_point,"variants": ["pos_slope", "neg_slope"]},
}

_D3 = {
    "function_shift":                {"fn": _d3_function_shift,                "variants": ["shift_down", "shift_up"]},
    "translate_intercept":           {"fn": _d3_translate_intercept,           "variants": ["small_k", "large_k"]},
    "slope_complex_expr":            {"fn": _d3_slope_complex_expr,            "variants": ["single_fraction", "two_fraction_terms"]},
    "match_graph_to_equation":       {"fn": _d3_match_graph_to_equation,       "variants": ["small_intercepts", "large_intercepts"]},
    "parallel_from_standard_form":   {"fn": _d3_parallel_from_standard_form,   "variants": ["find_y_coeff", "which_equation_parallel"]},
    # NEW T1/T3/T7c coverage
    "word_problem_hard":                  {"fn": _d3_word_problem_hard,                  "variants": ["spr_value", "mcq_equation"]},
    "table_to_equation_hard":             {"fn": _d3_table_to_equation_hard,             "variants": ["frac_slope", "neg_frac_slope"]},
    "find_intercept_from_slope_and_x_int":{"fn": _d3_find_intercept_from_slope_and_x_int,"variants": ["pos_y_int", "neg_y_int"]},
}

_ROUTING = {1: _D1, 2: _D2, 3: _D3}

# _L2V_TEMPLATES auto-derived from routing dicts — single source of truth
_L2V_TEMPLATES = {d: set(tpls.keys()) for d, tpls in _ROUTING.items()}


# ── Public metadata API ───────────────────────────────────────────────────────

def l2v_variants(difficulty: int, template: str = None) -> dict:
    """
    Return variant metadata for linear_eq_two_var.

    If template is None: returns {template: [variants]} for all templates at
    the given difficulty level.

    If template is given: returns {"variants": [...]} for that specific template.
    """
    routing = _ROUTING.get(difficulty, {})
    if template is None:
        return {tpl: entry["variants"] for tpl, entry in routing.items()}
    if template not in routing:
        raise ValueError(f"Unknown template '{template}' for linear_eq_two_var d{difficulty}")
    return {"variants": routing[template]["variants"]}


# ── Main generator ────────────────────────────────────────────────────────────

def gen_linear_eq_two_var(difficulty: int, rng_obj: random.Random, exclude_params: set,
                           force_template: str = None,
                           force_variant: str = None,
                           **_kwargs) -> dict:
    """
    Linear equations in two variables (L2V).

    Dispatches to a standalone per-template function via _D1/_D2/_D3 routing dicts.

    Args:
        force_template: pin to a specific template (e.g. "parallel_slope").
                        If None, picks randomly from the difficulty level's template pool.
        force_variant:  pin to a specific variant within the template
                        (e.g. "neg_slope"). If None, no variant filter is applied
                        (any variant may be generated).
    """
    clamped = min(max(difficulty, 1), 3)
    routing = _ROUTING.get(clamped, _D3)

    if force_template is not None:
        if force_template not in routing:
            valid = sorted(routing.keys())
            raise ValueError(
                f"--template '{force_template}' is not valid for "
                f"linear_eq_two_var d{clamped}. Valid: {valid}"
            )
        tpl = force_template
    else:
        tpl = rng_obj.choice(list(routing.keys()))

    entry = routing[tpl]
    return entry["fn"](rng_obj, exclude_params, variant=force_variant)
