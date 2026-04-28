import math as _math
import random
import sympy as sp
from sympy import symbols, solve, Rational
from .core import (
    param_hash, fmt_num, fmt_fn, fmt_fx, fmt_lin_rhs,
    spr_bounds, make_distractors, validate_math_object,
)

# ── Helpers ───────────────────────────────────────────────────────────────────

def _lfn(d, params, ph, ans, distractors, sm, sx, qt, ctx, diag=None):
    """Standard LFN result builder."""
    return {"skill": "linear_functions", "difficulty": d, "questionType": qt,
            "params": params, "paramHash": ph, "verifiedAnswer": ans,
            "distractors": distractors, "sprMin": sm, "sprMax": sx,
            "scenarioTag": None, "diagramSpec": diag, "questionContext": ctx}


def _fmt_fn_as_fx(m, b):
    """Format f(x) = mx + b, handling m = ±1 and b = 0."""
    if m == 1:
        mx = "x"
    elif m == -1:
        mx = "-x"
    else:
        mx = f"{m}x"
    if b == 0:
        return f"f(x) = {mx}"
    if b > 0:
        return f"f(x) = {mx} + {b}"
    return f"f(x) = {mx} - {abs(b)}"


# ── Contextual scenario pools ────────────────────────────────────────────────

_LFN_SLOPE_SCENARIOS = [
    # (quantity, rate_noun, rate_per, unit_out)
    ("total cost", "cost per", "item", "dollars"),
    ("total pay", "pay per", "hour", "dollars"),
    ("distance traveled", "speed of", "second", "feet"),
    ("water collected", "collection rate of", "minute", "liters"),
    ("pages read", "reading rate of", "day", "pages"),
]

_LFN_INTERCEPT_SCENARIOS = [
    # (quantity, start_noun, unit_out, rate_label, rate_unit)
    ("height of a tree", "initial height", "inches", "growth rate", "inches per year"),
    ("bank balance", "initial deposit", "dollars", "weekly deposit", "dollars per week"),
    ("water volume", "starting volume", "liters", "evaporation rate", "liters per day"),
    ("song practice count", "starting count", "songs", "daily practice", "songs per day"),
]

_LFN_DECAY_SCENARIOS = [
    # (quantity, init_label, unit_out, rate_label, rate_unit, tick)
    ("gasoline remaining in a tank", "initial gasoline", "gallons", "usage rate", "gallons per mile", "mile"),
    ("juice remaining in a pitcher", "initial volume", "fluid ounces", "pour rate", "fluid ounces per cup", "cup"),
    ("water remaining in a reservoir", "initial amount", "liters", "leak rate", "liters per hour", "hour"),
]

_LFN_WORD_FLAT_RATE = [
    # (total_name, total_units, fixed_name, per_name, per_unit)
    ("total cost", "dollars", "flat shipping fee", "cost per item", "item"),
    ("total charge", "dollars", "activation fee", "monthly charge", "month"),
    ("total cost", "dollars", "insurance fee", "daily rental", "day"),
    ("total balance", "dollars", "starting savings", "weekly deposit", "week"),
]

_LFN_TIERED_SCENARIOS = [
    # (item, first_unit, rest_unit)
    ("backhoe rental", "first day", "each additional day"),
    ("carpet cleaner rental", "first day", "each additional day"),
    ("kayak rental", "first hour", "each additional hour"),
    ("dumpster rental", "first day", "each additional day"),
]


# ═══════════════════════════════════════════════════════════════════════════════
# d1 TEMPLATE FUNCTIONS (Easy — 9 templates)
# ═══════════════════════════════════════════════════════════════════════════════

def _d1_evaluate_integer(rng_obj, exclude_params, variant=None):
    """Given f(x) = mx + b, evaluate at integer x.
    Variants: pos_input, neg_input, neg_slope, eval_at_zero, unit_coefficient.
    """
    x = symbols("x")
    for _ in range(200):
        m = rng_obj.choice([i for i in range(-6, 7) if i != 0])
        b = rng_obj.choice([i for i in range(-10, 11) if i != 0])
        xv = rng_obj.choice([i for i in range(-8, 9) if i != 0])
        # Variant gates
        if variant == "pos_input" and xv < 0:
            continue
        if variant == "neg_input" and xv > 0:
            continue
        if variant == "neg_slope" and m > 0:
            continue
        if variant == "eval_at_zero":
            xv = 0
        if variant == "unit_coefficient" and abs(m) != 1:
            continue
        # Derive variant when None
        if variant is None:
            if xv == 0:
                sub = "eval_at_zero"
            elif abs(m) == 1:
                sub = "unit_coefficient"
            elif m < 0:
                sub = "neg_slope"
            elif xv < 0:
                sub = "neg_input"
            else:
                sub = "pos_input"
        else:
            sub = variant
        yv = m * xv + b
        if abs(yv) > 200:
            continue
        params = {"m": m, "b": b, "xv": xv,
                  "tpl": "evaluate_integer", "variant": sub}
        ph = param_hash(params)
        if ph in exclude_params:
            continue
        assert sp.expand(m * x + b).subs(x, xv) == yv
        ans = str(yv)
        distractors = make_distractors(ans, [
            str(m * xv),        # forgot to add b
            str(m + xv + b),    # added everything
            str(yv + b),        # double-counted b
            str(-yv),           # sign error
        ])
        eq_str = _fmt_fn_as_fx(m, b)
        exact_stem = f"The function f is defined by {eq_str}. What is the value of f({xv})?"
        ctx = (f"LFN d1 evaluate_integer ({sub}). "
               f"Function: {eq_str}. Substitute x = {xv}: {m}({xv}) + {b} = {yv}. "
               f"Correct: {ans}. "
               f"Distractor {m*xv}: forgot to add b. "
               f"Distractor {-yv}: sign error. Stem is locked — do not rewrite it.")
        result = _lfn(1, params, ph, ans, distractors, None, None, "mcq", ctx, None)
        result["exactStem"] = exact_stem
        if validate_math_object(result):
            continue
        return result
    raise RuntimeError("evaluate_integer d1: could not generate unique params")


def _d1_evaluate_fraction(rng_obj, exclude_params, variant=None):
    """Given f(x) with fractional or decimal coefficient, evaluate.
    Variants: pos_frac, neg_frac, decimal_coeff.
    """
    x = symbols("x")
    for _ in range(200):
        if variant == "decimal_coeff":
            # Decimal coefficient version: f(x) = 0.Nx + b
            coef_dec = rng_obj.choice([Rational(1, 4), Rational(1, 2), Rational(3, 4),
                                        Rational(1, 5), Rational(2, 5)])
            b = rng_obj.randint(1, 10)
            # Pick x so coef*x is an integer
            xv = coef_dec.denominator * rng_obj.randint(1, 6)
            yv = coef_dec * xv + b
            if yv.denominator != 1:
                continue
            yv = int(yv)
            sub = "decimal_coeff"
            params = {"n": coef_dec.numerator, "d": coef_dec.denominator, "b": b, "xv": xv,
                      "tpl": "evaluate_fraction", "variant": sub}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(yv)
            dec_str = f"{float(coef_dec)}"
            exact_stem = (
                f"The function f is defined by f(x) = {dec_str}x + {b}. "
                f"What is the value of f({xv})?"
            )
            ctx = (f"LFN d1 evaluate_fraction (decimal_coeff). "
                   f"Function: f(x) = {dec_str}x + {b}. "
                   f"Substitute x = {xv}: {dec_str}·{xv} + {b} = {yv}. "
                   f"Correct: {ans}. Stem is locked — do not rewrite it.")
            sm, sx = spr_bounds(ans)
            result = _lfn(1, params, ph, ans, [], sm, sx, "spr", ctx, None)
            result["exactStem"] = exact_stem
            if validate_math_object(result):
                continue
            return result

        # Fractional variants
        den = rng_obj.choice([2, 3, 4, 5, 6])
        num = rng_obj.choice([i for i in range(-6, 7) if i != 0])
        b_num = rng_obj.choice([i for i in range(-6, 7) if i != 0])
        # Choose x as a multiple of den so product is clean
        xv = den * rng_obj.choice([i for i in range(-4, 5) if i != 0])
        yv = Rational(num, den) * xv + Rational(b_num, den)
        if yv.denominator != 1:
            continue
        yv = int(yv)
        if abs(yv) > 30:
            continue
        if variant == "pos_frac" and num < 0:
            continue
        if variant == "neg_frac" and num > 0:
            continue
        sub = variant or ("pos_frac" if num > 0 else "neg_frac")
        params = {"num": num, "den": den, "b_num": b_num, "xv": xv,
                  "tpl": "evaluate_fraction", "variant": sub}
        ph = param_hash(params)
        if ph in exclude_params:
            continue
        ans = str(yv)
        frac_str = f"{num}/{den}"
        bfrac_str = f"{b_num}/{den}"
        exact_stem = (
            f"The function f is defined by "
            f"\\(f(x) = \\frac{{{num}}}{{{den}}}x + \\frac{{{b_num}}}{{{den}}}\\). "
            f"What is the value of f({xv})?"
        )
        ctx = (f"LFN d1 evaluate_fraction ({sub}). "
               f"Function: f(x) = {frac_str}·x + {bfrac_str}. "
               f"Substitute x = {xv}: {frac_str}·{xv} + {bfrac_str} = {yv}. "
               f"Correct: {ans}. Stem is locked — do not rewrite it.")
        sm, sx = spr_bounds(ans)
        result = _lfn(1, params, ph, ans, [], sm, sx, "spr", ctx, None)
        result["exactStem"] = exact_stem
        if validate_math_object(result):
            continue
        return result
    raise RuntimeError("evaluate_fraction d1: could not generate unique params")


def _d1_interpret_slope_easy(rng_obj, exclude_params, variant=None):
    """Interpret m as rate of change in context.
    Variants: rate_per_unit, cost_per_item, decrease_rate.
    """
    for _ in range(200):
        if variant == "decrease_rate":
            sub = "decrease_rate"
            sc = rng_obj.choice(_LFN_DECAY_SCENARIOS)
            quantity, init_label, unit_out, rate_label, rate_unit, tick = sc
            m_val = rng_obj.choice([Rational(1, 20), Rational(1, 10), Rational(1, 5), Rational(1, 4)])
            b_val = rng_obj.randint(20, 80)
            m_disp = str(float(m_val))
            params = {"m_num": m_val.numerator, "m_den": m_val.denominator, "b": b_val,
                      "sc_idx": _LFN_DECAY_SCENARIOS.index(sc),
                      "tpl": "interpret_slope_easy", "variant": sub}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = f"The rate, in {rate_unit}, at which the {quantity.split(' remaining')[0]} decreases"
            d1 = f"The initial {init_label}"
            d2 = f"The total {quantity.split(' remaining')[0]} after {b_val} {tick}s"
            d3 = f"The amount of {quantity.split(' remaining')[0]} gained per {tick}"
            distractors = make_distractors(ans, [d1, d2, d3])
            exact_stem = (
                f"The function f is defined by f(x) = {b_val} - {m_disp}x, where f(x) is the "
                f"{quantity} after x {tick}s. Which of the following is the best interpretation "
                f"of {m_disp} in this context?"
            )
            ctx = (f"LFN d1 interpret_slope_easy (decrease_rate). "
                   f"Stem (set verbatim): '{exact_stem}'. "
                   f"The coefficient {m_disp} is the decrease rate per {tick}. "
                   f"Correct: '{ans}'. "
                   f"CRITICAL — do NOT state the value {b_val} as meaningful; it is the intercept.")
            result = _lfn(1, params, ph, ans, distractors, None, None, "mcq", ctx, None)
            result["exactStem"] = exact_stem
            if validate_math_object(result):
                continue
            return result

        # rate_per_unit or cost_per_item
        sc = rng_obj.choice(_LFN_SLOPE_SCENARIOS)
        quantity, rate_noun, rate_per, unit_out = sc
        m = rng_obj.choice([3, 4, 5, 8, 10, 12, 15, 20, 25])
        b = rng_obj.choice([10, 15, 20, 25, 30, 40, 50])
        if m == b:
            continue
        # Variant classification based on scenario
        if rate_per in ("item", "hour"):
            derived_variant = "cost_per_item"
        else:
            derived_variant = "rate_per_unit"
        if variant == "rate_per_unit" and derived_variant != "rate_per_unit":
            continue
        if variant == "cost_per_item" and derived_variant != "cost_per_item":
            continue
        sub = variant or derived_variant
        params = {"m": m, "b": b, "sc_idx": _LFN_SLOPE_SCENARIOS.index(sc),
                  "tpl": "interpret_slope_easy", "variant": sub}
        ph = param_hash(params)
        if ph in exclude_params:
            continue
        ans = f"The {rate_noun} {rate_per}, in {unit_out}"
        d1 = f"The fixed starting {quantity}, in {unit_out}"
        d2 = f"The total {quantity}, in {unit_out}, for {m} {rate_per}s"
        d3 = f"The number of {rate_per}s"
        distractors = make_distractors(ans, [d1, d2, d3])
        exact_stem = (
            f"The function f is defined by f(x) = {m}x + {b}, where f(x) is the {quantity}, "
            f"in {unit_out}, for x {rate_per}s. Which of the following is the best interpretation "
            f"of {m} in this context?"
        )
        ctx = (f"LFN d1 interpret_slope_easy ({sub}). "
               f"Stem (set verbatim): '{exact_stem}'. "
               f"The coefficient {m} is the {rate_noun} {rate_per}, in {unit_out}. "
               f"Correct: '{ans}'. "
               f"Distractor (intercept confusion): '{d1}'.")
        result = _lfn(1, params, ph, ans, distractors, None, None, "mcq", ctx, None)
        result["exactStem"] = exact_stem
        if validate_math_object(result):
            continue
        return result
    raise RuntimeError("interpret_slope_easy d1: could not generate unique params")


def _d1_interpret_intercept_easy(rng_obj, exclude_params, variant=None):
    """Interpret b as starting value in context.
    Variants: initial_value, starting_amount, constant_in_growth, find_y_intercept.
    """
    for _ in range(200):
        if variant == "find_y_intercept":
            sub = "find_y_intercept"
            num = rng_obj.choice([i for i in range(-6, 7) if i != 0])
            den = rng_obj.choice([2, 3, 4, 5, 10])
            b = rng_obj.choice([i for i in range(-8, 9) if i != 0])
            params = {"num": num, "den": den, "b": b,
                      "tpl": "interpret_intercept_easy", "variant": sub}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = f"(0, {b})"
            distractors = make_distractors(ans, [
                f"(0, {num}/{den})",
                f"({b}, 0)",
                f"(0, {-b})",
            ])
            exact_stem = (
                f"The function f is defined by "
                f"\\(f(x) = \\frac{{{num}}}{{{den}}}x + {b}\\). "
                f"What is the y-intercept of the graph of y = f(x) in the xy-plane?"
            )
            ctx = (f"LFN d1 interpret_intercept_easy (find_y_intercept). "
                   f"Function: f(x) = {num}/{den}·x + {b}. "
                   f"The y-intercept is f(0) = {b}, formatted as ordered pair (0, {b}). "
                   f"Correct: {ans}. Stem is locked — do not rewrite it.")
            result = _lfn(1, params, ph, ans, distractors, None, None, "mcq", ctx, None)
            result["exactStem"] = exact_stem
            if validate_math_object(result):
                continue
            return result

        sc = rng_obj.choice(_LFN_INTERCEPT_SCENARIOS)
        quantity, start_noun, unit_out, rate_label, rate_unit = sc
        m = rng_obj.choice([2, 3, 4, 5, 8, 10])
        b = rng_obj.choice([4, 6, 9, 10, 12, 15, 18, 20])
        if m == b:
            continue
        derived = rng_obj.choice(["initial_value", "starting_amount", "constant_in_growth"])
        if variant in ("initial_value", "starting_amount", "constant_in_growth"):
            derived = variant
        sub = derived
        params = {"m": m, "b": b, "sc_idx": _LFN_INTERCEPT_SCENARIOS.index(sc),
                  "tpl": "interpret_intercept_easy", "variant": sub}
        ph = param_hash(params)
        if ph in exclude_params:
            continue
        ans = f"The {start_noun}, in {unit_out}, at the start of observation"
        d1 = f"The {rate_label}, in {rate_unit}"
        d2 = f"The total {quantity}, in {unit_out}, after {b} time units"
        d3 = f"The number of time units observed"
        distractors = make_distractors(ans, [d1, d2, d3])
        exact_stem = (
            f"The function f is defined by f(x) = {m}x + {b}, where f(x) is the {quantity}, "
            f"in {unit_out}, x time units after the start of observation. Which of the following "
            f"is the best interpretation of {b} in this context?"
        )
        ctx = (f"LFN d1 interpret_intercept_easy ({sub}). "
               f"Stem (set verbatim): '{exact_stem}'. "
               f"The constant {b} is f(0), which is the starting value. "
               f"Correct: '{ans}'. "
               f"Distractor (rate confusion): '{d1}'.")
        result = _lfn(1, params, ph, ans, distractors, None, None, "mcq", ctx, None)
        result["exactStem"] = exact_stem
        if validate_math_object(result):
            continue
        return result
    raise RuntimeError("interpret_intercept_easy d1: could not generate unique params")


def _d1_graph_read_intercept(rng_obj, exclude_params, variant=None):
    """Read x- or y-intercept from a linear-function graph.
    Variants: x_intercept, y_intercept, identify_y_coord.
    """
    for _ in range(200):
        m = rng_obj.choice([i for i in range(-4, 5) if i != 0])
        # b must stay within ±4 so both intercepts are visible in the ±5 viewport
        b = rng_obj.choice([i for i in range(-4, 5) if i != 0 and i != m])
        # Need clean x-intercept: -b/m integer and within ±4 viewport margin
        if b % m != 0:
            continue
        x_int = -b // m
        if abs(x_int) > 4:
            continue
        # Guard: when b == x_int (m=-1) or b == -x_int (m=1), distractor (b,0) duplicates
        # the answer or its sign-flip, forcing make_distractors to substitute a scalar which
        # creates an inconsistent choice set.
        if variant == "x_intercept" and (b == x_int or b == -x_int):
            continue

        if variant == "x_intercept":
            sub = "x_intercept"
            ans = f"({x_int}, 0)"
            distractors = make_distractors(ans, [
                f"(0, {b})",
                f"({-x_int}, 0)",
                f"({b}, 0)",
            ])
            exact_stem = "The function f is graphed in the xy-plane. What is the x-intercept of the graph of y = f(x)?"
            ctx = (f"LFN d1 graph_read_intercept (x_intercept). "
                   f"Line f(x) = {m}x + {b}, slope {m}, y-intercept (0, {b}). "
                   f"x-intercept: ({x_int}, 0). Correct: {ans}. "
                   f"CRITICAL — do NOT list the coordinates ({x_int}, 0) in the stem. "
                   f"Stem is locked — do not rewrite it.")
        elif variant == "y_intercept":
            sub = "y_intercept"
            ans = f"(0, {b})"
            distractors = make_distractors(ans, [
                f"({x_int}, 0)",
                f"(0, {-b})",
                f"({b}, 0)",
            ])
            exact_stem = "The function f is graphed in the xy-plane. What is the y-intercept of the graph of y = f(x)?"
            ctx = (f"LFN d1 graph_read_intercept (y_intercept). "
                   f"Line f(x) = {m}x + {b}, slope {m}, x-intercept ({x_int}, 0). "
                   f"y-intercept: (0, {b}). Correct: {ans}. "
                   f"CRITICAL — do NOT list the coordinates (0, {b}) in the stem. "
                   f"Stem is locked — do not rewrite it.")
        else:
            sub = "identify_y_coord"
            ans = f"(0, {b})"
            distractors = make_distractors(ans, [
                f"({b}, 0)",
                f"(0, {-b})",
                f"({-b}, 0)",
            ])
            exact_stem = "The function f is graphed in the xy-plane. Which of the following is the y-intercept of the graph of y = f(x)?"
            ctx = (f"LFN d1 graph_read_intercept (identify_y_coord). "
                   f"The line crosses the y-axis at y = {b}. Correct: {ans}. "
                   f"Test coordinate-form awareness — student reads y = {b} from graph and picks ordered pair. "
                   f"Stem is locked — do not rewrite it.")

        params = {"m": m, "b": b, "tpl": "graph_read_intercept", "variant": sub}
        ph = param_hash(params)
        if ph in exclude_params:
            continue
        diag = {"type": "coordinate_plane", "function": fmt_fn(m, b), "label": fmt_fn(m, b), "hideLabel": True}
        result = _lfn(1, params, ph, ans, distractors, None, None, "mcq", ctx, diag)
        result["exactStem"] = exact_stem
        if validate_math_object(result):
            continue
        return result
    raise RuntimeError("graph_read_intercept d1: could not generate unique params")


def _d1_word_equation_simple(rng_obj, exclude_params, variant=None):
    """Translate word problem into linear equation.
    Variants: flat_plus_rate, verbal_description, service_contract.
    """
    for _ in range(200):
        if variant == "verbal_description":
            sub = "verbal_description"
            n = rng_obj.randint(20, 120)
            op = rng_obj.choice(["less than", "more than"])
            params = {"n": n, "op": op, "tpl": "word_equation_simple", "variant": sub}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            if op == "less than":
                ans = f"y = x − {n}"
                distractors = make_distractors(ans, [
                    f"y = {n} − x",
                    f"y = x + {n}",
                    f"y = −{n}x",
                ])
            else:
                ans = f"y = x + {n}"
                distractors = make_distractors(ans, [
                    f"y = {n} − x",
                    f"y = x − {n}",
                    f"y = {n}x",
                ])
            exact_stem = (
                f"The value of y is {n} {op} the value of x. "
                f"Which of the following equations represents this relationship?"
            )
            ctx = (f"LFN d1 word_equation_simple (verbal_description). "
                   f"The value of y is {n} {op} the value of x. "
                   f"Correct: {ans}. Stem is locked — do not rewrite it.")
            result = _lfn(1, params, ph, ans, distractors, None, None, "mcq", ctx, None)
            result["exactStem"] = exact_stem
            if validate_math_object(result):
                continue
            return result

        sc = rng_obj.choice(_LFN_WORD_FLAT_RATE)
        total_name, total_units, fixed_name, per_name, per_unit = sc
        flat = rng_obj.choice([5, 10, 12, 15, 20, 25, 30, 35, 50])
        rate = rng_obj.choice([3, 4, 5, 8, 10, 12, 15, 20, 23, 25])
        if flat == rate:
            continue
        derived = rng_obj.choice(["flat_plus_rate", "service_contract"])
        if variant in ("flat_plus_rate", "service_contract"):
            derived = variant
        sub = derived
        params = {"flat": flat, "rate": rate, "sc_idx": _LFN_WORD_FLAT_RATE.index(sc),
                  "tpl": "word_equation_simple", "variant": sub}
        ph = param_hash(params)
        if ph in exclude_params:
            continue
        ans = f"y = {flat} + {rate}x"
        distractors = make_distractors(ans, [
            f"y = {rate} + {flat}x",
            f"y = {flat + rate}x",
            f"y = {flat}x + {rate}",
        ])
        exact_stem = (
            f"A service charges a ${flat} {fixed_name} plus ${rate} for each {per_unit}. "
            f"Which equation gives the {total_name} y, in {total_units}, of using this service "
            f"for x {per_unit}s?"
        )
        ctx = (f"LFN d1 word_equation_simple ({sub}). "
               f"Stem (set verbatim): '{exact_stem}'. "
               f"Flat: ${flat}. Rate: ${rate}/{per_unit}. "
               f"Equation: y = {flat} + {rate}x. "
               f"Correct: {ans}. "
               f"Distractor (swap): y = {rate} + {flat}x.")
        result = _lfn(1, params, ph, ans, distractors, None, None, "mcq", ctx, None)
        result["exactStem"] = exact_stem
        if validate_math_object(result):
            continue
        return result
    raise RuntimeError("word_equation_simple d1: could not generate unique params")


def _d1_inverse_evaluate_easy(rng_obj, exclude_params, variant=None):
    """Given f(x) = value, find x.
    Variants: one_step, two_step, distribute_solve.
    """
    x = symbols("x")
    for _ in range(200):
        if variant == "one_step":
            sub = "one_step"
            m = rng_obj.choice([2, 3, 4, 5, 6, 7, 8, 9, 10])
            x_ans = rng_obj.randint(2, 12)
            rhs = m * x_ans
            params = {"m": m, "rhs": rhs, "tpl": "inverse_evaluate_easy", "variant": sub}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(x_ans)
            distractors = make_distractors(ans, [str(rhs - m), str(rhs + m), str(rhs * m)])
            exact_stem = (
                f"The function f is defined by f(x) = {m}x. "
                f"What value of x gives f(x) = {rhs}?"
            )
            ctx = (f"LFN d1 inverse_evaluate_easy (one_step). "
                   f"f(x) = {m}x; f(x) = {rhs} → x = {x_ans}. "
                   f"Correct: {ans}. Stem is locked — do not rewrite it.")
            result = _lfn(1, params, ph, ans, distractors, None, None, "mcq", ctx, None)
            result["exactStem"] = exact_stem
            if validate_math_object(result):
                continue
            return result

        # two_step default
        sub = "two_step"
        m = rng_obj.choice([2, 3, 4, 5, 6, 7, 8])
        b = rng_obj.choice([i for i in range(-12, 13) if i != 0])
        x_ans = rng_obj.randint(1, 10)
        rhs = m * x_ans + b
        if rhs <= 0:
            continue
        params = {"m": m, "b": b, "rhs": rhs, "tpl": "inverse_evaluate_easy", "variant": sub}
        ph = param_hash(params)
        if ph in exclude_params:
            continue
        ans = str(x_ans)
        distractors = make_distractors(ans, [
            str(x_ans + 1),
            str((rhs + b) // m) if (rhs + b) % m == 0 else str(x_ans + 2),
            str(rhs - b),
        ])
        exact_stem = (
            f"The function f is defined by f(x) = {m}x + {b}. "
            f"If f(x) = {rhs}, what is the value of x?"
        )
        ctx = (f"LFN d1 inverse_evaluate_easy (two_step). "
               f"f(x) = {m}x + {b}; f(x) = {rhs} → {m}x = {rhs - b} → x = {x_ans}. "
               f"Correct: {ans}. SPR format. Stem is locked — do not rewrite it.")
        sm, sx = spr_bounds(ans)
        result = _lfn(1, params, ph, ans, [], sm, sx, "spr", ctx, None)
        result["exactStem"] = exact_stem
        if validate_math_object(result):
            continue
        return result
    raise RuntimeError("inverse_evaluate_easy d1: could not generate unique params")


def _d1_match_graph_to_equation_table(rng_obj, exclude_params, variant=None):
    """Match a function to its table of values.
    Variants: table_to_equation.
    """
    for _ in range(200):
        m = rng_obj.choice([i for i in range(-8, 9) if i not in (0, 1, -1)])
        b = rng_obj.choice([i for i in range(-10, 11) if i != 0])
        sub = "table_to_equation"
        xs = [0, 1, 2, 3]
        ys = [m * v + b for v in xs]
        params = {"m": m, "b": b, "tpl": "match_graph_to_equation_table", "variant": sub}
        ph = param_hash(params)
        if ph in exclude_params:
            continue
        correct_table = f"x: 0, 1, 2, 3 | g: {ys[0]}, {ys[1]}, {ys[2]}, {ys[3]}"
        # Distractor tables
        d1 = f"x: 0, 1, 2, 3 | g: {m}, {ys[1]}, {ys[2]}, {ys[3]}"      # intercept swap
        d2 = f"x: 0, 1, 2, 3 | g: {ys[0]}, {ys[0] + m + 1}, {ys[0] + 2*(m+1)}, {ys[0] + 3*(m+1)}"  # slope off by 1
        d3 = f"x: 0, 1, 2, 3 | g: 0, {m}, {2*m}, {3*m}"                 # missing intercept
        ans = correct_table
        distractors = make_distractors(ans, [d1, d2, d3])
        exact_stem = (
            f"Which of the following tables shows values consistent with the "
            f"function g(x) = {m}x + {b}?"
        )
        ctx = (f"LFN d1 match_graph_to_equation_table (table_to_equation). "
               f"Function g(x) = {m}x + {b}. g(0)={ys[0]}, g(1)={ys[1]}, g(2)={ys[2]}, g(3)={ys[3]}. "
               f"Correct table matches these. Stem is locked — do not rewrite it.")
        result = _lfn(1, params, ph, ans, distractors, None, None, "mcq", ctx, None)
        result["exactStem"] = exact_stem
        if validate_math_object(result):
            continue
        return result
    raise RuntimeError("match_graph_to_equation_table d1: could not generate unique params")


# ═══════════════════════════════════════════════════════════════════════════════
# d2 / d3 TEMPLATE FUNCTIONS — stubbed, to be filled in subsequent passes
# ═══════════════════════════════════════════════════════════════════════════════

def _stub(name):
    def _fn(rng_obj, exclude_params, variant=None):
        raise NotImplementedError(f"{name} not yet implemented")
    return _fn


def _d2_evaluate_compound(rng_obj, exclude_params, variant=None):
    """Chained/compound function evaluation.
    Variants: combine_two_fns, scaled_output, coefficient_gather, difference_single_fn, symbolic_input.
    """
    x = symbols("x")
    for _ in range(200):
        if variant == "symbolic_input":
            sub = "symbolic_input"
            m = rng_obj.choice([2, 3, 4, 5])
            b = rng_obj.choice([i for i in range(-10, 11) if i != 0])
            shift = rng_obj.choice([i for i in range(-6, 7) if i != 0])
            # f(k + shift) = m(k + shift) + b = mk + (m*shift + b)
            out_const = m * shift + b
            params = {"m": m, "b": b, "shift": shift,
                      "tpl": "evaluate_compound", "variant": sub}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            if out_const > 0:
                ans = f"{m}k + {out_const}"
                distractors = make_distractors(ans, [
                    f"{m}k + {b}",
                    f"{m}k + {shift}",
                    f"{m}k - {abs(out_const)}",
                ])
            else:
                ans = f"{m}k - {abs(out_const)}"
                distractors = make_distractors(ans, [
                    f"{m}k + {b}",
                    f"{m}k + {shift}",
                    f"{m}k + {abs(out_const)}",
                ])
            shift_disp = f"+ {shift}" if shift > 0 else f"- {abs(shift)}"
            exact_stem = (
                f"The function f is defined by f(x) = {m}x + {b}. "
                f"What is the value of f(k {shift_disp}) in terms of k?"
            )
            ctx = (f"LFN d2 evaluate_compound (symbolic_input). "
                   f"f(x) = {m}x + {b}. f(k {shift_disp}) = {m}(k {shift_disp}) + {b} = {m}k {shift_disp * 0} . "
                   f"Simplify: {m}k + ({m*shift} + {b}) = {ans}. "
                   f"Correct: {ans}. Stem is locked — do not rewrite it.")
            result = _lfn(2, params, ph, ans, distractors, None, None, "mcq", ctx, None)
            result["exactStem"] = exact_stem
            if validate_math_object(result):
                continue
            return result

        if variant == "difference_single_fn":
            sub = "difference_single_fn"
            m = rng_obj.choice([i for i in range(-8, 9) if i not in (0, 1, -1)])
            b = rng_obj.choice([i for i in range(-10, 11) if i != 0])
            a_in = rng_obj.randint(1, 8)
            b_in = a_in + rng_obj.randint(1, 6)
            fa = m * a_in + b
            fb = m * b_in + b
            ans_val = fb - fa
            if abs(ans_val) > 100 or ans_val == 0:
                continue
            params = {"m": m, "b": b, "a_in": a_in, "b_in": b_in,
                      "tpl": "evaluate_compound", "variant": sub}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(ans_val)
            distractors = make_distractors(ans, [
                str(fa), str(fb), str(fb + fa),
            ])
            exact_stem = (
                f"The function f is defined by f(x) = {m}x + {b}. "
                f"What is the value of f({b_in}) \u2212 f({a_in})?"
            )
            ctx = (f"LFN d2 evaluate_compound (difference_single_fn). "
                   f"f(x) = {m}x + {b}. f({b_in}) - f({a_in}) = {fb} - {fa} = {ans_val}. "
                   f"Shortcut: slope × (b-a) = {m}({b_in - a_in}) = {ans_val}. "
                   f"Correct: {ans}. Stem is locked — do not rewrite it.")
            result = _lfn(2, params, ph, ans, distractors, None, None, "mcq", ctx, None)
            result["exactStem"] = exact_stem
            if validate_math_object(result):
                continue
            return result

        if variant == "scaled_output":
            sub = "scaled_output"
            m = rng_obj.choice([25, 30, 40, 45, 50, 60])
            b = rng_obj.choice([100, 200, 300, 400, 500, 600])
            xv = rng_obj.choice([20, 25, 30, 40, 50])
            yv = m * xv + b
            params = {"m": m, "b": b, "xv": xv,
                      "tpl": "evaluate_compound", "variant": sub}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(yv)
            distractors = make_distractors(ans, [
                str(m * xv),
                str(m + b + xv),
                str(yv + b),
            ])
            exact_stem = (
                f"A catering company charges a setup fee of ${b} plus ${m} per guest. "
                f"What is the total cost, in dollars, of a catering event for {xv} guests?"
            )
            ctx = (f"LFN d2 evaluate_compound (scaled_output). "
                   f"f(x) = {m}x + {b}; f({xv}) = {yv}. "
                   f"Correct: {ans}. Stem is locked — do not rewrite it.")
            result = _lfn(2, params, ph, ans, distractors, None, None, "mcq", ctx, None)
            result["exactStem"] = exact_stem
            if validate_math_object(result):
                continue
            return result

        # combine_two_fns or coefficient_gather
        m1 = rng_obj.choice([i for i in range(-5, 6) if i != 0])
        b1 = rng_obj.choice([i for i in range(-10, 11) if i != 0])
        m2 = rng_obj.choice([i for i in range(-5, 6) if i != 0])
        b2 = rng_obj.choice([i for i in range(-10, 11) if i != 0])
        xv = rng_obj.randint(2, 6)
        k = rng_obj.choice([3, 4, 5, 7])
        fv = m1 * xv + b1
        gv = m2 * xv + b2
        if variant == "coefficient_gather":
            sub = "coefficient_gather"
            combined = k * fv - gv
        else:
            sub = "combine_two_fns"
            combined = 4 * fv - gv
        if abs(combined) > 100:
            continue
        params = {"m1": m1, "b1": b1, "m2": m2, "b2": b2, "xv": xv,
                  "k": k if sub == "coefficient_gather" else 4,
                  "tpl": "evaluate_compound", "variant": sub}
        ph = param_hash(params)
        if ph in exclude_params:
            continue
        ans = str(combined)
        distractors = make_distractors(ans, [
            str(fv), str(gv),
            str(combined + m1), str(combined - m2),
        ])
        scale_coef = k if sub == "coefficient_gather" else 4
        exact_stem = (
            f"The functions f and g are defined by f(x) = {m1}x + {b1} and g(x) = {m2}x + {b2}. "
            f"What is the value of {scale_coef}f({xv}) \u2212 g({xv})?"
        )
        ctx = (f"LFN d2 evaluate_compound ({sub}). "
               f"f(x) = {m1}x + {b1}, g(x) = {m2}x + {b2}. "
               f"f({xv}) = {fv}, g({xv}) = {gv}. "
               f"{scale_coef}f({xv}) − g({xv}) = {scale_coef*fv} − {gv} = {combined}. "
               f"Correct: {ans}. Stem is locked — do not rewrite it.")
        result = _lfn(2, params, ph, ans, distractors, None, None, "mcq", ctx, None)
        result["exactStem"] = exact_stem
        if validate_math_object(result):
            continue
        return result
    raise RuntimeError("evaluate_compound d2: could not generate unique params")


def _d2_interpret_slope_medium(rng_obj, exclude_params, variant=None):
    """Interpret slope in a medium-difficulty contextual setting.
    Variants: rate_in_formula, rate_from_graph, gas_tank_rate.
    """
    for _ in range(200):
        if variant == "gas_tank_rate":
            sub = "gas_tank_rate"
            b = rng_obj.choice([12, 14, 16, 18, 20])
            m_dec = rng_obj.choice([Rational(1, 25), Rational(1, 20), Rational(1, 30), Rational(3, 100)])
            m_disp = str(float(m_dec))
            params = {"b": b, "m_num": m_dec.numerator, "m_den": m_dec.denominator,
                      "tpl": "interpret_slope_medium", "variant": sub}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = "The number of gallons used per mile"
            distractors = make_distractors(ans, [
                "The initial amount of gasoline, in gallons, in the tank",
                "The total miles driven",
                "The number of miles driven per gallon",
            ])
            exact_stem = (
                f"The function g is defined by g(x) = {b} − {m_disp}x, where g(x) is the gasoline, "
                f"in gallons, remaining in a tank x miles into a trip. Which of the following is the "
                f"best interpretation of −{m_disp} in this context?"
            )
            ctx = (f"LFN d2 interpret_slope_medium (gas_tank_rate). "
                   f"Stem (set verbatim): '{exact_stem}'. "
                   f"−{m_disp} is the consumption rate (gallons per mile). "
                   f"Correct: '{ans}'.")
            result = _lfn(2, params, ph, ans, distractors, None, None, "mcq", ctx, None)
            result["exactStem"] = exact_stem
            if validate_math_object(result):
                continue
            return result

        if variant == "rate_from_graph":
            sub = "rate_from_graph"
            m = rng_obj.choice([20, 25, 30, 35, 40, 45])
            b = rng_obj.choice([20, 30, 40, 50, 60, 75])
            params = {"m": m, "b": b,
                      "tpl": "interpret_slope_medium", "variant": sub}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = f"The hourly rate, in dollars per hour"
            distractors = make_distractors(ans, [
                f"The total charge, in dollars, for 1 hour of work",
                f"The call-out fee, in dollars",
                f"The number of hours included in the flat fee",
            ])
            exact_stem = (
                f"An electrician charges a flat call-out fee plus an hourly rate. The graph of the "
                f"linear function f, where y = f(x), shows the total charge y, in dollars, for x hours "
                f"of work. The graph passes through (0, {b}) and (4, {b + 4*m}). What does the slope "
                f"of this line represent?"
            )
            # No diagram: m ∈ [20,45], b ∈ [20,75] are outside the ±5 coordinate_plane viewport.
            # The exactStem describes the graph via two listed points; no visual needed.
            ctx = (f"LFN d2 interpret_slope_medium (rate_from_graph). "
                   f"Stem (set verbatim): '{exact_stem}'. "
                   f"Slope = (output change)/(input change) = {m} dollars per hour. "
                   f"Correct: '{ans}'.")
            result = _lfn(2, params, ph, ans, distractors, None, None, "mcq", ctx, None)
            result["exactStem"] = exact_stem
            if validate_math_object(result):
                continue
            return result

        # rate_in_formula (default)
        sub = "rate_in_formula"
        m = rng_obj.choice([8, 10, 12, 15, 18, 20, 25])
        b = rng_obj.choice([20, 25, 30, 40, 50, 60, 75])
        if m == b:
            continue
        params = {"m": m, "b": b,
                  "tpl": "interpret_slope_medium", "variant": sub}
        ph = param_hash(params)
        if ph in exclude_params:
            continue
        ans = "The cost per shirt, in dollars"
        distractors = make_distractors(ans, [
            "The total cost, in dollars, of ordering shirts",
            "The number of shirts ordered",
            "The fixed fee, in dollars, charged per order",
        ])
        exact_stem = (
            f"The equation C = {m}n + {b} represents the cost C, in dollars, of ordering n custom "
            f"t-shirts, where n ≥ 1. Which of the following is the best interpretation of {m} in this context?"
        )
        ctx = (f"LFN d2 interpret_slope_medium (rate_in_formula). "
               f"Stem (set verbatim): '{exact_stem}'. "
               f"In C = {m}n + {b}, coefficient {m} is cost per shirt; {b} is fixed fee. "
               f"Correct: '{ans}'.")
        result = _lfn(2, params, ph, ans, distractors, None, None, "mcq", ctx, None)
        result["exactStem"] = exact_stem
        if validate_math_object(result):
            continue
        return result
    raise RuntimeError("interpret_slope_medium d2: could not generate unique params")


def _d2_interpret_intercept_medium(rng_obj, exclude_params, variant=None):
    """Interpret y-intercept in a medium-difficulty context.
    Variants: juice_volume, fabric_relation.
    """
    for _ in range(200):
        if variant == "fabric_relation":
            sub = "fabric_relation"
            m = rng_obj.choice([3, 4, 5, 6, 7, 8])
            b = rng_obj.choice([4, 5, 6, 8, 10, 12])
            params = {"m": m, "b": b,
                      "tpl": "interpret_intercept_medium", "variant": sub}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = "The amount of fabric, in yards, reserved before making any pillows"
            distractors = make_distractors(ans, [
                "The length of fabric, in yards, needed to make one pillow",
                "The total number of pillows that can be made",
                "The fabric used after 6 pillows",
            ])
            exact_stem = (
                f"Kaylani uses fabric according to the equation y − {m}x = {b}, where y represents the "
                f"length of fabric, in yards, and x represents the number of pillows made. Which of the "
                f"following is the best interpretation of {b} in this context?"
            )
            ctx = (f"LFN d2 interpret_intercept_medium (fabric_relation). "
                   f"Stem (set verbatim): '{exact_stem}'. "
                   f"Rearrange: y = {m}x + {b}. At x=0, y={b} yards reserved. "
                   f"Correct: '{ans}'.")
            result = _lfn(2, params, ph, ans, distractors, None, None, "mcq", ctx, None)
            result["exactStem"] = exact_stem
            if validate_math_object(result):
                continue
            return result

        # juice_volume default
        sub = "juice_volume"
        b = rng_obj.choice([120, 150, 180, 200, 240])
        m = rng_obj.choice([8, 10, 12, 15, 16, 20])
        params = {"m": m, "b": b,
                  "tpl": "interpret_intercept_medium", "variant": sub}
        ph = param_hash(params)
        if ph in exclude_params:
            continue
        ans = "The initial volume of juice in the pitcher"
        distractors = make_distractors(ans, [
            "The volume of juice per cup",
            "The maximum number of cups that can be poured",
            f"The volume of juice after {m} cups",
        ])
        exact_stem = (
            f"The function f is defined by f(x) = {b} − {m}x, where f(x) is the volume of juice, "
            f"in fluid ounces, remaining in a pitcher after x cups have been poured. Which of the "
            f"following is the best interpretation of the y-intercept of the graph of y = f(x) in the "
            f"xy-plane?"
        )
        ctx = (f"LFN d2 interpret_intercept_medium (juice_volume). "
               f"Stem (set verbatim): '{exact_stem}'. "
               f"y-intercept = f(0) = {b}, representing initial juice volume. "
               f"Correct: '{ans}'.")
        result = _lfn(2, params, ph, ans, distractors, None, None, "mcq", ctx, None)
        result["exactStem"] = exact_stem
        if validate_math_object(result):
            continue
        return result
    raise RuntimeError("interpret_intercept_medium d2: could not generate unique params")


def _d2_interpret_x_intercept(rng_obj, exclude_params, variant=None):
    """Interpret the x-intercept in a real-world context.
    Variants: time_zero_context, break_even_context.
    """
    for _ in range(200):
        if variant == "break_even_context":
            sub = "break_even_context"
            m = rng_obj.choice([150, 200, 250, 300, 400, 450])
            c_months = rng_obj.choice([6, 9, 12, 15, 18, 24])
            b = -m * c_months
            params = {"m": m, "c": c_months,
                      "tpl": "interpret_x_intercept", "variant": sub}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = "The number of months needed for the business to break even"
            distractors = make_distractors(ans, [
                "The initial startup cost, in dollars",
                f"The monthly profit, in dollars, at month {m}",
                "The total profit, in dollars, over 12 months",
            ])
            exact_stem = (
                f"A new-business owner models monthly profit, in dollars, with the function "
                f"P(m) = {m}m − {abs(b)}, where m is the number of months since opening. The graph of "
                f"y = P(m) crosses the m-axis at (c, 0). What is the best interpretation of c in this context?"
            )
            ctx = (f"LFN d2 interpret_x_intercept (break_even_context). "
                   f"Stem (set verbatim): '{exact_stem}'. "
                   f"x-intercept: P(m) = 0 → m = {c_months}; business breaks even at month {c_months}. "
                   f"Correct: '{ans}'.")
            result = _lfn(2, params, ph, ans, distractors, None, None, "mcq", ctx, None)
            result["exactStem"] = exact_stem
            if validate_math_object(result):
                continue
            return result

        # time_zero_context
        sub = "time_zero_context"
        b = rng_obj.choice([120, 150, 180, 240, 300, 360])
        m = rng_obj.choice([6, 8, 10, 12, 15, 20])
        if b % m != 0:
            continue
        x_empty = b // m
        params = {"m": m, "b": b,
                  "tpl": "interpret_x_intercept", "variant": sub}
        ph = param_hash(params)
        if ph in exclude_params:
            continue
        ans = "The time, in hours, at which the reservoir is empty"
        distractors = make_distractors(ans, [
            f"The initial amount of water, in liters, in the reservoir",
            f"The rate at which water is leaking, in liters per hour",
            f"The total amount of water, in liters, lost in {m} hours",
        ])
        exact_stem = (
            f"The function f is defined by f(x) = {b} − {m}x, where f(x) is the amount of water, "
            f"in liters, remaining in a reservoir x hours after a leak began. In the xy-plane, the "
            f"graph of y = f(x) has an x-intercept at (c, 0). Which of the following is the best "
            f"interpretation of c in this context?"
        )
        ctx = (f"LFN d2 interpret_x_intercept (time_zero_context). "
               f"Stem (set verbatim): '{exact_stem}'. "
               f"x-intercept: 0 = {b} − {m}x → x = {x_empty}; reservoir empty at {x_empty} hours. "
               f"Correct: '{ans}'.")
        result = _lfn(2, params, ph, ans, distractors, None, None, "mcq", ctx, None)
        result["exactStem"] = exact_stem
        if validate_math_object(result):
            continue
        return result
    raise RuntimeError("interpret_x_intercept d2: could not generate unique params")


def _d2_equation_from_two_pts(rng_obj, exclude_params, variant=None):
    """Find the equation given two points or given slope + point.
    Variants: integer_slope, larger_slope, from_slope_and_point, negative_slope_decreasing.
    """
    for _ in range(200):
        if variant == "from_slope_and_point":
            sub = "from_slope_and_point"
            m = rng_obj.choice([i for i in range(-5, 6) if i not in (0, 1, -1)])
            x0 = rng_obj.choice([i for i in range(-5, 6) if i != 0])
            y0 = rng_obj.choice([i for i in range(-10, 11) if i != 0])
            b = y0 - m * x0
            params = {"m": m, "x0": x0, "y0": y0,
                      "tpl": "equation_from_two_pts", "variant": sub}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = fmt_fn(m, b)
            distractors = make_distractors(ans, [
                fmt_fn(m, y0),
                fmt_fn(m, b + 1),
                fmt_fn(-m, b),
            ])
            exact_stem = (
                f"A line has slope {m} and passes through ({x0}, {y0}). "
                f"Which equation represents this line?"
            )
            ctx = (f"LFN d2 equation_from_two_pts (from_slope_and_point). "
                   f"Slope {m}, through ({x0}, {y0}): b = {y0} - {m}({x0}) = {b}. "
                   f"Equation: {ans}. "
                   f"CRITICAL — use exactStem verbatim; do NOT alter ({x0}, {y0}) or slope {m}.")
            result = _lfn(2, params, ph, ans, distractors, None, None, "mcq", ctx, None)
            result["exactStem"] = exact_stem
            if validate_math_object(result):
                continue
            return result

        if variant == "negative_slope_decreasing":
            sub = "negative_slope_decreasing"
            # Force negative slope between two points
            x1 = rng_obj.randint(1, 6)
            x2 = x1 + rng_obj.randint(1, 4)
            m = rng_obj.choice([-2, -3, -4, -5])
            y1 = rng_obj.randint(5, 25)
            y2 = y1 + m * (x2 - x1)
            b = y1 - m * x1
            params = {"x1": x1, "y1": y1, "x2": x2, "y2": y2,
                      "tpl": "equation_from_two_pts", "variant": sub}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = fmt_fn(m, b)
            distractors = make_distractors(ans, [
                fmt_fn(-m, b),
                fmt_fn(m, y1),
                fmt_fn(m, b + 1),
            ])
            exact_stem = (
                f"The function h is linear, with h({x1}) = {y1} and h({x2}) = {y2}. "
                f"Which of the following defines h(x)?"
            )
            ctx = (f"LFN d2 equation_from_two_pts (negative_slope_decreasing). "
                   f"Points ({x1}, {y1}) and ({x2}, {y2}). Slope = ({y2}-{y1})/({x2}-{x1}) = {m}. "
                   f"Intercept b = {b}. Equation: {ans}. "
                   f"CRITICAL — use exactStem verbatim; do NOT alter h({x1})={y1} or h({x2})={y2}.")
            result = _lfn(2, params, ph, ans, distractors, None, None, "mcq", ctx, None)
            result["exactStem"] = exact_stem
            if validate_math_object(result):
                continue
            return result

        # integer_slope or larger_slope
        x1 = 0
        x2 = rng_obj.choice([2, 4, 5, 6, 8, 10])
        y1 = rng_obj.choice([i for i in range(-10, 11) if i != 0])
        if variant == "larger_slope":
            sub = "larger_slope"
            m = rng_obj.choice([3, 4, 5, 6, 7, 8])
        else:
            sub = "integer_slope"
            m = rng_obj.choice([2, 3, 4])
        y2 = y1 + m * x2
        params = {"x2": x2, "y1": y1, "y2": y2,
                  "tpl": "equation_from_two_pts", "variant": sub}
        ph = param_hash(params)
        if ph in exclude_params:
            continue
        ans = fmt_fn(m, y1)
        distractors = make_distractors(ans, [
            fmt_fn(y1, m),
            fmt_fn(1, y2 - y1),
            fmt_fn(y2 - y1, x2),
        ])
        exact_stem = (
            f"A line in the xy-plane passes through (0, {y1}) and ({x2}, {y2}). "
            f"Which equation represents this line?"
        )
        ctx = (f"LFN d2 equation_from_two_pts ({sub}). "
               f"Line through (0, {y1}) and ({x2}, {y2}). "
               f"Slope = ({y2}-{y1})/({x2}-0) = {m}. Intercept = {y1}. "
               f"Equation: {ans}. "
               f"CRITICAL — use exactStem verbatim; do NOT alter (0,{y1}) or ({x2},{y2}).")
        result = _lfn(2, params, ph, ans, distractors, None, None, "mcq", ctx, None)
        result["exactStem"] = exact_stem
        if validate_math_object(result):
            continue
        return result
    raise RuntimeError("equation_from_two_pts d2: could not generate unique params")


def _d2_coefficient_from_table(rng_obj, exclude_params, variant=None):
    """Given a table and a partial function, find the missing constant.
    Variants: find_m, find_b, two_unknowns.
    """
    for _ in range(200):
        if variant == "two_unknowns":
            sub = "two_unknowns"
            a = rng_obj.choice([2, 3, 4, 5])
            b = rng_obj.choice([i for i in range(-6, 7) if i != 0])
            x1 = 1
            x2 = rng_obj.choice([2, 3, 4, 5])
            g1 = a * x1 + b
            g2 = a * x2 + b
            ans_val = a + b
            params = {"a": a, "b": b, "x1": x1, "x2": x2,
                      "tpl": "coefficient_from_table", "variant": sub}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(ans_val)
            distractors = make_distractors(ans, [
                str(a), str(b), str(g1 + g2), str(ans_val + 1),
            ])
            exact_stem = (
                f"The function g is defined by g(x) = ax + b, where a and b are constants. "
                f"The table shows g({x1}) = {g1} and g({x2}) = {g2}. What is the value of a + b?"
            )
            ctx = (f"LFN d2 coefficient_from_table (two_unknowns). "
                   f"g(x) = ax + b; g({x1})={g1}, g({x2})={g2}. "
                   f"Slope a = ({g2}-{g1})/({x2}-{x1}) = {a}; b = {g1} - {a}*{x1} = {b}. "
                   f"a + b = {ans_val}. "
                   f"CRITICAL — use exactStem verbatim; do NOT alter g({x1})={g1} or g({x2})={g2}.")
            result = _lfn(2, params, ph, ans, distractors, None, None, "mcq", ctx, None)
            result["exactStem"] = exact_stem
            if validate_math_object(result):
                continue
            return result

        if variant == "find_b":
            sub = "find_b"
            m = rng_obj.choice([3, 4, 5, 6, 7, 8])
            x_in = rng_obj.randint(2, 8)
            b_ans = rng_obj.choice([i for i in range(-10, 11) if i != 0])
            y_out = m * x_in + b_ans
            params = {"m": m, "x_in": x_in, "y_out": y_out,
                      "tpl": "coefficient_from_table", "variant": sub}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(b_ans)
            sm, sx = spr_bounds(ans)
            exact_stem = (
                f"The function g is defined by g(x) = {m}x + b, where b is a constant. "
                f"The table shows g({x_in}) = {y_out}. What is the value of b?"
            )
            ctx = (f"LFN d2 coefficient_from_table (find_b). "
                   f"g(x) = {m}x + b; g({x_in}) = {y_out}. "
                   f"{y_out} = {m}({x_in}) + b → b = {b_ans}. "
                   f"Correct: {ans}. Stem is locked — do not rewrite it.")
            result = _lfn(2, params, ph, ans, [], sm, sx, "spr", ctx, None)
            result["exactStem"] = exact_stem
            if validate_math_object(result):
                continue
            return result

        # find_m (default)
        sub = "find_m"
        m_ans = rng_obj.choice([6, 7, 8, 9, 11, 12, 13, 14])
        b_fixed = rng_obj.choice([i for i in range(-40, 41, 4) if i != 0])
        x_start = rng_obj.choice([5, 10, 15, 20])
        x_step = rng_obj.choice([2, 3, 4, 5])
        xs = [x_start, x_start + x_step, x_start + 2*x_step, x_start + 3*x_step]
        fxs = [m_ans * v + b_fixed for v in xs]
        params = {"m": m_ans, "b": b_fixed, "x_start": x_start, "x_step": x_step,
                  "tpl": "coefficient_from_table", "variant": sub}
        ph = param_hash(params)
        if ph in exclude_params:
            continue
        ans = str(m_ans)
        sm, sx = spr_bounds(ans)
        exact_stem = (
            f"The function f is defined by f(x) = mx + {b_fixed}, where m is a constant. "
            f"The table shows selected values: f({xs[0]}) = {fxs[0]}, f({xs[1]}) = {fxs[1]}, "
            f"f({xs[2]}) = {fxs[2]}, f({xs[3]}) = {fxs[3]}. What is the value of m?"
        )
        ctx = (f"LFN d2 coefficient_from_table (find_m). "
               f"f(x) = mx + ({b_fixed}); table: "
               f"({xs[0]},{fxs[0]}), ({xs[1]},{fxs[1]}), ({xs[2]},{fxs[2]}), ({xs[3]},{fxs[3]}). "
               f"m = ({fxs[1]}-{fxs[0]})/({xs[1]}-{xs[0]}) = {m_ans}. "
               f"Correct: {ans} (SPR). "
               f"CRITICAL — use exactStem verbatim; all 4 table values must appear exactly as given.")
        result = _lfn(2, params, ph, ans, [], sm, sx, "spr", ctx, None)
        result["exactStem"] = exact_stem
        if validate_math_object(result):
            continue
        return result
    raise RuntimeError("coefficient_from_table d2: could not generate unique params")


def _d2_parameter_solve_simple(rng_obj, exclude_params, variant=None):
    """Given function with one unknown parameter and one data point, solve.
    Variants: solve_m, solve_b, inverse_then_solve.
    """
    for _ in range(200):
        if variant == "inverse_then_solve":
            sub = "inverse_then_solve"
            den = rng_obj.choice([3, 4, 5, 6])
            shift = rng_obj.choice([10, 12, 15, 18, 20])
            target = rng_obj.choice([8, 10, 12, 15])
            a = den * target - shift
            if a <= 0:
                continue
            params = {"den": den, "shift": shift, "target": target,
                      "tpl": "parameter_solve_simple", "variant": sub}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(a)
            sm, sx = spr_bounds(ans)
            exact_stem = (
                f"The function f is defined by f(x) = (x + {shift})/{den}. "
                f"If f(a) = {target}, what is the value of a?"
            )
            ctx = (f"LFN d2 parameter_solve_simple (inverse_then_solve). "
                   f"f(x) = (x + {shift})/{den}; f(a) = {target} → a + {shift} = {den*target} → a = {a}. "
                   f"Correct: {ans}. "
                   f"CRITICAL — use exactStem verbatim. The function is (x + {shift}) DIVIDED BY {den}, "
                   f"NOT {den}x + {shift}. Do NOT rewrite as a product.")
            result = _lfn(2, params, ph, ans, [], sm, sx, "spr", ctx, None)
            result["exactStem"] = exact_stem
            if validate_math_object(result):
                continue
            return result

        if variant == "solve_b":
            sub = "solve_b"
            m = 1
            b_ans = rng_obj.choice([i for i in range(-40, 41, 5) if i != 0])
            params = {"b_ans": b_ans,
                      "tpl": "parameter_solve_simple", "variant": sub}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(b_ans)
            distractors = make_distractors(ans, [
                "0", "1", str(b_ans + 1),
            ])
            exact_stem = (
                f"The linear function h is defined by h(x) = x + b, where b is a constant. "
                f"If h(0) = {b_ans}, what is the value of b?"
            )
            ctx = (f"LFN d2 parameter_solve_simple (solve_b). "
                   f"h(x) = x + b; h(0) = {b_ans} → b = {b_ans}. "
                   f"Correct: {ans}. "
                   f"CRITICAL — use exactStem verbatim; h(0) = {b_ans}.")
            result = _lfn(2, params, ph, ans, distractors, None, None, "mcq", ctx, None)
            result["exactStem"] = exact_stem
            if validate_math_object(result):
                continue
            return result

        # solve_m (default)
        sub = "solve_m"
        m_ans = rng_obj.choice([2, 3, 4, 5, 6, 7, 8])
        b_fixed = rng_obj.choice([i for i in range(-12, 13) if i != 0])
        x_in = rng_obj.choice([3, 4, 5, 6, 7, 8, 9])
        y_out = m_ans * x_in + b_fixed
        params = {"m_ans": m_ans, "b": b_fixed, "x_in": x_in,
                  "tpl": "parameter_solve_simple", "variant": sub}
        ph = param_hash(params)
        if ph in exclude_params:
            continue
        ans = str(m_ans)
        sm, sx = spr_bounds(ans)
        exact_stem = (
            f"The function f is defined by f(x) = mx + {b_fixed}, where m is a constant. "
            f"If f({x_in}) = {y_out}, what is the value of m?"
        )
        ctx = (f"LFN d2 parameter_solve_simple (solve_m). "
               f"f(x) = mx + {b_fixed}; f({x_in}) = {y_out}. "
               f"{y_out} = {x_in}m + {b_fixed} → m = {m_ans}. "
               f"Correct: {ans}. "
               f"CRITICAL — use exactStem verbatim; f({x_in}) = {y_out}.")
        result = _lfn(2, params, ph, ans, [], sm, sx, "spr", ctx, None)
        result["exactStem"] = exact_stem
        if validate_math_object(result):
            continue
        return result
    raise RuntimeError("parameter_solve_simple d2: could not generate unique params")


def _d2_linear_model_word_solve(rng_obj, exclude_params, variant=None):
    """Word-problem linear model; set up and solve.
    Variants: forward_interp, specific_input, acceleration_like, savings_balance.
    """
    for _ in range(200):
        if variant == "savings_balance":
            sub = "savings_balance"
            base = rng_obj.choice([400, 500, 600, 700, 800])
            rate = rng_obj.choice([20, 25, 30, 35, 40, 50])
            weeks = rng_obj.choice([3, 4, 5, 6, 8])
            balance = base + rate * weeks
            params = {"base": base, "rate": rate, "weeks": weeks,
                      "tpl": "linear_model_word_solve", "variant": sub}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(balance)
            sm, sx = spr_bounds(ans)
            exact_stem = (
                f"Someone deposits ${rate} into a savings account each week. "
                f"The starting balance was ${base}. "
                f"What is the balance, in dollars, at the end of week {weeks}?"
            )
            ctx = (f"LFN d2 linear_model_word_solve (savings_balance). "
                   f"Balance = {base} + {rate}*{weeks} = {balance}. "
                   f"Correct: {ans}. SPR. "
                   f"CRITICAL — use exactStem verbatim; starting balance is ${base}, weekly rate is ${rate}.")
            result = _lfn(2, params, ph, ans, [], sm, sx, "spr", ctx, None)
            result["exactStem"] = exact_stem
            if validate_math_object(result):
                continue
            return result

        if variant == "acceleration_like":
            sub = "acceleration_like"
            base = rng_obj.choice([30, 40, 50, 60])
            rate = rng_obj.choice([3, 4, 5, 6, 8])
            tv = rng_obj.choice([3, 5, 7, 9, 10])
            speed = base + rate * tv
            params = {"base": base, "rate": rate, "tv": tv,
                      "tpl": "linear_model_word_solve", "variant": sub}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(speed)
            distractors = make_distractors(ans, [
                str(base), str(rate * tv),
                str(base - rate * tv), str(speed + rate),
            ])
            exact_stem = (
                f"The function s defined by s = {base} + {rate}t gives a vehicle's speed, "
                f"in miles per hour, t seconds after it began accelerating. "
                f"What is the speed of the vehicle at t = {tv}?"
            )
            ctx = (f"LFN d2 linear_model_word_solve (acceleration_like). "
                   f"s = {base} + {rate}t; at t={tv}: s = {speed}. "
                   f"Correct: {ans}. Stem is locked — do not rewrite it.")
            result = _lfn(2, params, ph, ans, distractors, None, None, "mcq", ctx, None)
            result["exactStem"] = exact_stem
            if validate_math_object(result):
                continue
            return result

        if variant == "specific_input":
            sub = "specific_input"
            rate = rng_obj.choice([20, 25, 30, 40, 50, 60])
            tv = rng_obj.choice([2, 3, 4, 5])
            dist = rate * tv
            params = {"rate": rate, "tv": tv,
                      "tpl": "linear_model_word_solve", "variant": sub}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(dist)
            distractors = make_distractors(ans, [
                str(rate // tv), str(rate), str(dist + rate),
            ])
            exact_stem = (
                f"A bus travels at a constant speed given by d = {rate}t, where d is "
                f"the distance traveled in feet and t is the time in seconds since it began moving. "
                f"What is the distance traveled, in feet, after {tv} seconds?"
            )
            ctx = (f"LFN d2 linear_model_word_solve (specific_input). "
                   f"d = {rate}t; at t = {tv}: d = {dist}. "
                   f"Correct: {ans}. Stem is locked — do not rewrite it.")
            result = _lfn(2, params, ph, ans, distractors, None, None, "mcq", ctx, None)
            result["exactStem"] = exact_stem
            if validate_math_object(result):
                continue
            return result

        # forward_interp (default)
        sub = "forward_interp"
        base = rng_obj.choice([300, 400, 500, 600, 800, 1000])
        rate = rng_obj.choice([25, 30, 35, 40, 50])
        t_ans = rng_obj.choice([6, 8, 10, 11, 12, 15])
        total = base + rate * t_ans
        params = {"base": base, "rate": rate, "t_ans": t_ans,
                  "tpl": "linear_model_word_solve", "variant": sub}
        ph = param_hash(params)
        if ph in exclude_params:
            continue
        ans = str(t_ans)
        sm, sx = spr_bounds(ans)
        exact_stem = (
            f"A reservoir holds an initial {base} gallons of water. Starting at time t = 0 hours, "
            f"water flows in at a constant rate of {rate} gallons per hour. "
            f"After how many hours will the reservoir contain {total} gallons?"
        )
        ctx = (f"LFN d2 linear_model_word_solve (forward_interp). "
               f"V = {base} + {rate}t = {total} → t = {t_ans}. "
               f"Correct: {ans}. SPR. "
               f"CRITICAL — use exactStem verbatim; initial={base}, rate={rate}, total={total}. "
               f"Do NOT alter any of these three values.")
        result = _lfn(2, params, ph, ans, [], sm, sx, "spr", ctx, None)
        result["exactStem"] = exact_stem
        if validate_math_object(result):
            continue
        return result
    raise RuntimeError("linear_model_word_solve d2: could not generate unique params")


def _d2_graph_intercept_computed(rng_obj, exclude_params, variant=None):
    """Compute intercept(s) requiring algebra.
    Variants: sum_of_intercepts, intercept_after_shift.
    """
    for _ in range(200):
        if variant == "intercept_after_shift":
            sub = "intercept_after_shift"
            m = rng_obj.choice([1, 2, 3, -2, -3])
            # Shifted graph: y = f(x) - k. So shifted y-int = f(0) - k = b - k.
            k = rng_obj.choice([6, 8, 10, 11, 12, 14])
            b = rng_obj.choice([i for i in range(-5, 6) if i != 0])
            # Visible y-intercept on shifted graph:
            vis_int = b - k
            # f(x) answer would be mx + b; given shifted graph shows y = mx + (b-k) passing through certain pts
            params = {"m": m, "k": k, "b": b,
                      "tpl": "graph_intercept_computed", "variant": sub}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = fmt_fn(m, b)
            distractors = make_distractors(ans, [
                fmt_fn(m, vis_int),
                fmt_fn(m, b + k),
                fmt_fn(m, -b),
            ])
            exact_stem = (
                f"In the xy-plane, the graph of y = f(x) \u2212 {k} has slope {m} "
                f"and y-intercept {vis_int}. Which of the following defines f(x)?"
            )
            ctx = (f"LFN d2 graph_intercept_computed (intercept_after_shift). "
                   f"Shifted graph y = f(x) − {k} has y-intercept {vis_int}; f(0) = {vis_int} + {k} = {b}. "
                   f"f(x) = {m}x + {b}. Correct: {ans}. Stem is locked — do not rewrite it.")
            result = _lfn(2, params, ph, ans, distractors, None, None, "mcq", ctx, None)
            result["exactStem"] = exact_stem
            if validate_math_object(result):
                continue
            return result

        # sum_of_intercepts
        sub = "sum_of_intercepts"
        m = rng_obj.choice([i for i in range(-8, 9) if i not in (0, 1, -1)])
        b = rng_obj.choice([i for i in range(-84, 85, 7) if i != 0])
        if b % m != 0:
            continue
        x_int = -b // m
        if abs(x_int) > 30 or abs(b) > 100:
            continue
        ans_val = x_int + b
        params = {"m": m, "b": b,
                  "tpl": "graph_intercept_computed", "variant": sub}
        ph = param_hash(params)
        if ph in exclude_params:
            continue
        ans = str(ans_val)
        sm, sx = spr_bounds(ans)
        exact_stem = (
            f"The function f is defined by f(x) = {m}x + {b}. In the xy-plane, the graph of "
            f"y = f(x) has an x-intercept and a y-intercept. What is the sum of the x-coordinate "
            f"of the x-intercept and the y-coordinate of the y-intercept?"
        )
        ctx = (f"LFN d2 graph_intercept_computed (sum_of_intercepts). "
               f"f(x) = {m}x + {b}. y-intercept y-coord: {b}; x-intercept x-coord: {x_int}. "
               f"Sum: {x_int} + {b} = {ans_val}. "
               f"Correct: {ans}. SPR. Stem is locked — do not rewrite it.")
        result = _lfn(2, params, ph, ans, [], sm, sx, "spr", ctx, None)
        result["exactStem"] = exact_stem
        if validate_math_object(result):
            continue
        return result
    raise RuntimeError("graph_intercept_computed d2: could not generate unique params")


def _d2_parallel_slope_from_fn(rng_obj, exclude_params, variant=None):
    """Slope of a line parallel to a given linear function.
    Variants: parallel_to_linear_fn.
    """
    for _ in range(200):
        sub = "parallel_to_linear_fn"
        m = rng_obj.choice([i for i in range(-8, 9) if i not in (0, 1, -1)])
        b = rng_obj.choice([i for i in range(-10, 11) if i != 0])
        params = {"m": m, "b": b,
                  "tpl": "parallel_slope_from_fn", "variant": sub}
        ph = param_hash(params)
        if ph in exclude_params:
            continue
        ans = str(m)
        sm, sx = spr_bounds(ans)
        exact_stem = (
            f"The function f is defined by f(x) = {m}x + {b}. "
            f"In the xy-plane, line j is parallel to the graph of y = f(x). "
            f"What is the slope of line j?"
        )
        ctx = (f"LFN d2 parallel_slope_from_fn (parallel_to_linear_fn). "
               f"f(x) = {m}x + {b}, slope {m}. Parallel lines have equal slopes. "
               f"Correct: {ans}. SPR. "
               f"CRITICAL — use 'line j' (not a function g). Do NOT add g(0) or any extra condition. "
               f"Stem is locked — do not rewrite it.")
        result = _lfn(2, params, ph, ans, [], sm, sx, "spr", ctx, None)
        result["exactStem"] = exact_stem
        if validate_math_object(result):
            continue
        return result
    raise RuntimeError("parallel_slope_from_fn d2: could not generate unique params")


def _d3_parameter_solve_compound(rng_obj, exclude_params, variant=None):
    """Hard parameter-solve then evaluate/interpret.
    Variants: double_param, expr_input, implicit_b, table_derived.
    """
    for _ in range(200):
        if variant == "expr_input":
            sub = "expr_input"
            # f(cx) = x - s; find c given f(p) = q
            s = rng_obj.choice([5, 6, 7, 8, 10, 12])
            p = rng_obj.choice([10, 12, 14, 15, 18, 20])
            q = rng_obj.choice([20, 25, 30, 35, 40])
            # x - s = q → x = q + s; and cx = p → c = p/(q+s)
            x_derived = q + s
            if x_derived <= 0 or _math.gcd(p, x_derived) == x_derived:
                continue
            params = {"s": s, "p": p, "q": q,
                      "tpl": "parameter_solve_compound", "variant": sub}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = f"{p}/{x_derived}"
            distractors = make_distractors(ans, [
                f"{x_derived}/{p}",
                f"{p}/{q}",
                f"{q}/{p}",
            ])
            exact_stem = (
                f"The function f is defined by f(cx) = x \u2212 {s}, where c is a constant. "
                f"If f({p}) = {q}, what is the value of c?"
            )
            ctx = (f"LFN d3 parameter_solve_compound (expr_input). "
                   f"f(cx) = x - {s}; f({p}) = {q} → x = {x_derived}; cx = {p} → c = {p}/{x_derived}. "
                   f"Correct: {ans}. Stem is locked — do not rewrite it.")
            result = _lfn(3, params, ph, ans, distractors, None, None, "mcq", ctx, None)
            result["exactStem"] = exact_stem
            if validate_math_object(result):
                continue
            return result

        if variant == "implicit_b":
            sub = "implicit_b"
            # g(x) = b - 15x; g(c+7) = c/4; solve b in terms of c
            m_rate = rng_obj.choice([12, 15, 18])
            offset = rng_obj.choice([5, 6, 7, 8])
            frac_den = rng_obj.choice([3, 4, 5])
            params = {"m_rate": m_rate, "offset": offset, "frac_den": frac_den,
                      "tpl": "parameter_solve_compound", "variant": sub}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            # g(c+offset) = b - m_rate(c+offset) = b - m_rate·c - m_rate·offset
            # Set equal to c/frac_den: b = c/frac_den + m_rate·c + m_rate·offset
            #                          = (m_rate·frac_den·c + c)/frac_den + m_rate·offset
            #                          = ((m_rate·frac_den + 1)c)/frac_den + m_rate·offset
            num = m_rate * frac_den + 1
            const = m_rate * offset
            ans = f"b = {num}c/{frac_den} + {const}"
            d1 = f"b = c/{frac_den} + {m_rate}c + {const}"
            d2 = f"b = {num}c/{frac_den} − {const}"
            d3 = f"b = {m_rate}c + {offset}"
            distractors = make_distractors(ans, [d1, d2, d3])
            exact_stem = (
                f"The function g is defined by g(x) = b \u2212 {m_rate}x, where b is a constant. "
                f"If g(c + {offset}) = c/{frac_den}, what is b in terms of c?"
            )
            ctx = (f"LFN d3 parameter_solve_compound (implicit_b). "
                   f"g(x) = b − {m_rate}x; g(c+{offset}) = c/{frac_den}. "
                   f"Expand: b − {m_rate}·c − {m_rate}·{offset} = c/{frac_den}. "
                   f"Solve for b: b = c/{frac_den} + {m_rate}c + {const} = {num}c/{frac_den} + {const}. "
                   f"Correct: {ans}. Stem is locked — do not rewrite it.")
            result = _lfn(3, params, ph, ans, distractors, None, None, "mcq", ctx, None)
            result["exactStem"] = exact_stem
            if validate_math_object(result):
                continue
            return result

        if variant == "table_derived":
            sub = "table_derived"
            m = rng_obj.choice([3, 4, 5, 6, 7])
            b = rng_obj.choice([i for i in range(-10, 11) if i != 0])
            x1 = rng_obj.randint(2, 5)
            x2 = x1 + rng_obj.randint(2, 5)
            f_x1 = m * x1 + b
            f_x2 = m * x2 + b
            shift = rng_obj.choice([10, 12, 14, 15, 20])
            x_eval = rng_obj.choice([8, 10, 12])
            h_val = m * x_eval + b - shift
            if abs(h_val) > 80:
                continue
            params = {"m": m, "b": b, "x1": x1, "x2": x2, "shift": shift, "x_eval": x_eval,
                      "tpl": "parameter_solve_compound", "variant": sub}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(h_val)
            sm, sx = spr_bounds(ans)
            exact_stem = (
                f"The function f is linear. The table shows two values: f({x1}) = {f_x1} and "
                f"f({x2}) = {f_x2}. If h(x) = f(x) - {shift}, what is the value of h({x_eval})?"
            )
            ctx = (f"LFN d3 parameter_solve_compound (table_derived). "
                   f"From table: f({x1})={f_x1}, f({x2})={f_x2}. Slope m = ({f_x2}-{f_x1})/({x2}-{x1}) = {m}; "
                   f"b = {f_x1} - {m}*{x1} = {b}; f(x) = {m}x + {b}. "
                   f"h(x) = f(x) - {shift} (subtracts {shift}; NOT an upward shift). "
                   f"h({x_eval}) = ({m*x_eval + b}) - {shift} = {h_val}. "
                   f"Correct: {ans}. SPR. "
                   f"CRITICAL — use the exactStem verbatim; do NOT rewrite as 'vertical shift upward'.")
            result = _lfn(3, params, ph, ans, [], sm, sx, "spr", ctx, None)
            result["exactStem"] = exact_stem
            if validate_math_object(result):
                continue
            return result

        # double_param (default)
        sub = "double_param"
        m_fixed = rng_obj.choice([3, 4, 5, 6])
        k = rng_obj.choice([2, 3, 4, 5])
        x_known = rng_obj.choice([4, 5, 6, 8])
        x_target = rng_obj.choice([10, 12, 15])
        if x_target == x_known:
            continue
        # f(x) = m_fixed * x + k * (x - 1). f(x_known) given, find f(x_target).
        f_known = m_fixed * x_known + k * (x_known - 1)
        f_target = m_fixed * x_target + k * (x_target - 1)
        params = {"m_fixed": m_fixed, "k": k, "x_known": x_known, "x_target": x_target,
                  "tpl": "parameter_solve_compound", "variant": sub}
        ph = param_hash(params)
        if ph in exclude_params:
            continue
        ans = str(f_target)
        sm, sx = spr_bounds(ans)
        exact_stem = (
            f"The function f is defined by f(x) = {m_fixed}x + k(x - 1), where k is a constant. "
            f"If f({x_known}) = {f_known}, what is the value of f({x_target})?"
        )
        ctx = (f"LFN d3 parameter_solve_compound (double_param). "
               f"f(x) = {m_fixed}x + k(x-1); given f({x_known}) = {f_known}: "
               f"{m_fixed*x_known} + k*{x_known - 1} = {f_known}, so k = {k}. "
               f"f({x_target}) = {m_fixed*x_target} + {k}*{x_target - 1} = {f_target}. "
               f"Correct: {ans}. SPR. "
               f"CRITICAL — k is the UNKNOWN in the stem; do NOT substitute k={k} into the function definition. "
               f"Use the exactStem verbatim.")
        result = _lfn(3, params, ph, ans, [], sm, sx, "spr", ctx, None)
        result["exactStem"] = exact_stem
        if validate_math_object(result):
            continue
        return result
    raise RuntimeError("parameter_solve_compound d3: could not generate unique params")


def _d3_word_model_multistep(rng_obj, exclude_params, variant=None):
    """Multi-step word-problem linear models.
    Variants: flat_plus_daily, tiered_rate, coverage_double.
    """
    for _ in range(200):
        if variant == "coverage_double":
            sub = "coverage_double"
            cov = rng_obj.choice([170, 200, 220, 250, 300])
            area = rng_obj.choice([2, 3, 4, 5, 6]) * cov
            gallons = 2 * area // cov
            params = {"cov": cov, "area": area,
                      "tpl": "word_model_multistep", "variant": sub}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(gallons)
            sm, sx = spr_bounds(ans)
            exact_stem = (
                f"One gallon of paint covers {cov} square feet of wall, and a double coat is to be applied. "
                f"How many gallons are needed to double-coat a wall that is {area} square feet?"
            )
            ctx = (f"LFN d3 word_model_multistep (coverage_double). "
                   f"One gallon covers {cov} sq ft; wall is {area} sq ft; double coat doubles area. "
                   f"Gallons = 2·{area}/{cov} = {gallons}. "
                   f"Correct: {ans}. SPR. Stem is locked — do not rewrite it.")
            result = _lfn(3, params, ph, ans, [], sm, sx, "spr", ctx, None)
            result["exactStem"] = exact_stem
            if validate_math_object(result):
                continue
            return result

        if variant == "tiered_rate":
            sub = "tiered_rate"
            sc = rng_obj.choice(_LFN_TIERED_SCENARIOS)
            item, first_unit, rest_unit = sc
            first = rng_obj.choice([200, 250, 270, 300])
            rest = rng_obj.choice([100, 120, 135, 150])
            if first <= rest:
                continue
            # y = first + rest(x - 1) = rest·x + (first - rest)
            intercept = first - rest
            params = {"first": first, "rest": rest, "sc_idx": _LFN_TIERED_SCENARIOS.index(sc),
                      "tpl": "word_model_multistep", "variant": sub}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = f"y = {rest}x + {intercept}"
            distractors = make_distractors(ans, [
                f"y = {first}x − {rest}",
                f"y = {first}x + {rest}",
                f"y = {rest}x + {first}",
            ])
            exact_stem = (
                f"The cost of renting a {item} is ${first} for the {first_unit} and ${rest} for "
                f"{rest_unit}. Which equation gives the cost y, in dollars, of renting the {item} "
                f"for x days, where x is a positive integer?"
            )
            ctx = (f"LFN d3 word_model_multistep (tiered_rate). "
                   f"Stem (set verbatim): '{exact_stem}'. "
                   f"y = {first} + {rest}(x − 1) = {rest}x + {intercept}. "
                   f"Correct: {ans}.")
            result = _lfn(3, params, ph, ans, distractors, None, None, "mcq", ctx, None)
            result["exactStem"] = exact_stem
            if validate_math_object(result):
                continue
            return result

        # flat_plus_daily
        sub = "flat_plus_daily"
        flat = rng_obj.choice([40, 50, 60, 75, 80, 100])
        rate = rng_obj.choice([20, 25, 30, 35, 40, 50])
        hours = rng_obj.choice([2, 3, 4, 5, 6])
        total = flat + rate * hours
        params = {"flat": flat, "rate": rate, "hours": hours,
                  "tpl": "word_model_multistep", "variant": sub}
        ph = param_hash(params)
        if ph in exclude_params:
            continue
        ans = str(hours)
        distractors = make_distractors(ans, [
            str(total // rate),
            str(hours + 1),
            str(hours - 1) if hours > 1 else str(hours + 2),
        ])
        exact_stem = (
            f"A service charges a flat fee of ${flat} plus ${rate} per hour worked. "
            f"If the total charge was ${total}, for how many hours did the service run?"
        )
        ctx = (f"LFN d3 word_model_multistep (flat_plus_daily). "
               f"Cost = {flat} + {rate}h = {total} → h = {hours}. "
               f"Correct: {ans}. Stem is locked — do not rewrite it.")
        result = _lfn(3, params, ph, ans, distractors, None, None, "mcq", ctx, None)
        result["exactStem"] = exact_stem
        if validate_math_object(result):
            continue
        return result
    raise RuntimeError("word_model_multistep d3: could not generate unique params")


def _d3_linear_model_three_pts_hard(rng_obj, exclude_params, variant=None):
    """Three-data-point linear models; find unknown 3rd point.
    Variants: interpolate, extrapolate, window_repair.
    """
    for _ in range(200):
        if variant == "window_repair":
            sub = "window_repair"
            # 2 data points give (hours, cost); ask for 3rd
            rate = rng_obj.choice([30, 35, 40, 45, 50])
            fixed = rng_obj.choice([50, 60, 70, 80, 100])
            h1 = rng_obj.choice([2, 3])
            h2 = h1 + rng_obj.choice([2, 3])
            h3 = h2 + rng_obj.choice([2, 3, 4])
            c1 = rate * h1 + fixed
            c2 = rate * h2 + fixed
            c3 = rate * h3 + fixed
            params = {"rate": rate, "fixed": fixed, "h1": h1, "h2": h2, "h3": h3,
                      "tpl": "linear_model_three_pts_hard", "variant": sub}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(c3)
            sm, sx = spr_bounds(ans)
            exact_stem = (
                f"A repair company charges a fixed trip fee plus an hourly labor rate. "
                f"A {h1}-hour job cost ${c1}, and a {h2}-hour job cost ${c2}. "
                f"What will a {h3}-hour job cost, in dollars?"
            )
            ctx = (f"LFN d3 linear_model_three_pts_hard (window_repair). "
                   f"From (h, c): ({h1}, {c1}) and ({h2}, {c2}); slope = ({c2-c1})/({h2-h1}) = {rate}; "
                   f"fixed = {c1} - {rate}*{h1} = {fixed}. For h={h3}: cost = {rate}*{h3} + {fixed} = {c3}. "
                   f"Correct: {ans}. SPR. "
                   f"CRITICAL — use exactStem verbatim; data points are (${c1}, {h1}h) and (${c2}, {h2}h), do NOT alter.")
            result = _lfn(3, params, ph, ans, [], sm, sx, "spr", ctx, None)
            result["exactStem"] = exact_stem
            if validate_math_object(result):
                continue
            return result

        if variant == "extrapolate":
            sub = "extrapolate"
            # P(0) = 1, P(10) = 2, extrapolate to 33 → 4.3
            # More general: surface pressure p_surface, per-meter rate r, depth d_target
            p_surface = rng_obj.choice([1, 2])
            r_num = rng_obj.choice([1, 2, 3])
            r_den = rng_obj.choice([10, 20])
            d_ref = r_den  # depth at which pressure ≈ surface + 1
            d_target = rng_obj.choice([20, 25, 30, 33, 40, 50])
            if d_target == d_ref:
                continue
            p_target = p_surface + (r_num * d_target) / r_den
            params = {"p_surface": p_surface, "r_num": r_num, "r_den": r_den, "d_target": d_target,
                      "tpl": "linear_model_three_pts_hard", "variant": sub}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            # Round to one decimal
            ans = f"{p_target:.1f}".rstrip("0").rstrip(".")
            if "." not in ans:
                ans = f"{p_target:.1f}"
            sm, sx = spr_bounds(ans)
            d_near = d_ref
            p_near = p_surface + r_num
            exact_stem = (
                f"A scuba diver measures pressure below the water surface. "
                f"At 0 meters the pressure is {p_surface} atm, and at {d_near} meters the pressure is {p_near} atm. "
                f"If the pressure is a linear function of depth, what is the pressure, in atm, "
                f"at {d_target} meters? Round to the nearest tenth."
            )
            ctx = (f"LFN d3 linear_model_three_pts_hard (extrapolate). "
                   f"P(0) = {p_surface}, P({d_near}) = {p_near}; slope = {r_num}/{r_den}. "
                   f"P({d_target}) = ({r_num}/{r_den})*{d_target} + {p_surface} = {p_target:.4f} → {ans}. "
                   f"Correct: {ans}. SPR. "
                   f"CRITICAL — use exactStem verbatim; P({d_near}) = {p_near}, NOT a nearby decimal.")
            result = _lfn(3, params, ph, ans, [], sm, sx, "spr", ctx, None)
            result["exactStem"] = exact_stem
            if validate_math_object(result):
                continue
            return result

        # interpolate (default)
        sub = "interpolate"
        y1 = rng_obj.choice([30, 40, 50, 60])
        y2 = y1 + rng_obj.choice([80, 100, 120, 150])
        yr_span = rng_obj.choice([10, 15, 20])
        yr_target_offset = rng_obj.choice([2, 3, 4, 5])
        rate_per_yr = (y2 - y1) / yr_span
        y_target = y1 + rate_per_yr * (yr_span + yr_target_offset)
        y_target_rounded = round(y_target)
        params = {"y1": y1, "y2": y2, "yr_span": yr_span, "yr_target_offset": yr_target_offset,
                  "tpl": "linear_model_three_pts_hard", "variant": sub}
        ph = param_hash(params)
        if ph in exclude_params:
            continue
        ans = str(y_target_rounded)
        sm, sx = spr_bounds(ans)
        exact_stem = (
            f"A linear model estimates a quantity over time. "
            f"The quantity was {y1} at year 0 and {y2} at year {yr_span}. "
            f"If the relationship is linear, to the nearest whole number, "
            f"what is the quantity at year {yr_span + yr_target_offset}?"
        )
        ctx = (f"LFN d3 linear_model_three_pts_hard (interpolate). "
               f"Year 0: y={y1}; year {yr_span}: y={y2}; rate = ({y2}-{y1})/{yr_span} = {rate_per_yr}. "
               f"Year {yr_span + yr_target_offset}: y = {y1} + {rate_per_yr}*{yr_span + yr_target_offset} = {y_target:.2f} -> {ans}. "
               f"Correct: {ans}. SPR. "
               f"CRITICAL — use exactStem verbatim; target year is {yr_span + yr_target_offset}, NOT an intermediate year.")
        result = _lfn(3, params, ph, ans, [], sm, sx, "spr", ctx, None)
        result["exactStem"] = exact_stem
        if validate_math_object(result):
            continue
        return result
    raise RuntimeError("linear_model_three_pts_hard d3: could not generate unique params")


def _d3_literal_formula_solve(rng_obj, exclude_params, variant=None):
    """Rearrange a literal formula and solve for another variable.
    Variants: isolate_var, kelvin_inverse.
    """
    for _ in range(200):
        if variant == "kelvin_inverse":
            sub = "kelvin_inverse"
            # h = 9(v - 273.15)/5 + 32; given h, find v
            h_target = rng_obj.choice([350, 400, 450, 467.33, 500, 550])
            if isinstance(h_target, float):
                h_num = h_target
            else:
                h_num = float(h_target)
            # v - 273.15 = (h - 32) * 5/9
            v = (h_num - 32) * 5 / 9 + 273.15
            v_rounded = round(v)
            if abs(v - v_rounded) > 0.5:
                continue
            params = {"h": h_target, "tpl": "literal_formula_solve", "variant": sub}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(v_rounded)
            sm, sx = spr_bounds(ans)
            exact_stem = (
                f"The equation h = 9(v - 273.15)/5 + 32 gives the temperature h, in degrees Fahrenheit, "
                f"of any substance that has a temperature of v kelvins. "
                f"If a substance has a temperature of {h_target} degrees Fahrenheit, "
                f"what is the corresponding temperature, in kelvins? "
                f"Round to the nearest whole number."
            )
            ctx = (f"LFN d3 literal_formula_solve (kelvin_inverse). "
                   f"h = 9(v-273.15)/5 + 32; h = {h_target} (Fahrenheit). "
                   f"Solve for v (Kelvin): v = ({h_target}-32)*5/9 + 273.15 = {v_rounded}. "
                   f"Correct: {ans}. SPR. "
                   f"CRITICAL — use exactStem verbatim. Given value is {h_target} FAHRENHEIT; "
                   f"ask for KELVIN. Do NOT reverse the question direction.")
            result = _lfn(3, params, ph, ans, [], sm, sx, "spr", ctx, None)
            result["exactStem"] = exact_stem
            if validate_math_object(result):
                continue
            return result

        # isolate_var (F = 9/5 C + 32 family)
        sub = "isolate_var"
        c_ans = rng_obj.choice([10, 15, 20, 25, 30, 35])
        f_target = 9 * c_ans / 5 + 32
        if f_target != int(f_target):
            continue
        f_target = int(f_target)
        params = {"c_ans": c_ans, "f_target": f_target,
                  "tpl": "literal_formula_solve", "variant": sub}
        ph = param_hash(params)
        if ph in exclude_params:
            continue
        ans = str(c_ans)
        sm, sx = spr_bounds(ans)
        exact_stem = (
            f"The equation F = (9/5)C + 32 gives the temperature F, in degrees Fahrenheit, "
            f"corresponding to a temperature of C degrees Celsius. "
            f"What is the value of C when F = {f_target}?"
        )
        ctx = (f"LFN d3 literal_formula_solve (isolate_var). "
               f"F = (9/5)C + 32; given F = {f_target}, solve for C: C = ({f_target}-32)*5/9 = {c_ans}. "
               f"Correct: {ans}. SPR. "
               f"CRITICAL — use exactStem verbatim. Given value is F = {f_target} (Fahrenheit); "
               f"ask for C (Celsius). Do NOT reverse the question direction.")
        result = _lfn(3, params, ph, ans, [], sm, sx, "spr", ctx, None)
        result["exactStem"] = exact_stem
        if validate_math_object(result):
            continue
        return result
    raise RuntimeError("literal_formula_solve d3: could not generate unique params")


def _d3_interpret_shift_or_coeff(rng_obj, exclude_params, variant=None):
    """Interpret how a change in input produces a change in output, or interpret signed coefficient.
    Variants: signed_change, abs_change, coefficient_from_growth.
    """
    for _ in range(200):
        if variant == "coefficient_from_growth":
            sub = "coefficient_from_growth"
            birth = Rational(rng_obj.choice([12, 15, 18]), 10)  # 1.2, 1.5, 1.8
            week = rng_obj.choice([2, 4, 6, 8])
            rate = Rational(rng_obj.choice([4, 5, 6, 8, 10]), 10)  # 0.4, 0.5...
            after = birth + rate * week
            if after.denominator != 10:
                continue
            params = {"birth_num": birth.numerator, "birth_den": birth.denominator,
                      "week": week,
                      "rate_num": rate.numerator, "rate_den": rate.denominator,
                      "tpl": "interpret_shift_or_coeff", "variant": sub}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            rate_disp = f"{float(rate)}"
            ans = f"The piglet gains {rate_disp} kilogram per week"
            distractors = make_distractors(ans, [
                f"The total weight, in kilograms, after {week} weeks",
                f"The piglet weighs {rate_disp} kilogram at birth",
                f"The total weight gained over {week} weeks",
            ])
            exact_stem = (
                f"A scientist models a piglet's weight with W(x) = a + bx, where a is the birth weight "
                f"in kilograms and x is the number of weeks since birth. "
                f"If W({week}) = {float(after)} and the birth weight was {float(birth)} kilograms, "
                f"which of the following is the best interpretation of b in this context?"
            )
            ctx = (f"LFN d3 interpret_shift_or_coeff (coefficient_from_growth). "
                   f"W(x) = a + bx; a = {float(birth)}, W({week}) = {float(after)} → b = {rate_disp}. "
                   f"b is the slope = weekly weight gain. "
                   f"Correct: '{ans}'. "
                   f"CRITICAL — use exactStem verbatim. Do NOT define b in the stem; "
                   f"the student must compute b = ({float(after)} - {float(birth)}) / {week} = {rate_disp} "
                   f"and interpret it. Stating 'b is the weekly gain' in the stem leaks the answer.")
            result = _lfn(3, params, ph, ans, distractors, None, None, "mcq", ctx, None)
            result["exactStem"] = exact_stem
            if validate_math_object(result):
                continue
            return result

        if variant == "abs_change":
            sub = "abs_change"
            init = rng_obj.choice([100, 200, 300, 400, 500])
            rate = rng_obj.choice([2, 3, 4, 5, 6, 8])
            params = {"init": init, "rate": rate,
                      "tpl": "interpret_shift_or_coeff", "variant": sub}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = f"The volume of water decreases by {rate} liters each minute"
            distractors = make_distractors(ans, [
                f"The container starts with −{rate} liters of water",
                f"The volume of water increases by {rate} liters each minute",
                f"The container empties after {rate} minutes",
            ])
            exact_stem = (
                f"The function P is defined by P(t) = {init} − {rate}t, where P(t) is the volume of water "
                f"in a container, in liters, t minutes after draining begins. Which of the following is the "
                f"best interpretation of −{rate} in this context?"
            )
            ctx = (f"LFN d3 interpret_shift_or_coeff (abs_change). "
                   f"Stem (set verbatim): '{exact_stem}'. "
                   f"−{rate} is rate per minute; negative sign indicates decrease. "
                   f"Correct: '{ans}'.")
            result = _lfn(3, params, ph, ans, distractors, None, None, "mcq", ctx, None)
            result["exactStem"] = exact_stem
            if validate_math_object(result):
                continue
            return result

        # signed_change (kelvin → Fahrenheit rate)
        sub = "signed_change"
        delta_k_num = rng_obj.choice([21, 25, 30, 35, 42])  # small decimals
        delta_k = delta_k_num / 10.0  # 2.1, 2.5, etc.
        delta_f = delta_k * 9 / 5
        params = {"delta_k_num": delta_k_num,
                  "tpl": "interpret_shift_or_coeff", "variant": sub}
        ph = param_hash(params)
        if ph in exclude_params:
            continue
        ans = f"{delta_f:.2f}".rstrip("0").rstrip(".")
        if "." not in ans:
            ans = f"{delta_f:.2f}"
        sm, sx = spr_bounds(ans)
        exact_stem = (
            f"The function F is defined by F(x) = (9/5)(x - 273.15) + 32, giving the Fahrenheit "
            f"temperature F corresponding to x kelvins. If the temperature of a substance increases "
            f"by {delta_k} kelvins, by how many degrees Fahrenheit does its temperature increase?"
        )
        ctx = (f"LFN d3 interpret_shift_or_coeff (signed_change). "
               f"F(x) = (9/5)(x-273.15) + 32; change of {delta_k} K → (9/5)*{delta_k} = {delta_f} F. "
               f"Correct: {ans}. SPR. "
               f"CRITICAL — use exactStem verbatim; the given increase is {delta_k} kelvins.")
        result = _lfn(3, params, ph, ans, [], sm, sx, "spr", ctx, None)
        result["exactStem"] = exact_stem
        if validate_math_object(result):
            continue
        return result
    raise RuntimeError("interpret_shift_or_coeff d3: could not generate unique params")


# ═══════════════════════════════════════════════════════════════════════════════
# Routing dicts
# ═══════════════════════════════════════════════════════════════════════════════

_D1 = {
    "evaluate_integer":              {"fn": _d1_evaluate_integer,
                                      "variants": ["pos_input", "neg_input", "neg_slope",
                                                   "eval_at_zero", "unit_coefficient"]},
    "evaluate_fraction":             {"fn": _d1_evaluate_fraction,
                                      "variants": ["pos_frac", "neg_frac", "decimal_coeff"]},
    "interpret_slope_easy":          {"fn": _d1_interpret_slope_easy,
                                      "variants": ["rate_per_unit", "cost_per_item", "decrease_rate"]},
    "interpret_intercept_easy":      {"fn": _d1_interpret_intercept_easy,
                                      "variants": ["initial_value", "starting_amount",
                                                   "constant_in_growth", "find_y_intercept"]},
    "graph_read_intercept":          {"fn": _d1_graph_read_intercept,
                                      "variants": ["x_intercept", "y_intercept", "identify_y_coord"]},
    "word_equation_simple":          {"fn": _d1_word_equation_simple,
                                      "variants": ["flat_plus_rate", "verbal_description", "service_contract"]},
    "inverse_evaluate_easy":         {"fn": _d1_inverse_evaluate_easy,
                                      "variants": ["one_step", "two_step"]},
    "match_graph_to_equation_table": {"fn": _d1_match_graph_to_equation_table,
                                      "variants": ["table_to_equation"]},
}

_D2 = {
    "evaluate_compound":            {"fn": _d2_evaluate_compound,
                                     "variants": ["combine_two_fns", "scaled_output", "coefficient_gather",
                                                  "difference_single_fn", "symbolic_input"]},
    "interpret_slope_medium":       {"fn": _d2_interpret_slope_medium,
                                     "variants": ["rate_in_formula", "rate_from_graph", "gas_tank_rate"]},
    "interpret_intercept_medium":   {"fn": _d2_interpret_intercept_medium,
                                     "variants": ["juice_volume", "fabric_relation"]},
    "interpret_x_intercept":        {"fn": _d2_interpret_x_intercept,
                                     "variants": ["time_zero_context", "break_even_context"]},
    "equation_from_two_pts":        {"fn": _d2_equation_from_two_pts,
                                     "variants": ["integer_slope", "larger_slope",
                                                  "from_slope_and_point", "negative_slope_decreasing"]},
    "coefficient_from_table":       {"fn": _d2_coefficient_from_table,
                                     "variants": ["find_m", "find_b", "two_unknowns"]},
    "parameter_solve_simple":       {"fn": _d2_parameter_solve_simple,
                                     "variants": ["solve_m", "solve_b", "inverse_then_solve"]},
    "linear_model_word_solve":      {"fn": _d2_linear_model_word_solve,
                                     "variants": ["forward_interp", "specific_input",
                                                  "acceleration_like", "savings_balance"]},
    "graph_intercept_computed":     {"fn": _d2_graph_intercept_computed,
                                     "variants": ["sum_of_intercepts", "intercept_after_shift"]},
    "parallel_slope_from_fn":       {"fn": _d2_parallel_slope_from_fn,
                                     "variants": ["parallel_to_linear_fn"]},
}

_D3 = {
    "parameter_solve_compound":     {"fn": _d3_parameter_solve_compound,
                                     "variants": ["double_param", "expr_input",
                                                  "implicit_b", "table_derived"]},
    "word_model_multistep":         {"fn": _d3_word_model_multistep,
                                     "variants": ["flat_plus_daily", "tiered_rate", "coverage_double"]},
    "linear_model_three_pts_hard":  {"fn": _d3_linear_model_three_pts_hard,
                                     "variants": ["interpolate", "extrapolate", "window_repair"]},
    "literal_formula_solve":        {"fn": _d3_literal_formula_solve,
                                     "variants": ["isolate_var", "kelvin_inverse"]},
    "interpret_shift_or_coeff":     {"fn": _d3_interpret_shift_or_coeff,
                                     "variants": ["signed_change", "abs_change", "coefficient_from_growth"]},
}

_ROUTING = {1: _D1, 2: _D2, 3: _D3}


# ═══════════════════════════════════════════════════════════════════════════════
# Public metadata API
# ═══════════════════════════════════════════════════════════════════════════════

def lfn_variants(difficulty: int, template: str = None) -> dict:
    """
    Return variant metadata for linear_functions.

    If template is None: returns {template: [variants]} for all templates at the given difficulty.
    If template is given: returns {"variants": [...]} for that template.
    """
    routing = _ROUTING.get(difficulty, {})
    if template is None:
        return {tpl: entry["variants"] for tpl, entry in routing.items()}
    if template not in routing:
        raise ValueError(f"Unknown template '{template}' for linear_functions d{difficulty}")
    return {"variants": routing[template]["variants"]}


# ═══════════════════════════════════════════════════════════════════════════════
# Main generator
# ═══════════════════════════════════════════════════════════════════════════════

def gen_linear_functions(difficulty: int, rng_obj: random.Random, exclude_params: set,
                         force_template: str = None,
                         force_variant: str = None,
                         **_kwargs) -> dict:
    """
    Linear functions (LFN).

    Dispatches to a standalone per-template function via _D1/_D2/_D3 routing dicts.
    """
    clamped = min(max(difficulty, 1), 3)
    routing = _ROUTING.get(clamped, _D3)

    if force_template is not None:
        if force_template not in routing:
            valid = sorted(routing.keys())
            raise ValueError(
                f"--template '{force_template}' is not valid for "
                f"linear_functions d{clamped}. Valid: {valid}"
            )
        tpl = force_template
    else:
        tpl = rng_obj.choice(list(routing.keys()))

    entry = routing[tpl]
    return entry["fn"](rng_obj, exclude_params, variant=force_variant)
