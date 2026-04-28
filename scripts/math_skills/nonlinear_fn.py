import math as _math
import random
import sympy as sp
from sympy import symbols, solve, Rational
from .core import param_hash, spr_bounds, make_distractors, validate_math_object

# ── Format helpers ────────────────────────────────────────────────────────────

def _lin(m, b):
    """Format m·x + b cleanly (handles m=±1, b=0, negative b)."""
    ms = "" if m == 1 else ("-" if m == -1 else str(m))
    xs = f"{ms}x"
    if b > 0:
        return f"{xs} + {b}"
    elif b < 0:
        return f"{xs} − {abs(b)}"
    return xs


def _exp_str(a, base, c=0):
    """Format a·base^x + c (a=1 → omit coefficient)."""
    a_str = str(a) if a != 1 else ""
    expr = f"{a_str}({base})^x" if a_str else f"({base})^x"
    if c > 0:
        return f"{expr} + {c}"
    elif c < 0:
        return f"{expr} − {abs(c)}"
    return expr


def _poly_str(a, b, var="x"):
    """Format a·var² + b (a=1 → omit coefficient)."""
    a_str = "" if a == 1 else str(a)
    quad = f"{a_str}{var}²"
    if b > 0:
        return f"{quad} + {b}"
    elif b < 0:
        return f"{quad} − {abs(b)}"
    return quad


# ── Result helper ─────────────────────────────────────────────────────────────

def _nlf(d, params, ph, ans, distractors, qt="mcq", ctx="",
         exact_stem=None, diagram=None, scenario_tag=None):
    """Build a nonlinear_functions MathObject dict."""
    sm, sx = (None, None)
    if qt == "spr":
        try:
            sm, sx = spr_bounds(str(ans))
        except Exception:
            pass
    return {
        "skill":         "nonlinear_functions",
        "difficulty":    d,
        "questionType":  qt,
        "params":        params,
        "paramHash":     ph,
        "verifiedAnswer": str(ans),
        "distractors":   [str(d_) for d_ in distractors],
        "sprMin":        sm,
        "sprMax":        sx,
        "scenarioTag":   scenario_tag,
        "diagramSpec":   diagram,
        "questionContext": ctx,
        "exactStem":     exact_stem,
    }


# ── Context pools ─────────────────────────────────────────────────────────────
# Each tuple: (tag, fn_name, setup_tmpl, correct_tmpl, wrong1, wrong2, wrong3)

_NLF_INITIAL_VALUE_CTX = [
    (
        "bacteria",
        "P",
        "\\(P(t) = {a} \\cdot {b}^t\\), where \\(P(t)\\) is the number of bacteria in a culture after \\(t\\) hours.",
        "The initial number of bacteria in the culture is {a}.",
        "The number of bacteria increases by {a} each hour.",
        "After {b} hours, there are {a} bacteria in the culture.",
        "{a} is the growth factor of the bacteria per hour.",
    ),
    (
        "savings",
        "A",
        "\\(A(t) = {a} \\cdot {b}^t\\), where \\(A(t)\\) is the value, in dollars, of a savings account after \\(t\\) years.",
        "The initial value of the savings account is {a} dollars.",
        "Each year, the savings account grows by {a} dollars.",
        "After {b} years, the savings account is worth {a} dollars.",
        "{a} is the annual growth factor of the account.",
    ),
    (
        "population",
        "P",
        "\\(P(t) = {a} \\cdot {b}^t\\), where \\(P(t)\\) is the population of a town \\(t\\) years after 2010.",
        "The population of the town in 2010 was {a}.",
        "The population grows by {a} people each year.",
        "After {b} years, the population is {a}.",
        "{a} is the annual growth factor of the population.",
    ),
    (
        "temperature",
        "T",
        "\\(T(t) = {a} \\cdot {b}^t\\), where \\(T(t)\\) is the temperature, in degrees Fahrenheit, "
        "of an object \\(t\\) minutes after being removed from an oven.",
        "The temperature of the object when it was removed from the oven was {a}°F.",
        "Each minute, the temperature increases by {a} degrees.",
        "After {b} minutes, the temperature is {a}°F.",
        "{a} is the rate at which the temperature changes per minute.",
    ),
    (
        "revenue",
        "R",
        "\\(R(t) = {a} \\cdot {b}^t\\), where \\(R(t)\\) is the monthly revenue, in dollars, "
        "of a new company \\(t\\) months after opening.",
        "The monthly revenue of the company when it opened was {a} dollars.",
        "Each month, the revenue increases by {a} dollars.",
        "After {b} months, the monthly revenue is {a} dollars.",
        "{a} is the monthly growth factor of the company's revenue.",
    ),
]


# ═══════════════════════════════════════════════════════════════════════════════
# D1 TEMPLATES  (Easy — 8 templates · 13 variants)
# ═══════════════════════════════════════════════════════════════════════════════

def _d1_evaluate_polynomial(rng_obj, exclude_params, variant=None):
    """f(x) = ax² + b  or  x³ + b; evaluate at given x.  MCQ or SPR."""
    v = "find_output"
    for _ in range(200):
        use_cubic = rng_obj.random() < 0.3
        if use_cubic:
            b   = rng_obj.randint(0, 8)
            x   = rng_obj.randint(-2, 3)
            ans_val = x ** 3 + b
            if abs(ans_val) > 30:
                continue
            if b > 0:
                fn_str = f"f(x) = x³ + {b}"
            elif b < 0:
                fn_str = f"f(x) = x³ − {abs(b)}"
            else:
                fn_str = "f(x) = x³"
            params = {"b": b, "x_val": x, "form": "cubic",
                      "tpl": "evaluate_polynomial", "variant": v}
        else:
            a = rng_obj.randint(1, 4)
            b = rng_obj.randint(-4, 6)
            x = rng_obj.randint(-3, 4)
            ans_val = a * x ** 2 + b
            if abs(ans_val) > 40:
                continue
            a_str = "" if a == 1 else str(a)
            if b > 0:
                fn_str = f"f(x) = {a_str}x² + {b}"
            elif b < 0:
                fn_str = f"f(x) = {a_str}x² − {abs(b)}"
            else:
                fn_str = f"f(x) = {a_str}x²"
            params = {"a": a, "b": b, "x_val": x, "form": "quadratic",
                      "tpl": "evaluate_polynomial", "variant": v}

        ph = param_hash(params)
        if ph in exclude_params:
            continue

        ans = str(ans_val)
        qt  = rng_obj.choice(["mcq", "spr"])

        if use_cubic:
            d1 = str(x ** 2 + b)    # used x² instead of x³
            d2 = str(x ** 3 - b)    # subtracted b
            d3 = str(3 * x ** 2)    # derivative confusion
        else:
            a_ = params.get("a", 1)
            d1 = str(a_ * abs(x) + b)   # forgot to square (used |x|)
            d2 = str(a_ * x ** 2)       # dropped constant b
            d3 = str(a_ * x + b)        # used x instead of x²

        dist  = make_distractors(ans, [d1, d2, d3])
        exact = f"The function f is defined by {fn_str}. What is the value of f({x})?"
        ctx   = (f"{fn_str}; f({x}) = {ans_val}. "
                 f"CRITICAL — stem is locked (exactStem). Do NOT rewrite or alter the function. "
                 f"DISTRACTOR ERRORS — wrong power/sign/constant in each choice.")
        return _nlf(1, params, ph, ans, dist if qt == "mcq" else [], qt, ctx, exact_stem=exact)

    raise RuntimeError("_d1_evaluate_polynomial: could not generate unique params")


def _d1_evaluate_exponential(rng_obj, exclude_params, variant=None):
    """f(x) = a·b^x; evaluate at given x (x∈[0..3]).  MCQ or SPR."""
    v = "find_output"
    for _ in range(200):
        a = rng_obj.randint(2, 5)
        b = rng_obj.randint(2, 3)
        x = rng_obj.randint(0, 3)
        ans_val = a * (b ** x)
        if ans_val > 80:
            continue

        params = {"a": a, "b": b, "x_val": x,
                  "tpl": "evaluate_exponential", "variant": v}
        ph = param_hash(params)
        if ph in exclude_params:
            continue

        ans = str(ans_val)
        qt  = rng_obj.choice(["mcq", "spr"])

        d1 = str(a * b * x)            # treated b^x as b·x
        d2 = str(a + b ** x)           # added a instead of multiplying
        d3 = str(a * b ** (x + 1))     # evaluated at x+1

        dist  = make_distractors(ans, [d1, d2, d3])
        exact = f"The function f is defined by \\(f(x) = {a} \\cdot {b}^x\\). What is the value of \\(f({x})\\)?"
        ctx   = (f"f(x) = {a}({b})^x; f({x}) = {ans_val}. "
                 f"CRITICAL — stem is locked (exactStem). Do NOT rewrite or alter the function. "
                 f"CRITICAL — answer choices must be plain integers, NO LaTeX or math delimiters. "
                 f"DISTRACTOR ERRORS — "
                 f"'{dist[0]}': treated b^x as b·x. "
                 f"'{dist[1] if len(dist)>1 else '?'}': added a instead of multiplying. "
                 f"'{dist[2] if len(dist)>2 else '?'}': used x+1 as the exponent.")
        return _nlf(1, params, ph, ans, dist if qt == "mcq" else [], qt, ctx, exact_stem=exact)

    raise RuntimeError("_d1_evaluate_exponential: could not generate unique params")


def _d1_evaluate_other_nonlinear(rng_obj, exclude_params, variant=None):
    """√(x+c),  k/x,  or  |x+c|;  evaluate at given x.  MCQ or SPR."""
    v = variant or rng_obj.choice(
        ["find_radical_output", "find_rational_output", "find_absolute_value_output"])

    for _ in range(200):
        # ── find_radical_output ───────────────────────────────────────────────
        if v == "find_radical_output":
            target  = rng_obj.randint(1, 6)
            sq      = target * target
            x_base  = rng_obj.randint(-3, 10)
            c       = sq - x_base
            if c == 0:
                continue   # trivial √x
            x_val = x_base
            c_str = f"+ {c}" if c > 0 else f"− {abs(c)}"
            fn_str = f"f(x) = √(x {c_str})"

            params = {"c": c, "x_val": x_val, "sq": sq,
                      "tpl": "evaluate_other_nonlinear", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue

            ans  = str(target)
            d1   = str(sq)
            d2   = str(target + 1)
            d3   = str(target - 1) if target > 1 else str(target + 2)
            dist = make_distractors(ans, [d1, d2, d3])
            exact = f"The function f is defined by {fn_str}. What is the value of f({x_val})?"
            ctx   = (f"{fn_str}; f({x_val}) = √{sq} = {target}. "
                     f"CRITICAL — stem is locked (exactStem). Do NOT rewrite or alter the function. "
                     f"DISTRACTOR ERRORS — "
                     f"'{d1}': forgot to take the square root. "
                     f"'{d2}/{d3}': off by one.")
            qt = rng_obj.choice(["mcq", "spr"])
            return _nlf(1, params, ph, ans, dist if qt == "mcq" else [], qt, ctx, exact_stem=exact)

        # ── find_rational_output ──────────────────────────────────────────────
        elif v == "find_rational_output":
            k        = rng_obj.choice([6, 8, 10, 12, 15, 20])
            divisors = [d for d in range(2, k + 1) if k % d == 0 and d != k]
            if not divisors:
                continue
            x_pos  = rng_obj.choice(divisors)
            x_val  = rng_obj.choice([x_pos, -x_pos])
            ans_val = k // x_pos
            if x_val < 0:
                ans_val = -ans_val

            params = {"k": k, "x_val": x_val,
                      "tpl": "evaluate_other_nonlinear", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue

            ans  = str(ans_val)
            d1   = str(k * x_val)                          # multiplied instead of divided
            d2   = str(abs(ans_val) + 1)                   # sign / off-by-one
            d3   = str(k - abs(x_val))                     # subtracted
            dist = make_distractors(ans, [d1, d2, d3])
            exact = f"The function f is defined by f(x) = {k}/x. What is the value of f({x_val})?"
            ctx   = (f"f(x) = {k}/x; f({x_val}) = {ans_val}. "
                     f"CRITICAL — stem is locked (exactStem). Do NOT rewrite or alter the function. "
                     f"DISTRACTOR ERRORS — "
                     f"'{dist[0]}': multiplied k·x. "
                     f"'{dist[1] if len(dist)>1 else '?'}': sign or rounding error.")
            return _nlf(1, params, ph, ans, dist, "mcq", ctx, exact_stem=exact)

        # ── find_absolute_value_output ────────────────────────────────────────
        else:
            c      = rng_obj.randint(-5, 5)
            target = rng_obj.randint(1, 8)
            # x such that |x + c| = target
            x_val = rng_obj.choice([target - c, -(target + c)])
            if abs(x_val + c) != target:
                continue

            c_str  = f"+ {c}" if c > 0 else (f"− {abs(c)}" if c < 0 else "")
            fn_str = f"f(x) = |x {c_str}|" if c_str else "f(x) = |x|"

            params = {"c": c, "x_val": x_val,
                      "tpl": "evaluate_other_nonlinear", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue

            ans  = str(target)
            d1   = str(x_val + c)                           # dropped abs (kept sign)
            d2   = str(target + 1)
            d3   = str(target - 1) if target > 1 else str(target + 2)
            dist = make_distractors(ans, [d1, d2, d3])
            exact = f"The function f is defined by {fn_str}. What is the value of f({x_val})?"
            ctx   = (f"{fn_str}; f({x_val}) = |{x_val + c}| = {target}. "
                     f"CRITICAL — stem is locked (exactStem). Do NOT rewrite or alter the function. "
                     f"DISTRACTOR ERRORS — "
                     f"'{d1}': dropped the absolute value bars. "
                     f"'{d2}/{d3}': off by one.")
            qt = rng_obj.choice(["mcq", "spr"])
            return _nlf(1, params, ph, ans, dist if qt == "mcq" else [], qt, ctx, exact_stem=exact)

    raise RuntimeError("_d1_evaluate_other_nonlinear: could not generate unique params")


def _d1_interpret_y_intercept_context(rng_obj, exclude_params, variant=None):
    """f(0) = a in real-world context; MCQ about meaning.  exactStem required."""
    v = "interpret_initial_value"
    for _ in range(200):
        a       = (rng_obj.randint(5, 50)) * 10   # round hundreds: 50–500
        b       = rng_obj.randint(2, 4)
        ctx_idx = rng_obj.randint(0, len(_NLF_INITIAL_VALUE_CTX) - 1)
        tag, fn_name, setup_t, corr_t, w1_t, w2_t, w3_t = _NLF_INITIAL_VALUE_CTX[ctx_idx]

        params = {"a": a, "b": b, "ctx_idx": ctx_idx,
                  "tpl": "interpret_y_intercept_context", "variant": v}
        ph = param_hash(params)
        if ph in exclude_params:
            continue

        setup   = setup_t.format(a=a, b=b)
        correct = corr_t.format(a=a, b=b)
        wrong1  = w1_t.format(a=a, b=b)
        wrong2  = w2_t.format(a=a, b=b)
        wrong3  = w3_t.format(a=a, b=b)

        if len({correct, wrong1, wrong2, wrong3}) < 4:
            continue

        exact_stem = (f"{setup}\n"
                      f"What does \\({fn_name}(0)\\) represent in this context?")
        ctx = (f"Context: {tag}. {fn_name}(0) = {a}. "
               f"Correct: '{correct}'. "
               f"CRITICAL — stem is locked (exactStem). Do NOT rewrite the stem or reveal the value {a}. "
               f"CRITICAL — answer choices must be plain English sentences, NO LaTeX or math delimiters. "
               f"Write numbers as plain digits (e.g. {a}, not \\({a}\\)). "
               f"DISTRACTOR ERRORS — "
               f"'{wrong1}': confused initial value with rate of change. "
               f"'{wrong2}': confused t=0 with t={b}. "
               f"'{wrong3}': confused initial value with growth factor.")

        result = _nlf(1, params, ph, correct, [wrong1, wrong2, wrong3],
                      "mcq", ctx, exact_stem=exact_stem, scenario_tag=tag)
        if validate_math_object(result):
            continue
        return result

    raise RuntimeError("_d1_interpret_y_intercept_context: could not generate unique params")


def _d1_y_intercept_from_graph(rng_obj, exclude_params, variant=None):
    """Exponential curve on graph; identify the y-intercept (0, a).  MCQ + diagram."""
    v = "identify_ordered_pair"
    for _ in range(200):
        a = rng_obj.randint(1, 4)
        b = rng_obj.randint(2, 3)

        params = {"a": a, "b": b, "tpl": "y_intercept_from_graph", "variant": v}
        ph = param_hash(params)
        if ph in exclude_params:
            continue

        ans = f"(0, {a})"
        d1  = f"(1, {a * b})"        # point at x=1
        d2  = f"(0, {a + 1})"        # y-value off by 1
        d3  = f"(0, {a * b})"        # confused y-intercept with f(1)
        dist = make_distractors(ans, [d1, d2, d3])

        diag = {
            "type": "nonlinear_curve",
            "curveType": "exponential",
            "a": a, "b": b, "c": 0,
            "x_range": [-2, 4],
            "labeled_points": [],
            "show_y_intercept": False,
        }
        ctx = (f"f(x) = {a}·{b}^x; y-intercept is (0, {a}). "
               f"CRITICAL — do NOT state the formula or the y-intercept value in the stem. "
               f"This is a graph-reading question: the stem must only say the graph is shown "
               f"and ask which ordered pair the graph passes through at x = 0. "
               f"DISTRACTOR ERRORS — "
               f"'(1, {a*b})': read x=1 instead of x=0. "
               f"'(0, {a+1})': misread the y-scale. "
               f"'(0, {a*b})': confused y-intercept with f(1).")
        return _nlf(1, params, ph, ans, dist, "mcq", ctx, diagram=diag)

    raise RuntimeError("_d1_y_intercept_from_graph: could not generate unique params")


def _d1_vertex_from_graph(rng_obj, exclude_params, variant=None):
    """Parabola on graph; read the vertex min or max VALUE.  MCQ or SPR + diagram."""
    v = variant or rng_obj.choice(["find_minimum", "find_maximum"])
    for _ in range(200):
        h = rng_obj.randint(-3, 3)
        k = rng_obj.randint(-3, 3)
        a = 1 if v == "find_minimum" else -1

        # y-intercept = a·h² + k — must stay within renderable range
        y_int = a * h * h + k
        if abs(y_int) > 5:
            continue

        params = {"a": a, "h": h, "k": k, "tpl": "vertex_from_graph", "variant": v}
        ph = param_hash(params)
        if ph in exclude_params:
            continue

        ans  = str(k)
        d1   = str(h)           # x-coord of vertex (confused x with y)
        d2   = str(k + 1)       # misread scale
        d3   = str(-k)          # negated vertex value
        dist = make_distractors(ans, [d1, d2, d3])

        diag = {
            "type": "parabola",
            "a": a, "h": h, "k": k,
            "vertex": [h, k],
            "x_intercepts": None,
            "y_intercept": y_int,
            "vertex_label": False,   # don't label (h,k) — student must read k from graph
        }
        direction = "minimum" if v == "find_minimum" else "maximum"
        sign_str  = "" if a == 1 else "−"
        ctx = (f"f(x) = {sign_str}(x − {h})² + {k}. "
               f"Vertex at ({h}, {k}); {direction} value is {k}. "
               f"CRITICAL — do NOT state the {direction} value in the stem. "
               f"Ask the student to find the {direction} value of f from the graph. "
               f"DISTRACTOR ERRORS — "
               f"'{h}': reported x-coordinate instead of y-coordinate of vertex. "
               f"'{k+1}': misread the scale. "
               f"'{-k}': negated the vertex y-value.")
        qt = rng_obj.choice(["mcq", "spr"])
        return _nlf(1, params, ph, ans, dist if qt == "mcq" else [], qt, ctx, diagram=diag)

    raise RuntimeError("_d1_vertex_from_graph: could not generate unique params")


def _d1_graph_translation(rng_obj, exclude_params, variant=None):
    """Vertical shift of an exponential.
    identify_shifted_graph  📊 — which equation is f(x)+k?
    find_output_after_shift   — given f(p)=v, find f(p)+k. exactStem required."""
    v = variant or rng_obj.choice(["identify_shifted_graph", "find_output_after_shift"])

    for _ in range(200):
        a = rng_obj.randint(1, 3)
        b = rng_obj.randint(2, 3)
        k = rng_obj.randint(1, 4)

        # ── identify_shifted_graph ────────────────────────────────────────────
        if v == "identify_shifted_graph":
            params = {"a": a, "b": b, "k": k,
                      "tpl": "graph_translation", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue

            a_str  = str(a) if a != 1 else ""
            # Plain-text forms (used only in ctx for Haiku's reference)
            plain_ans = f"y = {a_str}({b})^x + {k}"
            plain_d1  = f"y = {a_str}({b})^x − {k}"
            plain_d2  = f"y = {a_str}({b})^(x + {k})"
            plain_d3  = f"y = {a_str}({b * k})^x"
            # LaTeX-wrapped forms stored as answer choices (KaTeX renders ^ as superscript)
            ans  = f"\\(y = {a_str}({b})^x + {k}\\)"
            d1   = f"\\(y = {a_str}({b})^x - {k}\\)"            # shifted down
            d2   = f"\\(y = {a_str}({b})^{{x + {k}}}\\)"        # horizontal shift
            d3   = f"\\(y = {a_str}({b * k})^x\\)"              # scaled base
            dist = make_distractors(ans, [d1, d2, d3])

            diag = {
                "type": "nonlinear_curve",
                "curveType": "exponential",
                "a": a, "b": b, "c": 0,
                "x_range": [-2, 4],
                "labeled_points": [{"x": 0, "y": a, "label": f"(0, {a})"}],
                "show_y_intercept": True,
            }
            ctx = (f"f(x) = {a_str}({b})^x shown on graph. g(x) = f(x) + {k} = {plain_ans}. "
                   f"Ask which equation represents g(x) = f(x) + {k}. "
                   f"DISTRACTOR ERRORS — "
                   f"'{plain_d1}': shifted down by {k} instead of up. "
                   f"'{plain_d2}': horizontal shift (added {k} inside exponent) instead of vertical shift. "
                   f"'{plain_d3}': multiplied the base by {k} instead of adding {k} to the output.")
            return _nlf(1, params, ph, ans, dist, "mcq", ctx, diagram=diag)

        # ── find_output_after_shift ───────────────────────────────────────────
        else:
            p     = rng_obj.randint(-3, 5)
            v_val = rng_obj.randint(1, 20)
            ans_val = v_val + k

            params = {"p": p, "v": v_val, "k": k,
                      "tpl": "graph_translation", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue

            ans   = str(ans_val)
            d1    = str(v_val)           # forgot to add k
            d2    = str(v_val - k)       # subtracted k
            d3    = str(v_val * k)       # multiplied instead of added
            dist  = make_distractors(ans, [d1, d2, d3])
            exact = f"If f({p}) = {v_val}, what is the value of f({p}) + {k}?"
            ctx   = (f"f({p}) = {v_val}; f({p}) + {k} = {ans_val}. "
                     f"CRITICAL — stem is locked (exactStem). Do NOT rewrite it. "
                     f"DISTRACTOR ERRORS — "
                     f"'{v_val}': forgot to add {k}. "
                     f"'{v_val - k}': subtracted {k}. "
                     f"'{v_val * k}': multiplied f({p}) by {k}.")
            qt = rng_obj.choice(["mcq", "spr"])
            return _nlf(1, params, ph, ans, dist if qt == "mcq" else [], qt, ctx, exact)

    raise RuntimeError("_d1_graph_translation: could not generate unique params")


# piecewise_read_value — removed: zero Bluebook questions observed across all 414 screenshots.


# ═══════════════════════════════════════════════════════════════════════════════
# D2 TEMPLATES  (Medium — 12 templates · 23 variants)
# ═══════════════════════════════════════════════════════════════════════════════

# ── D2 context pools ──────────────────────────────────────────────────────────

# (tag, fn_name, unit, setup_tmpl)
_D2_EXP_CONTEXTS = [
    ("bacteria",    "P", "hours",  "bacteria in a culture",
     "\\(P(t) = {a} \\cdot {b}^t\\), where \\(P(t)\\) is the number of bacteria after \\(t\\) hours."),
    ("savings",     "A", "years",  "savings account",
     "\\(A(t) = {a} \\cdot {b}^t\\), where \\(A(t)\\) is the value, in dollars, of a savings account after \\(t\\) years."),
    ("population",  "P", "years",  "town population",
     "\\(P(t) = {a} \\cdot {b}^t\\), where \\(P(t)\\) is the population of a town \\(t\\) years after 2010."),
    ("temperature", "T", "minutes","object temperature",
     "\\(T(t) = {a} \\cdot {b}^t\\), where \\(T(t)\\) is the temperature, in °F, of an object \\(t\\) minutes after being removed from an oven."),
    ("revenue",     "R", "months", "company revenue",
     "\\(R(t) = {a} \\cdot {b}^t\\), where \\(R(t)\\) is the monthly revenue, in dollars, of a company \\(t\\) months after opening."),
]

# (tag, fn_name, unit, description, setup_tmpl) — for growth-rate contexts
_D2_GROWTH_CONTEXTS = [
    ("bacteria",    "P", "hours",  "bacteria in a culture",
     "\\(P(t) = {a}({base})^t\\), where \\(P(t)\\) is the number of bacteria after \\(t\\) hours."),
    ("savings",     "A", "years",  "savings account value in dollars",
     "\\(A(t) = {a}({base})^t\\), where \\(A(t)\\) is the value, in dollars, of an investment after \\(t\\) years."),
    ("population",  "P", "years",  "population of a town",
     "\\(P(t) = {a}({base})^t\\), where \\(P(t)\\) is the population of a town \\(t\\) years after 2015."),
    ("revenue",     "R", "months", "monthly revenue in dollars",
     "\\(R(t) = {a}({base})^t\\), where \\(R(t)\\) is the monthly revenue, in dollars, \\(t\\) months after launch."),
]

# (tag, fn_name, unit, t_meaning, zero_meaning) — for x-intercept contexts
_D2_XINT_CONTEXTS = [
    ("projectile", "h", "seconds",
     "the number of seconds after a ball is launched",
     "the ball returns to ground level"),
    ("profit",     "P", "units",
     "the number of units produced",
     "the company breaks even (zero profit)"),
    ("population", "P", "years",
     "the number of years after 2020",
     "the population reaches zero"),
    ("height",     "h", "seconds",
     "the number of seconds after a rocket is fired",
     "the rocket returns to the ground"),
]


def _d2_evaluate_exponential_zero(rng_obj, exclude_params, variant=None):
    """f(x)=a·bˣ; f(0)=a.
    find_initial_value   — compute f(0). exactStem. MCQ or SPR.
    interpret_initial_value — what does f(0) represent? exactStem (expression only). MCQ."""
    v = variant or rng_obj.choice(["find_initial_value", "interpret_initial_value"])

    for _ in range(200):
        ctx_entry = rng_obj.choice(_D2_EXP_CONTEXTS)
        tag, fn, unit, desc, setup_tmpl = ctx_entry

        a = rng_obj.randint(2, 20)
        b = rng_obj.randint(2, 4)
        setup = setup_tmpl.format(a=a, b=b)

        params = {"a": a, "b": b, "tag": tag, "tpl": "evaluate_exponential_zero", "variant": v}
        ph = param_hash(params)
        if ph in exclude_params:
            continue

        # ── find_initial_value ────────────────────────────────────────────────
        if v == "find_initial_value":
            ans = str(a)
            d1  = str(a * b)       # evaluated at t=1
            d2  = str(b)           # forgot coefficient a
            d3  = str(a + b)       # added instead of kept
            dist = make_distractors(ans, [d1, d2, d3])

            exact = f"{setup}\nWhat is the value of \\({fn}(0)\\)?"
            ctx = (f"f(0) = {a}·{b}^0 = {a}·1 = {a}. "
                   f"CRITICAL — stem is locked (exactStem). Do NOT rewrite. "
                   f"DISTRACTOR ERRORS — "
                   f"'{d1}': evaluated at t=1 (used b¹). "
                   f"'{d2}': forgot the coefficient {a}. "
                   f"'{d3}': added a and b instead.")
            qt = rng_obj.choice(["mcq", "spr"])
            return _nlf(2, params, ph, ans, dist if qt == "mcq" else [], qt, ctx, exact_stem=exact)

        # ── interpret_initial_value ───────────────────────────────────────────
        else:
            # Build 4 English choices — correct describes f(0)=a as the starting value
            correct_choice = f"The initial {desc} is {a}."
            w1 = f"The {desc} increases by {a} each {unit}."
            w2 = f"After {b} {unit}, the {desc} is {a}."
            w3 = f"{a} is the growth factor per {unit}."
            dist = make_distractors(correct_choice, [w1, w2, w3])

            # Stem shows expression only — never "f(0) = a"
            exact = f"{setup}\nWhat does \\({fn}(0)\\) represent in this context?"
            ctx = (f"{fn}(0) = {a} = initial {desc}. "
                   f"CRITICAL — stem is locked (exactStem). Do NOT include the value {a} in the stem question. "
                   f"CRITICAL — answer choices must be plain English sentences, NO LaTeX or math delimiters. "
                   f"DISTRACTOR ERRORS — "
                   f"'{w1}': confuses initial value with rate of change. "
                   f"'{w2}': misreads {b} as the time, {a} as the output. "
                   f"'{w3}': confuses initial value with growth factor.")
            ans = correct_choice
            return _nlf(2, params, ph, ans, dist, "mcq", ctx, exact_stem=exact)

    raise RuntimeError("_d2_evaluate_exponential_zero: could not generate unique params")


def _d2_interpret_exponential_statement(rng_obj, exclude_params, variant=None):
    """interpret_output_value — given f(t₀)=v, which English statement is correct?
    interpret_growth_factor — f(x)=a(1+r)ˣ; what does the base represent?"""
    v = variant or rng_obj.choice(["interpret_output_value", "interpret_growth_factor"])

    for _ in range(200):
        ctx_entry = rng_obj.choice(_D2_EXP_CONTEXTS)
        tag, fn, unit, desc, setup_tmpl = ctx_entry

        # ── interpret_output_value ────────────────────────────────────────────
        if v == "interpret_output_value":
            a  = rng_obj.randint(2, 10)
            b  = rng_obj.randint(2, 3)
            t0 = rng_obj.randint(1, 5)
            v_val = a * (b ** t0)
            if v_val > 500:
                continue

            params = {"a": a, "b": b, "t0": t0, "v": v_val, "tag": tag,
                      "tpl": "interpret_exponential_statement", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue

            setup = setup_tmpl.format(a=a, b=b)
            correct_choice = f"After {t0} {unit}, the {desc} is {v_val}."
            w1 = f"After {v_val} {unit}, the {desc} is {t0}."   # swapped t and v
            w2 = f"The {desc} increases by {v_val} each {unit}."  # interprets as rate
            w3 = f"The initial {desc} is {v_val}."               # confuses with f(0)
            dist = make_distractors(correct_choice, [w1, w2, w3])

            exact = (f"{setup}\n"
                     f"Which of the following is the best interpretation of the statement "
                     f"\\({fn}({t0}) = {v_val}\\) in this context?")
            ctx = (f"{fn}({t0}) = {v_val}: after {t0} {unit}, the {desc} is {v_val}. "
                   f"CRITICAL — stem is locked (exactStem). Do NOT rewrite. "
                   f"CRITICAL — answer choices must be plain English sentences, NO LaTeX. "
                   f"DISTRACTOR ERRORS — "
                   f"'{w1}': swapped the input ({t0}) and output ({v_val}). "
                   f"'{w2}': misread as a linear rate. "
                   f"'{w3}': confused {fn}({t0}) with {fn}(0).")
            ans = correct_choice
            return _nlf(2, params, ph, ans, dist, "mcq", ctx, exact_stem=exact)

        # ── interpret_growth_factor ───────────────────────────────────────────
        else:
            ctx_entry2 = rng_obj.choice(_D2_GROWTH_CONTEXTS)
            tag2, fn2, unit2, desc2, setup_tmpl2 = ctx_entry2

            a = rng_obj.randint(50, 500)
            # r in {5,8,10,12,15,20,25} %
            r_pct = rng_obj.choice([5, 8, 10, 12, 15, 20, 25])
            r = r_pct / 100
            base_num = round(1 + r, 2)
            base_str = str(base_num)

            params = {"a": a, "r_pct": r_pct, "base": base_str, "tag": tag2,
                      "tpl": "interpret_exponential_statement", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue

            setup = setup_tmpl2.format(a=a, base=base_str)
            correct_choice = f"The {desc2} increases by {r_pct}% each {unit2}."
            w1 = f"The {desc2} increases by {base_num} each {unit2}."   # base itself, not pct
            w2 = f"The {desc2} is multiplied by {r_pct} each {unit2}."  # r_pct as multiplier
            w3 = f"The initial {desc2} grows to {base_str} after one {unit2}."  # confuses f(1) meaning
            dist = make_distractors(correct_choice, [w1, w2, w3])

            ctx = (f"base = {base_str} = 1 + {r_pct}% → growth rate is {r_pct}% per {unit2}. "
                   f"CRITICAL — do NOT state the growth rate percentage in the stem. "
                   f"Ask what the base {base_str} represents. "
                   f"CRITICAL — answer choices must be plain English sentences, NO LaTeX. "
                   f"DISTRACTOR ERRORS — "
                   f"'{w1}': states the base value, not the percentage. "
                   f"'{w2}': confuses r (the rate) with b (the multiplier). "
                   f"'{w3}': misreads base as the value after one period.")
            ans = correct_choice
            return _nlf(2, params, ph, ans, dist, "mcq", ctx)

    raise RuntimeError("_d2_interpret_exponential_statement: could not generate unique params")


def _d2_minimum_from_vertex_form(rng_obj, exclude_params, variant=None):
    """g(x) = a(x−h)² + k, a>0.
    find_minimum_value — min = k. MCQ or SPR.
    find_x_at_minimum — x at min = h. MCQ or SPR."""
    v = variant or rng_obj.choice(["find_minimum_value", "find_x_at_minimum"])

    for _ in range(200):
        a = rng_obj.randint(1, 4)
        h = rng_obj.randint(-5, 5)
        k = rng_obj.randint(-6, 6)

        params = {"a": a, "h": h, "k": k,
                  "tpl": "minimum_from_vertex_form", "variant": v}
        ph = param_hash(params)
        if ph in exclude_params:
            continue

        # Format: g(x) = a(x − h)² + k
        h_str = f"x − {h}" if h >= 0 else f"x + {abs(h)}"
        a_str = "" if a == 1 else str(a)
        if k > 0:
            fn_str = f"g(x) = {a_str}({h_str})² + {k}"
        elif k < 0:
            fn_str = f"g(x) = {a_str}({h_str})² − {abs(k)}"
        else:
            fn_str = f"g(x) = {a_str}({h_str})²"

        if v == "find_minimum_value":
            ans = str(k)
            d1  = str(h)           # reported x-coord of vertex
            d2  = str(k - a)       # subtracted coefficient
            d3  = str(-k)          # negated
            dist = make_distractors(ans, [d1, d2, d3])
            exact = f"The function g is defined by {fn_str}. What is the minimum value of g?"
            ctx = (f"Vertex form a>0; min at x={h}, min value = {k}. "
                   f"CRITICAL — stem is locked (exactStem). Do NOT rewrite. "
                   f"CRITICAL — do NOT state the minimum value in the stem. "
                   f"DISTRACTOR ERRORS — "
                   f"'{h}': reported x-coord of vertex instead of y. "
                   f"'{k-a}': subtracted coefficient a. "
                   f"'{-k}': negated the minimum.")

        else:  # find_x_at_minimum
            ans = str(h)
            d1  = str(k)           # reported k (the y-min) instead of x
            d2  = str(-h)          # negated h (forgot the shift direction)
            d3  = str(h + 1)       # off-by-one
            dist = make_distractors(ans, [d1, d2, d3])
            exact = f"The function g is defined by {fn_str}. At what value of x does g reach its minimum?"
            ctx = (f"Vertex form a>0; x at min = {h}. "
                   f"CRITICAL — stem is locked (exactStem). Do NOT rewrite. "
                   f"CRITICAL — do NOT state the x-value in the stem. "
                   f"DISTRACTOR ERRORS — "
                   f"'{k}': reported minimum VALUE instead of x-position. "
                   f"'{-h}': negated h (misread shift direction). "
                   f"'{h+1}': off by one.")

        qt = rng_obj.choice(["mcq", "spr"])
        return _nlf(2, params, ph, ans, dist if qt == "mcq" else [], qt, ctx, exact_stem=exact)

    raise RuntimeError("_d2_minimum_from_vertex_form: could not generate unique params")


def _d2_x_for_min_from_factored(rng_obj, exclude_params, variant=None):
    """f(x) = (x−r)(x−s); x at minimum = (r+s)/2. MCQ or SPR."""
    v = "find_x_at_minimum"
    for _ in range(200):
        # Pick r, s with same parity so (r+s)/2 is an integer
        r = rng_obj.randint(-5, 4)
        s = rng_obj.randint(r + 1, 6)
        if (r + s) % 2 != 0:
            continue
        x_min = (r + s) // 2
        if x_min == r or x_min == s:
            continue

        params = {"r": r, "s": s, "tpl": "x_for_min_from_factored", "variant": v}
        ph = param_hash(params)
        if ph in exclude_params:
            continue

        # Format f(x) nicely
        r_str = f"x − {r}" if r >= 0 else f"x + {abs(r)}"
        s_str = f"x − {s}" if s >= 0 else f"x + {abs(s)}"
        fn_str = f"f(x) = ({r_str})({s_str})"

        ans = str(x_min)
        d1  = str(r)             # one of the zeros
        d2  = str(s)             # other zero
        d3  = str(r + s)         # sum without dividing by 2
        dist = make_distractors(ans, [d1, d2, d3])

        exact = f"The function f is defined by {fn_str}. At what value of x does f reach its minimum?"
        ctx = (f"Zeros at x={r} and x={s}; axis of symmetry = midpoint = {x_min}. "
               f"CRITICAL — stem is locked (exactStem). Do NOT rewrite. "
               f"CRITICAL — do NOT state the x-value in the stem. "
               f"DISTRACTOR ERRORS — "
               f"'{r}': reported one zero instead of the midpoint. "
               f"'{s}': reported the other zero. "
               f"'{r+s}': took the sum but forgot to divide by 2.")
        qt = rng_obj.choice(["mcq", "spr"])
        return _nlf(2, params, ph, ans, dist if qt == "mcq" else [], qt, ctx, exact_stem=exact)

    raise RuntimeError("_d2_x_for_min_from_factored: could not generate unique params")


def _d2_interpret_x_intercept_context(rng_obj, exclude_params, variant=None):
    """interpret_physical_meaning — what does h(t₀)=0 mean in context?
    identify_positive_zero — two zeros given; which is physically meaningful?"""
    v = variant or rng_obj.choice(["interpret_physical_meaning", "identify_positive_zero"])

    for _ in range(200):
        ctx_entry = rng_obj.choice(_D2_XINT_CONTEXTS)
        tag, fn, unit, t_meaning, zero_meaning = ctx_entry

        # ── interpret_physical_meaning ────────────────────────────────────────
        if v == "interpret_physical_meaning":
            # Build a quadratic h(t) = -p(t-r)(t-s), two positive roots
            r = rng_obj.randint(1, 4)
            s = rng_obj.randint(r + 1, 8)
            p = rng_obj.randint(1, 3)
            # Format: h(t) = -p(t-r)(t-s) or h(t) = -(t-r)(t-s)
            p_str = "" if p == 1 else str(p)
            r_str = f"t − {r}" if r > 0 else f"t + {abs(r)}"
            s_str = f"t − {s}" if s > 0 else f"t + {abs(s)}"
            fn_str = f"h(t) = −{p_str}({r_str})({s_str})"

            params = {"r": r, "s": s, "p": p, "tag": tag,
                      "tpl": "interpret_x_intercept_context", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue

            correct_choice = f"The values of t when {zero_meaning}."
            w1 = f"The maximum height reached, in {unit}."
            w2 = f"The initial value when t = 0."
            w3 = f"The time, in {unit}, when {t_meaning} is at its peak."
            dist = make_distractors(correct_choice, [w1, w2, w3])

            exact = (f"{fn_str}, where \\({fn}(t)\\) is the {tag.replace('_',' ')} "
                     f"and \\(t\\) is {t_meaning}.\n"
                     f"What does it mean when \\({fn}(t) = 0\\) in this context?")
            ctx = (f"h(t)=0 → {zero_meaning}. "
                   f"CRITICAL — stem is locked (exactStem). Do NOT rewrite. "
                   f"CRITICAL — answer choices must be plain English sentences, NO LaTeX. "
                   f"DISTRACTOR ERRORS — "
                   f"'{w1}': confuses x-intercepts with the maximum value. "
                   f"'{w2}': confuses x-intercepts with y-intercept (t=0). "
                   f"'{w3}': confuses zero of function with peak value.")
            ans = correct_choice
            return _nlf(2, params, ph, ans, dist, "mcq", ctx, exact_stem=exact)

        # ── identify_positive_zero ────────────────────────────────────────────
        else:
            r_pos = rng_obj.randint(1, 6)
            r_neg = rng_obj.randint(1, 4)
            # fn has zeros at r_pos and -r_neg
            params = {"r_pos": r_pos, "r_neg": -r_neg, "tag": tag,
                      "tpl": "interpret_x_intercept_context", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue

            r_str = f"t − {r_pos}" if r_pos > 0 else f"t"
            s_str = f"t + {r_neg}"
            fn_str = f"h(t) = −({r_str})({s_str})"

            correct_choice = str(r_pos)   # positive zero (physically meaningful)
            d1 = str(-r_neg)              # negative zero (not meaningful — negative time)
            d2 = str(r_pos + r_neg)       # sum of |zeros|
            d3 = str(r_pos - r_neg) if r_pos != r_neg else str(r_pos + 1)
            dist = make_distractors(correct_choice, [d1, d2, d3])

            exact = (f"{fn_str}, where \\({fn}(t)\\) is the {tag.replace('_',' ')} "
                     f"and \\(t\\) is {t_meaning}.\n"
                     f"The function has two zeros: \\(t = {r_pos}\\) and \\(t = {-r_neg}\\). "
                     f"Which zero is meaningful in this context?")
            ctx = (f"Zeros at t={r_pos} (positive → meaningful) and t={-r_neg} (negative → invalid). "
                   f"CRITICAL — stem is locked (exactStem). Do NOT rewrite. "
                   f"DISTRACTOR ERRORS — "
                   f"'{-r_neg}': negative time — physically impossible in context. "
                   f"'{r_pos+r_neg}': sum of zero magnitudes, not a zero of f. "
                   f"'{d3}': difference of zero magnitudes.")
            qt = rng_obj.choice(["mcq", "spr"])
            return _nlf(2, params, ph, correct_choice,
                        dist if qt == "mcq" else [], qt, ctx, exact_stem=exact)

    raise RuntimeError("_d2_interpret_x_intercept_context: could not generate unique params")


def _d2_exponential_from_table(rng_obj, exclude_params, variant=None):
    """identify_equation_from_table — constant-ratio table; 4 equation choices (LaTeX).
    find_missing_table_value — same table, one cell hidden."""
    v = variant or rng_obj.choice(["identify_equation_from_table", "find_missing_table_value"])

    for _ in range(200):
        a = rng_obj.randint(1, 8)
        b = rng_obj.randint(2, 4)
        xs = [0, 1, 2, 3]
        ys = [a * (b ** x) for x in xs]
        if max(ys) > 150:
            continue

        params = {"a": a, "b": b, "tpl": "exponential_from_table", "variant": v}
        ph = param_hash(params)
        if ph in exclude_params:
            continue

        # Build the table rows as text
        table_rows = "  \n".join([f"x = {x},  f(x) = {y}" for x, y in zip(xs, ys)])

        # ── identify_equation_from_table ──────────────────────────────────────
        if v == "identify_equation_from_table":
            ans  = f"\\(f(x) = {a} \\cdot {b}^x\\)"
            # Wrong: linear with slope (b-a), quadratic, wrong base
            slope_lin = ys[1] - ys[0]
            d1 = f"\\(f(x) = {a} + {slope_lin}x\\)"              # linear through (0,a)
            d2 = f"\\(f(x) = {a} \\cdot {b+1}^x\\)"              # wrong base
            d3 = f"\\(f(x) = {a+1} \\cdot {b}^x\\)"              # wrong coefficient
            dist = make_distractors(ans, [d1, d2, d3])

            exact = (f"x | f(x)\n"
                     f"{chr(10).join([f'{x} | {y}' for x,y in zip(xs,ys)])}\n\n"
                     f"Which of the following equations could define f?")
            ctx = (f"Table: {table_rows}. Constant ratio = {b} → f(x) = {a}·{b}^x. "
                   f"CRITICAL — stem must show the table as a formatted x|f(x) table. "
                   f"CRITICAL — each answer choice must be a complete LaTeX equation wrapped in \\(...\\). "
                   f"DISTRACTOR ERRORS — "
                   f"'{d1}': linear model — same y-intercept but constant difference. "
                   f"'{d2}': correct form but wrong base. "
                   f"'{d3}': correct base but wrong initial value.")
            return _nlf(2, params, ph, ans, dist, "mcq", ctx, exact_stem=exact)

        # ── find_missing_table_value ──────────────────────────────────────────
        else:
            # Hide one of x=1,2,3 entries
            hide_idx = rng_obj.randint(1, 3)
            hidden_x = xs[hide_idx]
            hidden_y = ys[hide_idx]
            known = [(x, y) for i, (x, y) in enumerate(zip(xs, ys)) if i != hide_idx]

            ans = str(hidden_y)
            d1  = str(hidden_y + b)          # added b instead of multiplied
            d2  = str(ys[hide_idx - 1] + b)  # added b linearly
            d3  = str(hidden_y * 2)           # doubled
            dist = make_distractors(ans, [d1, d2, d3])

            known_rows = "\n".join([f"{x} | {y}" for x, y in known])
            exact = (f"x | f(x)\n{known_rows}\n{hidden_x} | ?\n\n"
                     f"What is the missing value in the table?")
            ctx = (f"Table: {table_rows}. Pattern: each row × {b}. "
                   f"f({hidden_x}) = {a}·{b}^{hidden_x} = {hidden_y}. "
                   f"CRITICAL — stem is locked (exactStem). Do NOT rewrite. "
                   f"DISTRACTOR ERRORS — "
                   f"'{d1}': added {b} instead of multiplying. "
                   f"'{d2}': applied linear (+{b}) pattern. "
                   f"'{d3}': doubled the previous value.")
            qt = rng_obj.choice(["mcq", "spr"])
            return _nlf(2, params, ph, ans, dist if qt == "mcq" else [], qt, ctx, exact_stem=exact)

    raise RuntimeError("_d2_exponential_from_table: could not generate unique params")


def _d2_identify_quadratic_from_table(rng_obj, exclude_params, variant=None):
    """identify_equation_from_table — constant-second-differences → quadratic.
    find_missing_value — extend table using second-difference pattern. MCQ or SPR."""
    v = variant or rng_obj.choice(["identify_equation_from_table", "find_missing_value"])

    for _ in range(200):
        # f(x) = ax² + bx + c; pick small a so values stay < 100
        a_coef = rng_obj.randint(1, 3)
        b_coef = rng_obj.randint(-3, 3)
        c_coef = rng_obj.randint(0, 6)
        xs = [0, 1, 2, 3]
        ys = [a_coef * x**2 + b_coef * x + c_coef for x in xs]
        if max(abs(y) for y in ys) > 100:
            continue
        # Second differences must be 2·a_coef (constant check)
        d1_arr = [ys[i+1] - ys[i] for i in range(3)]
        d2_arr = [d1_arr[i+1] - d1_arr[i] for i in range(2)]
        if d2_arr[0] != d2_arr[1] or d2_arr[0] != 2 * a_coef:
            continue

        params = {"a": a_coef, "b": b_coef, "c": c_coef,
                  "tpl": "identify_quadratic_from_table", "variant": v}
        ph = param_hash(params)
        if ph in exclude_params:
            continue

        # ── identify_equation_from_table ──────────────────────────────────────
        if v == "identify_equation_from_table":
            # Format the correct equation
            a_s = "" if a_coef == 1 else str(a_coef)
            if b_coef == 1:
                b_part = " + x"
            elif b_coef == -1:
                b_part = " − x"
            elif b_coef > 1:
                b_part = f" + {b_coef}x"
            elif b_coef < -1:
                b_part = f" − {abs(b_coef)}x"
            else:
                b_part = ""
            c_part = f" + {c_coef}" if c_coef > 0 else (f" − {abs(c_coef)}" if c_coef < 0 else "")
            correct_eq = f"\\(f(x) = {a_s}x^2{b_part}{c_part}\\)"

            # Distractors: linear, wrong a, wrong c
            slope_lin = ys[1] - ys[0]
            sl_s = "x" if slope_lin == 1 else ("-x" if slope_lin == -1 else f"{slope_lin}x")
            c_lin = f" + {c_coef}" if c_coef > 0 else (f" − {abs(c_coef)}" if c_coef < 0 else "")
            w1 = f"\\(f(x) = {sl_s}{c_lin}\\)"
            a2 = a_coef + 1
            a2_s = "" if a2 == 1 else str(a2)
            w2 = f"\\(f(x) = {a2_s}x^2{b_part}{c_part}\\)"
            c2 = c_coef + 1
            c2_part = f" + {c2}" if c2 > 0 else (f" − {abs(c2)}" if c2 < 0 else "")
            w3 = f"\\(f(x) = {a_s}x^2{b_part}{c2_part}\\)"
            dist = make_distractors(correct_eq, [w1, w2, w3])

            table_rows = "\n".join([f"{x} | {y}" for x, y in zip(xs, ys)])
            exact = (f"x | f(x)\n{table_rows}\n\n"
                     f"Which of the following equations could define f?")
            ctx = (f"Table: {', '.join([f'f({x})={y}' for x,y in zip(xs,ys)])}. "
                   f"Second differences = {2*a_coef} → quadratic with a={a_coef}. "
                   f"CRITICAL — stem must show the table as a formatted x|f(x) table. "
                   f"CRITICAL — each answer choice must be wrapped in \\(...\\). "
                   f"DISTRACTOR ERRORS — "
                   f"'{w1}': linear model. "
                   f"'{w2}': wrong leading coefficient. "
                   f"'{w3}': wrong constant term.")
            return _nlf(2, params, ph, correct_eq, dist, "mcq", ctx, exact_stem=exact)

        # ── find_missing_value ────────────────────────────────────────────────
        else:
            # Extend to x=4 using second-difference pattern
            next_x = 4
            next_y = a_coef * 16 + b_coef * 4 + c_coef
            if abs(next_y) > 120:
                continue

            # Show x=0..3, hide x=4
            known_rows = "\n".join([f"{x} | {y}" for x, y in zip(xs, ys)])
            ans    = str(next_y)
            last_fd = d1_arr[-1]           # last first difference, e.g. 16
            next_fd = last_fd + 2*a_coef   # correct next first difference, e.g. 22

            # d1: linear-extrapolation error — student assumes last first diff stays constant
            # f(4) = f(3) + last_fd  (NOT f(4) + last_fd, which would be nonsensical)
            d1 = str(ys[-1] + last_fd)
            # d2 / d3: arithmetic errors when applying the second difference
            d2 = str(next_y + a_coef)
            d3 = str(next_y - a_coef)
            dist = make_distractors(ans, [d1, d2, d3])

            exact = (f"x | f(x)\n{known_rows}\n{next_x} | ?\n\n"
                     f"What is the missing value in the table?")
            ctx = (f"Table: {', '.join([f'f({x})={y}' for x,y in zip(xs,ys)])}. "
                   f"First differences: {', '.join(map(str, d1_arr))} (each increases by {2*a_coef}). "
                   f"Second difference is CONSTANT at {2*a_coef}. "
                   f"Next first difference = {last_fd} + {2*a_coef} = {next_fd}. "
                   f"f({next_x}) = {ys[-1]} + {next_fd} = {next_y}. "
                   f"CRITICAL — stem is locked (exactStem). "
                   f"CRITICAL — in the solution, write: 'The second difference is constant at "
                   f"{2*a_coef}; first differences are {', '.join(map(str, d1_arr))}; "
                   f"next first difference = {last_fd} + {2*a_coef} = {next_fd}; "
                   f"f({next_x}) = {ys[-1]} + {next_fd} = {next_y}.' "
                   f"DISTRACTOR ERRORS — "
                   f"'{d1}': linear extrapolation error — assumed first difference stays constant "
                   f"at {last_fd}: f({next_x}) = f({xs[-1]}) + {last_fd} = {ys[-1]} + {last_fd} = {d1}. "
                   f"'{d2}': arithmetic error — off by {a_coef} when computing next first difference. "
                   f"'{d3}': arithmetic error — off by {a_coef} in the other direction.")
            qt = rng_obj.choice(["mcq", "spr"])
            return _nlf(2, params, ph, ans, dist if qt == "mcq" else [], qt, ctx, exact_stem=exact)

    raise RuntimeError("_d2_identify_quadratic_from_table: could not generate unique params")


def _d2_exponential_growth_rate(rng_obj, exclude_params, variant=None):
    """find_growth_percentage — f(x)=a(1+r)ˣ; growth rate as %. MCQ.
    interpret_growth_rate — which statement correctly describes the rate? MCQ."""
    v = variant or rng_obj.choice(["find_growth_percentage", "interpret_growth_rate"])

    for _ in range(200):
        ctx_entry = rng_obj.choice(_D2_GROWTH_CONTEXTS)
        tag, fn, unit, desc, setup_tmpl = ctx_entry

        a = rng_obj.randint(50, 500)
        r_pct = rng_obj.choice([5, 8, 10, 12, 15, 20, 25])
        r = r_pct / 100
        base = round(1 + r, 2)
        base_str = str(base)

        params = {"a": a, "r_pct": r_pct, "base": base_str, "tag": tag,
                  "tpl": "exponential_growth_rate", "variant": v}
        ph = param_hash(params)
        if ph in exclude_params:
            continue

        setup = setup_tmpl.format(a=a, base=base_str)

        # ── find_growth_percentage ────────────────────────────────────────────
        if v == "find_growth_percentage":
            ans = f"{r_pct}%"
            # Wrong pct choices
            cands = [f"{p}%" for p in [5,8,10,12,15,20,25] if p != r_pct]
            rng_obj.shuffle(cands)
            dist = make_distractors(ans, cands[:3])

            ctx = (f"base = {base_str} = 1 + {r_pct}% → growth rate is {r_pct}% per {unit}. "
                   f"{setup} "
                   f"Ask: what is the percentage growth rate per {unit}? "
                   f"CRITICAL — do NOT state the percentage in the stem. "
                   f"DISTRACTOR ERRORS — nearby percentages that don't match the base {base_str}.")
            return _nlf(2, params, ph, ans, dist, "mcq", ctx)

        # ── interpret_growth_rate ─────────────────────────────────────────────
        else:
            correct_choice = f"The {desc} increases by {r_pct}% each {unit}."
            w1 = f"The {desc} increases by {base_str} each {unit}."
            w2 = f"The {desc} decreases by {r_pct}% each {unit}."
            w3 = f"The {desc} doubles every {r_pct} {unit}."
            dist = make_distractors(correct_choice, [w1, w2, w3])

            ctx = (f"base = {base_str} → {r_pct}% growth per {unit}. {setup} "
                   f"Ask which statement correctly describes the growth rate. "
                   f"CRITICAL — do NOT state the percentage in the stem. "
                   f"CRITICAL — answer choices must be plain English sentences, NO LaTeX. "
                   f"DISTRACTOR ERRORS — "
                   f"'{w1}': states the multiplicative factor, not the percentage. "
                   f"'{w2}': says 'decreases' when it actually increases. "
                   f"'{w3}': describes doubling time, which is incorrect here.")
            ans = correct_choice
            return _nlf(2, params, ph, ans, dist, "mcq", ctx)

    raise RuntimeError("_d2_exponential_growth_rate: could not generate unique params")


def _d2_function_table_shift(rng_obj, exclude_params, variant=None):
    """identify_transformed_table — given f-table; which table matches g(x)=f(x)−k? MCQ.
    find_specific_shifted_value — given f(a)=v; what is f(a)+k? SPR."""
    v = variant or rng_obj.choice(["identify_transformed_table", "find_specific_shifted_value"])

    for _ in range(200):
        # ── find_specific_shifted_value ───────────────────────────────────────
        # Design: give a 4-row f-table; define g(x) = f(x) ± k; ask for g(target_x).
        # Student must locate f(target_x) in the table then apply the shift.
        # Never state f(target_x) directly in the stem — that would leak the answer.
        if v == "find_specific_shifted_value":
            all_xs = list(range(-4, 8))
            rng_obj.shuffle(all_xs)
            xs_t = sorted(all_xs[:4])
            ys_f = [rng_obj.randint(2, 20) for _ in range(4)]
            k = rng_obj.randint(2, 8)
            ask_idx = rng_obj.randint(0, 3)
            ask_x   = xs_t[ask_idx]
            f_val   = ys_f[ask_idx]
            direction = rng_obj.choice(["+", "-"])
            ans_val   = f_val + k if direction == "+" else f_val - k

            params = {"xs": xs_t, "ys_f": ys_f, "k": k,
                      "ask_idx": ask_idx, "direction": direction,
                      "tpl": "function_table_shift", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue

            g_def     = f"g(x) = f(x) + {k}" if direction == "+" else f"g(x) = f(x) − {k}"
            table_rows = "\n".join([f"{x} | {y}" for x, y in zip(xs_t, ys_f)])
            exact = (f"x | f(x)\n{table_rows}\n\n"
                     f"The function g is defined by {g_def}.\n"
                     f"What is the value of g({ask_x})?")
            ans = str(ans_val)
            op  = "+" if direction == "+" else "−"
            ctx = (f"g({ask_x}) = f({ask_x}) {op} {k} = {f_val} {op} {k} = {ans_val}. "
                   f"CRITICAL — stem is locked (exactStem). "
                   f"CRITICAL — do NOT state f({ask_x}) = {f_val} in the stem or solution opening; "
                   f"the student must locate it by reading the table row where x = {ask_x}. "
                   f"The solution should: (1) identify the row x = {ask_x}, f(x) = {f_val}; "
                   f"(2) substitute into g: g({ask_x}) = {f_val} {op} {k} = {ans_val}.")
            return _nlf(2, params, ph, ans, [], "spr", ctx, exact_stem=exact)

        # ── identify_transformed_table ────────────────────────────────────────
        else:
            # 3-row f-table, g(x) = f(x) - k
            xs_t = [rng_obj.randint(-2, 0), rng_obj.randint(1, 2), rng_obj.randint(3, 5)]
            if len(set(xs_t)) < 3:
                continue
            xs_t.sort()
            ys_f = [rng_obj.randint(2, 15) for _ in range(3)]
            k = rng_obj.randint(2, 6)
            ys_g = [y - k for y in ys_f]

            params = {"xs": xs_t, "ys_f": ys_f, "k": k,
                      "tpl": "function_table_shift", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue

            def fmt_table(xs, ys):
                return " | ".join([f"({x},{y})" for x, y in zip(xs, ys)])

            correct_table = fmt_table(xs_t, ys_g)
            # Distractors: +k instead of -k, *k, values of f unchanged
            w1 = fmt_table(xs_t, [y + k for y in ys_f])        # added k instead of subtracting
            w2 = fmt_table(xs_t, ys_f)                          # unchanged (forgot to apply shift)
            w3 = fmt_table(xs_t, [y - k + 1 for y in ys_f])    # off by 1
            dist = make_distractors(correct_table, [w1, w2, w3])

            f_rows = "\n".join([f"{x} | {y}" for x, y in zip(xs_t, ys_f)])

            # exactStem: only f(x) table + question; answer choices (g tables) appear as A/B/C/D
            exact = (f"x | f(x)\n{f_rows}\n\n"
                     f"The function g is defined by g(x) = f(x) − {k}.\n"
                     f"Which table of values could represent g?")
            ctx = (f"g(x) = f(x) − {k}: subtract {k} from each f-value. "
                   f"Correct g-table: {correct_table}. "
                   f"CRITICAL — stem is locked (exactStem). Do NOT rewrite or add the answer tables into the stem. "
                   f"The answer choices (compact table strings) are the 4 g-tables to compare. "
                   f"DISTRACTOR ERRORS — "
                   f"'{w1}': added {k} instead of subtracting. "
                   f"'{w2}': left values unchanged (forgot to apply shift). "
                   f"'{w3}': off by 1 in each row.")
            ans = correct_table
            return _nlf(2, params, ph, ans, dist, "mcq", ctx, exact_stem=exact)

    raise RuntimeError("_d2_function_table_shift: could not generate unique params")


def _d2_graph_read_intercept_nonlinear(rng_obj, exclude_params, variant=None):
    """find_y_intercept — curve shown; which ordered pair is the y-intercept? MCQ.
    find_x_intercept — same curve; which ordered pair is the x-intercept? MCQ."""
    v = variant or rng_obj.choice(["find_y_intercept", "find_x_intercept"])

    for _ in range(200):
        a = rng_obj.randint(1, 4)
        b = rng_obj.randint(2, 3)

        if v == "find_y_intercept":
            # f(x) = a·bˣ (no shift) — y-intercept = (0, a), always clean
            c = 0
            y_int = a
            x_range = [-2, 4]

            params = {"a": a, "b": b, "c": c, "tpl": "graph_read_intercept_nonlinear", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue

            diag = {
                "type": "nonlinear_curve",
                "curveType": "exponential",
                "a": a, "b": b, "c": c,
                "x_range": x_range,
                "labeled_points": [],
                "show_y_intercept": True,
            }
            ans = f"(0, {y_int})"
            d1  = f"(0, {a * b})"       # f(1) instead of f(0)
            d2  = f"({a}, 0)"           # swapped coordinates
            d3  = f"(0, {a + b})"       # confused a+b with a
            dist = make_distractors(ans, [d1, d2, d3])
            ctx  = (f"f(0) = {a}·{b}^0 = {a}. y-intercept = (0, {y_int}). "
                    f"CRITICAL — do NOT state the y-intercept value in the stem. "
                    f"Ask which ordered pair represents where the graph crosses the y-axis. "
                    f"DISTRACTOR ERRORS — "
                    f"'{d1}': read f(1) = {a*b} instead of f(0). "
                    f"'{d2}': swapped x and y coordinates. "
                    f"'{d3}': confused a+b with a.")
            return _nlf(2, params, ph, ans, dist, "mcq", ctx, diagram=diag)

        else:  # find_x_intercept
            # Derive c so x-intercept is a clean integer:
            # f(x) = a·bˣ + c = 0 → c = -a·b^x_int
            x_int = rng_obj.randint(1, 3)
            c = -(a * (b ** x_int))
            y_int = a + c    # f(0) = a + c (will be negative — graph starts below axis at x=0)
            if c >= 0:
                continue     # sanity check

            params = {"a": a, "b": b, "c": c, "x_int": x_int,
                      "tpl": "graph_read_intercept_nonlinear", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue

            diag = {
                "type": "nonlinear_curve",
                "curveType": "exponential",
                "a": a, "b": b, "c": c,
                "x_range": [-1, x_int + 2],
                "labeled_points": [],
                "show_y_intercept": False,
            }
            ans  = f"({x_int}, 0)"
            d1   = f"(0, {y_int})"           # y-intercept instead
            d2   = f"({x_int + 1}, 0)"       # one step too far
            d3   = f"({x_int - 1}, 0)"       # one step too early
            dist = make_distractors(ans, [d1, d2, d3])
            ctx  = (f"f(x)=0 when {a}·{b}^x={-c}, 2^x={-c//a}, x={x_int}. x-intercept=({x_int},0). "
                    f"CRITICAL — do NOT state the x-intercept in the stem. "
                    f"Ask which ordered pair represents where the graph crosses the x-axis. "
                    f"DISTRACTOR ERRORS — "
                    f"'{d1}': reported y-intercept instead. "
                    f"'{d2}': read x={x_int+1} from the graph. "
                    f"'{d3}': read x={x_int-1} from the graph.")
            return _nlf(2, params, ph, ans, dist, "mcq", ctx, diagram=diag)

    raise RuntimeError("_d2_graph_read_intercept_nonlinear: could not generate unique params")


# function_composition — removed: only 1 Hard Bluebook example (complex abs-value + rational);
# current d2 implementation (simple quadratic+linear) does not match that structure.
# Redesign as d3 when additional Bluebook examples are available.


# inequality_system_nonlinear — removed: zero Bluebook questions observed across all 414 screenshots.


def _d2_domain_range_graph(rng_obj, exclude_params, variant=None):
    """find_range_parabola 📊 — parabola on graph; which inequality is the range? MCQ.
    find_domain_radical — f(x)=√(x−a); what is the domain? MCQ."""
    v = variant or rng_obj.choice(["find_range_parabola", "find_domain_radical"])

    for _ in range(200):
        # ── find_range_parabola ───────────────────────────────────────────────
        if v == "find_range_parabola":
            a = rng_obj.choice([-2, -1, 1, 2])
            h = rng_obj.randint(-3, 3)
            k = rng_obj.randint(-4, 4)
            y_int = a * h ** 2 + k
            if abs(y_int) > 6:
                continue

            params = {"a": a, "h": h, "k": k,
                      "tpl": "domain_range_graph", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue

            if a > 0:
                ans = f"y ≥ {k}"
                d1  = f"y ≤ {k}"      # flipped direction
                d2  = f"y ≥ {h}"      # confused x-coord with y-coord of vertex
                d3  = "All real numbers"
            else:
                ans = f"y ≤ {k}"
                d1  = f"y ≥ {k}"      # flipped direction
                d2  = f"y ≤ {h}"      # confused x-coord with y-coord
                d3  = "All real numbers"

            # Avoid collision when h == k (d2 would equal ans)
            if d2 == ans:
                d2 = f"y ≥ {k - 1}" if a > 0 else f"y ≤ {k + 1}"

            dist = make_distractors(ans, [d1, d2, d3])
            diag = {
                "type": "parabola",
                "a": a, "h": h, "k": k,
                "vertex": [h, k],
                "x_intercepts": None,
                "y_intercept": y_int,
                "vertex_label": True,   # student reads (h,k) from the graph
            }
            direction = "minimum" if a > 0 else "maximum"
            exact = "According to the graph, which of the following represents the range of f?"
            ctx = (f"Parabola vertex ({h},{k}), {'opens up' if a>0 else 'opens down'} → range: {ans}. "
                   f"CRITICAL — stem is locked (exactStem). Do NOT state the vertex or range value in the stem. "
                   f"CRITICAL — answer choices must be plain inequality strings (e.g. '{ans}'), NO LaTeX. "
                   f"DISTRACTOR ERRORS — "
                   f"'{d1}': reversed the inequality direction. "
                   f"'{d2}': used the x-coordinate {h} of the vertex instead of the y-coordinate {k}. "
                   f"'All real numbers': ignored the {direction} imposed by the vertex.")
            return _nlf(2, params, ph, ans, dist, "mcq", ctx, exact_stem=exact, diagram=diag)

        # ── find_domain_radical ───────────────────────────────────────────────
        else:
            a = rng_obj.randint(-4, 5)

            params = {"a": a, "tpl": "domain_range_graph", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue

            # Format function string
            if a > 0:
                fn_latex   = f"\\sqrt{{x - {a}}}"
                fn_display = f"√(x − {a})"
            elif a < 0:
                fn_latex   = f"\\sqrt{{x + {abs(a)}}}"
                fn_display = f"√(x + {abs(a)})"
            else:
                fn_latex   = "\\sqrt{x}"
                fn_display = "√x"

            ans = f"x ≥ {a}"
            d1  = f"x > {a}"           # excluded endpoint (√0=0 is defined)
            d2  = "x ≥ 0" if a != 0 else "x ≥ 1"   # forgot horizontal shift
            d3  = "All real numbers"
            # Avoid collision when a == 0 already handled above; also guard d2 == ans
            if d2 == ans:
                d2 = f"x ≥ {a - 1}"
            dist = make_distractors(ans, [d1, d2, d3])

            exact = f"The function f is defined by \\(f(x) = {fn_latex}\\). What is the domain of f?"
            shift_note = (f"forgot the horizontal shift — the radicand is x − {a}, not x"
                          if a != 0 else "correct formula for f(x)=√x, but excluded the endpoint")
            ctx = (f"Domain of f(x)={fn_display}: radicand x − {a} ≥ 0 → x ≥ {a}. "
                   f"CRITICAL — stem is locked (exactStem). "
                   f"CRITICAL — answer choices must be plain inequality strings, NO LaTeX. "
                   f"DISTRACTOR ERRORS — "
                   f"'{d1}': excluded x={a} — but √0=0 is defined, so x={a} is valid. "
                   f"'{d2}': {shift_note}. "
                   f"'All real numbers': ignored the restriction that the radicand must be ≥ 0.")
            return _nlf(2, params, ph, ans, dist, "mcq", ctx, exact_stem=exact)

    raise RuntimeError("_d2_domain_range_graph: could not generate unique params")


_D2 = {
    "evaluate_exponential_zero":        {"fn": _d2_evaluate_exponential_zero,        "variants": ["find_initial_value", "interpret_initial_value"]},
    "interpret_exponential_statement":  {"fn": _d2_interpret_exponential_statement,  "variants": ["interpret_output_value", "interpret_growth_factor"]},
    "minimum_from_vertex_form":         {"fn": _d2_minimum_from_vertex_form,         "variants": ["find_minimum_value", "find_x_at_minimum"]},
    "x_for_min_from_factored":          {"fn": _d2_x_for_min_from_factored,          "variants": ["find_x_at_minimum"]},
    "interpret_x_intercept_context":    {"fn": _d2_interpret_x_intercept_context,    "variants": ["interpret_physical_meaning", "identify_positive_zero"]},
    "exponential_from_table":           {"fn": _d2_exponential_from_table,           "variants": ["identify_equation_from_table", "find_missing_table_value"]},
    "identify_quadratic_from_table":    {"fn": _d2_identify_quadratic_from_table,    "variants": ["identify_equation_from_table", "find_missing_value"]},
    "exponential_growth_rate":          {"fn": _d2_exponential_growth_rate,          "variants": ["find_growth_percentage", "interpret_growth_rate"]},
    "function_table_shift":             {"fn": _d2_function_table_shift,             "variants": ["identify_transformed_table", "find_specific_shifted_value"]},
    "graph_read_intercept_nonlinear":   {"fn": _d2_graph_read_intercept_nonlinear,   "variants": ["find_y_intercept", "find_x_intercept"]},
    "domain_range_graph":               {"fn": _d2_domain_range_graph,               "variants": ["find_range_parabola", "find_domain_radical"]},
}


# ═══════════════════════════════════════════════════════════════════════════════
# D3 TEMPLATES  (Hard — 11 templates) — Phase 3
# ═══════════════════════════════════════════════════════════════════════════════

def _d3_max_in_context(rng_obj, exclude_params, variant=None):
    """find_x_at_max — axis of symmetry x=−b/2a. MCQ or SPR.
    find_max_value  — evaluate f at axis. MCQ or SPR."""
    v = variant or rng_obj.choice(["find_x_at_max", "find_max_value"])

    for _ in range(200):
        a = rng_obj.choice([-1, -2, -3, -4])
        # Force b so that x_max = -b/(2a) is a small positive integer
        x_max = rng_obj.randint(1, 6)
        b = -2 * a * x_max          # b = -2a·x_max → x_max = -b/(2a) ✓
        c = rng_obj.randint(-5, 15)
        f_max = a * x_max**2 + b * x_max + c

        if abs(f_max) > 100:
            continue

        params = {"a": a, "b": b, "c": c, "tpl": "max_in_context", "variant": v}
        ph = param_hash(params)
        if ph in exclude_params:
            continue

        c_str = f" + {c}" if c > 0 else (f" − {abs(c)}" if c < 0 else "")
        b_str = f" + {abs(b)}x" if b > 0 else (f" − {abs(b)}x" if b < 0 else "")
        fn_str = f"f(x) = {abs(a)}x²{b_str}{c_str}" if a == -1 else \
                 f"f(x) = −{abs(a)}x²{b_str}{c_str}"

        if v == "find_x_at_max":
            ans = str(x_max)
            d1  = str(b)              # used b directly
            d2  = str(-b)             # forgot the negative
            d3  = str(2 * x_max)      # forgot to divide by 2
            dist = make_distractors(ans, [d1, d2, d3])
            ctx = (f"f(x) = {a}x² + {b}x + {c}. "
                   f"x at max = −b/(2a) = −{b}/(2·{a}) = {x_max}. "
                   f"CRITICAL — do NOT state x = {x_max} in the stem. "
                   f"DISTRACTOR ERRORS — "
                   f"'{d1}': used b = {b} directly without formula. "
                   f"'{d2}': forgot the negative sign in −b/2a. "
                   f"'{d3}': used −b/a, forgot to divide by 2.")
        else:
            ans = str(f_max)
            d1  = str(x_max)          # reported x, not f(x)
            d2  = str(c)              # returned c (y-intercept)
            d3  = str(f_max + abs(a)) # off by a
            dist = make_distractors(ans, [d1, d2, d3])
            ctx = (f"f(x) = {a}x² + {b}x + {c}. "
                   f"x at max = {x_max}; f({x_max}) = {a}·{x_max}² + {b}·{x_max} + {c} = {f_max}. "
                   f"CRITICAL — do NOT state the maximum value in the stem. "
                   f"DISTRACTOR ERRORS — "
                   f"'{d1}': reported x-value {x_max} instead of f({x_max}). "
                   f"'{d2}': returned the y-intercept c = {c}. "
                   f"'{d3}': arithmetic error computing f({x_max}).")

        qt = rng_obj.choice(["mcq", "spr"])
        return _nlf(3, params, ph, ans, dist if qt == "mcq" else [], qt, ctx)

    raise RuntimeError("_d3_max_in_context: could not generate unique params")


def _d3_compound_function_max(rng_obj, exclude_params, variant=None):
    """find_max_of_compound — max(g)=max(f)+k. MCQ.
    find_shift_from_max  — given max(f) and max(g), find k. MCQ."""
    v = variant or rng_obj.choice(["find_max_of_compound", "find_shift_from_max"])

    for _ in range(200):
        f_max = rng_obj.randint(5, 20)
        k     = rng_obj.randint(2, 10)
        g_max = f_max + k

        params = {"f_max": f_max, "k": k, "tpl": "compound_function_max", "variant": v}
        ph = param_hash(params)
        if ph in exclude_params:
            continue

        if v == "find_max_of_compound":
            ans  = str(g_max)
            d1   = str(f_max - k)    # subtracted instead of adding
            d2   = str(f_max)        # ignored the shift
            d3   = str(f_max * k)    # multiplied
            dist = make_distractors(ans, [d1, d2, d3])
            exact = (f"The function f has a maximum value of {f_max}. "
                     f"The function g is defined by g(x) = f(x) + {k}. "
                     f"What is the maximum value of g?")
            ctx = (f"max(g) = max(f) + {k} = {f_max} + {k} = {g_max}. "
                   f"CRITICAL — stem is locked (exactStem). "
                   f"DISTRACTOR ERRORS — "
                   f"'{d1}': subtracted k instead of adding. "
                   f"'{d2}': ignored the shift, returned max(f). "
                   f"'{d3}': multiplied max(f) by k.")
        else:
            ans  = str(k)
            d1   = str(g_max)        # returned max(g) not k
            d2   = str(-k)           # wrong sign
            d3   = str(f_max + g_max) # added both maxima
            dist = make_distractors(ans, [d1, d2, d3])
            exact = (f"The function f has a maximum value of {f_max}. "
                     f"The function g is defined by g(x) = f(x) + k, where k is a constant. "
                     f"If the maximum value of g is {g_max}, what is the value of k?")
            ctx = (f"max(g) = max(f) + k → {g_max} = {f_max} + k → k = {k}. "
                   f"CRITICAL — stem is locked (exactStem). "
                   f"DISTRACTOR ERRORS — "
                   f"'{d1}': returned max(g) = {g_max} instead of k. "
                   f"'{d2}': computed {f_max} − {g_max} (wrong direction). "
                   f"'{d3}': added the two maxima together.")

        return _nlf(3, params, ph, ans, dist, "mcq", ctx, exact_stem=exact)

    raise RuntimeError("_d3_compound_function_max: could not generate unique params")


def _d3_vertex_from_zeros(rng_obj, exclude_params, variant=None):
    """find_vertex_x — midpoint of two zeros. MCQ or SPR.
    find_vertex_y  — evaluate factored form at vertex x. MCQ."""
    v = variant or rng_obj.choice(["find_vertex_x", "find_vertex_y"])

    for _ in range(200):
        r1 = rng_obj.randint(-5, 3)
        r2 = rng_obj.randint(r1 + 2, 8)
        if (r1 + r2) % 2 != 0:   # ensure integer vertex_x
            continue
        vx = (r1 + r2) // 2
        a  = rng_obj.choice([1, 2, -1, -2])
        vy = a * (vx - r1) * (vx - r2)

        params = {"r1": r1, "r2": r2, "a": a, "tpl": "vertex_from_zeros", "variant": v}
        ph = param_hash(params)
        if ph in exclude_params:
            continue

        if v == "find_vertex_x":
            ans  = str(vx)
            d1   = str(r1)
            d2   = str(r2)
            d3   = str(r2 - r1)      # computed difference, not midpoint
            dist = make_distractors(ans, [d1, d2, d3])
            exact = (f"The quadratic function f satisfies f({r1}) = 0 and f({r2}) = 0. "
                     f"What is the x-coordinate of the vertex of the graph of y = f(x)?")
            ctx = (f"Zeros at x={r1} and x={r2}; vertex x = ({r1}+{r2})/2 = {vx}. "
                   f"CRITICAL — stem is locked (exactStem). Do NOT rewrite it. "
                   f"DISTRACTOR ERRORS — "
                   f"'{r1}': used the first zero directly. "
                   f"'{r2}': used the second zero directly. "
                   f"'{r2-r1}': computed the distance between zeros instead of midpoint.")
            qt = rng_obj.choice(["mcq", "spr"])
            return _nlf(3, params, ph, ans, dist if qt == "mcq" else [], qt, ctx, exact_stem=exact)

        else:  # find_vertex_y
            # Express answer in terms of a where possible
            vy_over_a = (vx - r1) * (vx - r2)   # always negative (vertex between roots)
            ans_str = str(vy)
            # Distractors: wrong vertex_x → wrong vy
            d1 = str(a * (r1 - r1) * (r1 - r2))    # evaluated at r1 → 0
            d2 = str(a * (r2 - r1) * (r2 - r2))    # evaluated at r2 → 0
            d3 = str(-vy)                            # sign error
            dist = make_distractors(ans_str, [d1, d2, d3])
            a_str = "" if a == 1 else ("-" if a == -1 else str(a))
            r1_str = f"x + {abs(r1)}" if r1 < 0 else f"x − {r1}"
            r2_str = f"x + {abs(r2)}" if r2 < 0 else f"x − {r2}"
            exact = (f"The function f is defined by f(x) = {a_str}({r1_str})({r2_str}). "
                     f"What is the y-coordinate of the vertex of the graph of y = f(x)?")
            ctx = (f"vertex_x = ({r1}+{r2})/2 = {vx}; "
                   f"f({vx}) = {a}·({vx}-{r1})·({vx}-{r2}) = {a}·{vx-r1}·{vx-r2} = {vy}. "
                   f"CRITICAL — stem is locked (exactStem). "
                   f"DISTRACTOR ERRORS — "
                   f"'0': evaluated f at a zero (r1 or r2) instead of vertex. "
                   f"'{-vy}': sign error when multiplying factors.")
            return _nlf(3, params, ph, ans_str, dist, "mcq", ctx, exact_stem=exact)

    raise RuntimeError("_d3_vertex_from_zeros: could not generate unique params")


def _d3_identify_equivalent_form(rng_obj, exclude_params, variant=None):
    """reveal_maximum — vertex form shows min/max as explicit constant. MCQ.
    reveal_zeros   — factored form reveals x-intercepts. MCQ."""
    v = variant or rng_obj.choice(["reveal_maximum", "reveal_zeros"])

    for _ in range(200):
        # f(x) = (x-h)² + k  (vertex form, a=1 for simplicity)
        h = rng_obj.randint(-4, 4)
        k = rng_obj.randint(-8, 8)
        # Expanded: x² - 2hx + (h²+k)
        b_coef = -2 * h
        c_coef = h**2 + k

        # For reveal_zeros, ensure real roots (discriminant ≥ 0)
        if v == "reveal_zeros" and k > 0:
            continue
        if v == "reveal_zeros":
            disc = b_coef**2 - 4 * c_coef
            if disc < 0:
                continue
            sq = _math.sqrt(disc)
            if abs(sq - round(sq)) > 0.001:
                continue
            sq = int(round(sq))
            r1_z = (-b_coef - sq) // 2
            r2_z = (-b_coef + sq) // 2
            if (-b_coef - sq) % 2 != 0:
                continue

        params = {"h": h, "k": k, "tpl": "identify_equivalent_form", "variant": v}
        ph = param_hash(params)
        if ph in exclude_params:
            continue

        b_str = f" + {b_coef}x" if b_coef > 0 else (f" − {abs(b_coef)}x" if b_coef < 0 else "")
        c_str = f" + {c_coef}" if c_coef > 0 else (f" − {abs(c_coef)}" if c_coef < 0 else "")
        std_form = f"f(x) = x²{b_str}{c_str}"

        h_str = f"x − {h}" if h > 0 else (f"x + {abs(h)}" if h < 0 else "x")
        k_str = f" + {k}" if k > 0 else (f" − {abs(k)}" if k < 0 else "")
        vertex_form = f"f(x) = ({h_str})²{k_str}"

        if v == "reveal_maximum":
            ans  = vertex_form
            # Wrong choices: standard form (no explicit constant), wrong completion
            k2   = k + rng_obj.randint(1, 3)
            h2   = h + rng_obj.randint(1, 2)
            k2_str = f" + {k2}" if k2 > 0 else (f" − {abs(k2)}" if k2 < 0 else "")
            h2_str = f"x − {h2}" if h2 > 0 else f"x + {abs(h2)}"
            w1 = std_form
            w2 = f"f(x) = ({h2_str})²{k_str}"
            w3 = f"f(x) = ({h_str})²{k2_str}"
            dist = make_distractors(ans, [w1, w2, w3])
            minmax = "minimum" if True else "maximum"  # a=1 → opens up → minimum
            exact = (f"{std_form}\n"
                     f"Which of the following equivalent forms of f most clearly shows "
                     f"the minimum value of f as a constant?")
            ctx = (f"Complete the square: {std_form} → {vertex_form}. "
                   f"The minimum value {k} appears as the constant in vertex form. "
                   f"CRITICAL — stem is locked (exactStem). "
                   f"DISTRACTOR ERRORS — "
                   f"'{w1}': standard form — minimum not immediately visible. "
                   f"'{w2}': wrong h value in the square. "
                   f"'{w3}': wrong k value after completing the square.")

        else:  # reveal_zeros
            r1_str_f = f"x − {r1_z}" if r1_z > 0 else (f"x + {abs(r1_z)}" if r1_z < 0 else "x")
            r2_str_f = f"x − {r2_z}" if r2_z > 0 else (f"x + {abs(r2_z)}" if r2_z < 0 else "x")
            factored = f"f(x) = ({r1_str_f})({r2_str_f})"
            ans  = factored
            w1   = std_form
            w2   = vertex_form
            k3   = k - 1
            k3_str = f" + {k3}" if k3 > 0 else (f" − {abs(k3)}" if k3 < 0 else "")
            w3   = f"f(x) = ({h_str})²{k3_str}"
            dist = make_distractors(ans, [w1, w2, w3])
            exact = (f"{std_form}\n"
                     f"Which of the following equivalent forms of f most directly reveals "
                     f"the x-intercepts of the graph of y = f(x)?")
            ctx = (f"Factor: {std_form} → {factored}. "
                   f"x-intercepts at x={r1_z} and x={r2_z} are directly visible. "
                   f"CRITICAL — stem is locked (exactStem). "
                   f"DISTRACTOR ERRORS — "
                   f"'{w1}': standard form — zeros not directly visible. "
                   f"'{w2}': vertex form — shows minimum, not zeros. "
                   f"'{w3}': wrong constant in vertex form.")

        return _nlf(3, params, ph, ans, dist, "mcq", ctx, exact_stem=exact)

    raise RuntimeError("_d3_identify_equivalent_form: could not generate unique params")


def _d3_exponential_two_points(rng_obj, exclude_params, variant=None):
    """find_parameter_value — h(x)=aˣ+b through 2 points; find a. MCQ or SPR.
    find_product_of_params — h(x)=c·2ˣ+d through 2 points; find c+d. MCQ."""
    v = variant or rng_obj.choice(["find_parameter_value", "find_product_of_params"])

    for _ in range(200):
        if v == "find_parameter_value":
            # h(x) = a^x + b; through (0, p) and (2, q)
            # (0,p): 1 + b = p → b = p-1
            # (2,q): a² + b = q → a² = q - p + 1
            a = rng_obj.choice([2, 3, 4])
            b = rng_obj.randint(1, 6)
            p = 1 + b          # h(0) = a^0 + b = 1 + b
            q = a**2 + b       # h(2) = a^2 + b

            params = {"a": a, "b": b, "tpl": "exponential_two_points", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue

            ans  = str(a)
            d1   = str(a**2)       # returned a² instead of a
            d2   = str(b)          # returned b
            d3   = str(a + 1)      # off by 1
            dist = make_distractors(ans, [d1, d2, d3])
            exact = (f"The function h is defined by \\(h(x) = a^x + {b}\\), "
                     f"where a is a positive constant. "
                     f"The graph of h passes through the points (0, {p}) and (2, {q}). "
                     f"What is the value of a?")
            ctx = (f"h(0)=1+{b}={p} ✓; h(2)=a²+{b}={q} → a²={q-b} → a={a}. "
                   f"CRITICAL — stem is locked (exactStem). "
                   f"DISTRACTOR ERRORS — "
                   f"'{a**2}': returned a² = {a**2} instead of a. "
                   f"'{b}': returned the constant b. "
                   f"'{a+1}': off-by-one error solving a²={q-b}.")
            qt = rng_obj.choice(["mcq", "spr"])
            return _nlf(3, params, ph, ans, dist if qt == "mcq" else [], qt, ctx, exact_stem=exact)

        else:  # find_product_of_params
            # h(x) = c·2^x + d; through (0, p) and (1, q)
            # h(0) = c·1 + d = c + d = p
            # h(1) = c·2 + d = 2c + d = q
            # Subtract: c = q - p;  d = 2p - q
            # Ask for c·d (true product) — not directly readable from the given points.
            # Trap distractor: c+d = p is visible in stem → catches students who skip solving.
            c = rng_obj.randint(2, 6)
            d = rng_obj.randint(1, 5)
            if c == d:
                continue
            p = c + d          # h(0)
            q = 2*c + d        # h(1)
            product = c * d

            params = {"c": c, "d": d, "tpl": "exponential_two_points", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue

            ans  = str(product)
            d1   = str(p)          # read h(0)=c+d directly without isolating c,d
            d2   = str(c)          # found c only
            d3   = str(d)          # found d only
            dist = make_distractors(ans, [d1, d2, d3])
            exact = (f"The function h is defined by \\(h(x) = c \\cdot 2^x + d\\), "
                     f"where c and d are constants. "
                     f"The graph of h passes through the points (0, {p}) and (1, {q}). "
                     f"What is the value of \\(c \\cdot d\\)?")
            ctx = (f"h(0) = c + d = {p}; h(1) = 2c + d = {q}. "
                   f"Subtract: c = {q} - {p} = {c}; d = {p} - {c} = {d}. "
                   f"c \u00b7 d = {c} \u00d7 {d} = {product}. "
                   f"CRITICAL — stem is locked (exactStem). Do NOT rewrite it. "
                   f"DISTRACTOR ERRORS — "
                   f"'{p}': read c + d = {p} from the (0, {p}) point without isolating c and d. "
                   f"'{c}': found c = {c} only, forgot d. "
                   f"'{d}': found d = {d} only, forgot c.")
            return _nlf(3, params, ph, ans, dist, "mcq", ctx, exact_stem=exact)

    raise RuntimeError("_d3_exponential_two_points: could not generate unique params")


def _d3_quadratic_parameter_properties(rng_obj, exclude_params, variant=None):
    """determine_sign_of_param — axis + opening → deduce sign of b. MCQ.
    identify_true_statements — 3 statements about a,b,c; which must be true? MCQ."""
    v = variant or rng_obj.choice(["determine_sign_of_param", "identify_true_statements"])

    for _ in range(200):
        if v == "determine_sign_of_param":
            # f(x)=ax²+bx+c; axis=-b/(2a); opening direction → signs of a,b
            opens = rng_obj.choice(["up", "down"])
            a_sign = 1 if opens == "up" else -1
            axis_x = rng_obj.choice([1, 2, 3, -1, -2, -3])
            # axis = -b/(2a) = axis_x → b = -2a·axis_x
            b_sign = -a_sign * (1 if axis_x > 0 else -1)
            b_sign_str = "positive" if b_sign > 0 else "negative"
            axis_str = f"x = {axis_x}"

            params = {"opens": opens, "axis_x": axis_x,
                      "tpl": "quadratic_parameter_properties", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue

            ans  = f"b < 0" if b_sign < 0 else "b > 0"
            d1   = f"b > 0" if b_sign < 0 else "b < 0"
            d2   = "b = 0"
            d3   = "The sign of b cannot be determined"
            dist = make_distractors(ans, [d1, d2, d3])

            exact = (f"The function f is defined by f(x) = ax² + bx + c, "
                     f"where a, b, and c are nonzero constants. "
                     f"The graph of y = f(x) opens {opens}ward and has its axis of "
                     f"symmetry at {axis_str}. Which of the following must be true?")
            ctx = (f"Opens {opens}ward → a {'>' if a_sign>0 else '<'} 0. "
                   f"Axis = −b/(2a) = {axis_x} → b = −2a·{axis_x}. "
                   f"With a {'>' if a_sign>0 else '<'} 0 and axis_x = {axis_x}: "
                   f"b = −2·(a)·{axis_x} → b is {b_sign_str}. "
                   f"CRITICAL — stem is locked (exactStem). "
                   f"DISTRACTOR ERRORS — "
                   f"'{d1}': flipped the sign of b. "
                   f"'b = 0': b=0 would give axis x=0, contradicting {axis_str}. "
                   f"'cannot be determined': sign IS determined by opening + axis together.")
            return _nlf(3, params, ph, ans, dist, "mcq", ctx, exact_stem=exact)

        else:  # identify_true_statements
            # Setup: opens upward (a>0), axis at positive x (→ b<0), y-int positive (c>0)
            opens = rng_obj.choice(["up", "down"])
            a_pos = (opens == "up")
            axis_pos = rng_obj.choice([True, False])   # axis at positive x?
            c_pos = rng_obj.choice([True, False])       # y-intercept positive?

            # b sign: axis=-b/2a; a>0 + axis>0 → b<0; a>0 + axis<0 → b>0
            b_neg = (a_pos and axis_pos) or (not a_pos and not axis_pos)

            params = {"opens": opens, "axis_pos": axis_pos, "c_pos": c_pos,
                      "tpl": "quadratic_parameter_properties", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue

            a_true = f"a {'>' if a_pos else '<'} 0"
            b_true = f"b {'<' if b_neg else '>'} 0"
            c_true = f"c {'>' if c_pos else '<'} 0"

            # Build 3 statements, some true some false
            stmts = [a_true, b_true, c_true]
            true_indices = [i for i, s in enumerate(["a", "b", "c"])
                           if (s == "a" and a_pos) or
                              (s == "b" and b_neg) or
                              (s == "c" and c_pos)]

            if len(true_indices) == 0 or len(true_indices) == 3:
                continue  # avoid trivial all-true or all-false

            # Format statements as I, II, III
            stmt_labels = ["I", "II", "III"]
            true_labels = [stmt_labels[i] for i in true_indices]
            if len(true_labels) == 1:
                ans = true_labels[0]
                d1 = stmt_labels[(true_indices[0] + 1) % 3]
                d2 = stmt_labels[(true_indices[0] + 2) % 3]
                d3 = f"{stmt_labels[(true_indices[0]+1)%3]} and {stmt_labels[(true_indices[0]+2)%3]}"
            else:
                ans = " and ".join(true_labels)
                false_idx = [i for i in range(3) if i not in true_indices][0]
                d1 = stmt_labels[false_idx]
                d2 = true_labels[0]
                d3 = " and ".join(stmt_labels[i] for i in range(3))

            dist = make_distractors(ans, [d1, d2, d3])
            axis_desc = "a positive" if axis_pos else "a negative"
            yint_desc = "positive" if c_pos else "negative"
            exact = (f"The function f is defined by f(x) = ax² + bx + c, "
                     f"where a, b, and c are nonzero constants. "
                     f"The graph of y = f(x) opens {opens}ward, has its axis of symmetry "
                     f"at {axis_desc} x-value, and has a {yint_desc} y-intercept.\n"
                     f"I.   {stmts[0]}\n"
                     f"II.  {stmts[1]}\n"
                     f"III. {stmts[2]}\n"
                     f"Which of the following must be true?")
            ctx = (f"Opens {opens}ward → {a_true}. "
                   f"Axis at {axis_desc} x: axis=−b/2a {'< 0' if not axis_pos else '> 0'} → {b_true}. "
                   f"y-intercept = f(0) = c {'> 0' if c_pos else '< 0'} → {c_true}. "
                   f"True statements: {ans}. "
                   f"CRITICAL — stem is locked (exactStem).")
            return _nlf(3, params, ph, ans, dist, "mcq", ctx, exact_stem=exact)

    raise RuntimeError("_d3_quadratic_parameter_properties: could not generate unique params")


def _d3_exponential_reparameterize(rng_obj, exclude_params, variant=None):
    """convert_time_base  — monthly model → equivalent yearly form. MCQ.
    find_percent_change — compute annual % change from monthly base. MCQ."""
    v = variant or rng_obj.choice(["convert_time_base", "find_percent_change"])

    # Monthly growth bases with known nice yearly rates
    _BASES = [
        {"monthly": "1.02",  "desc": "2% monthly", "yearly_exp": "(1.02)^{12}"},
        {"monthly": "1.005", "desc": "0.5% monthly", "yearly_exp": "(1.005)^{12}"},
        {"monthly": "1.01",  "desc": "1% monthly", "yearly_exp": "(1.01)^{12}"},
        {"monthly": "1.03",  "desc": "3% monthly", "yearly_exp": "(1.03)^{12}"},
    ]
    _CONTEXTS = [
        ("bacteria", "sample", "months", "B"),
        ("account balance", "dollars", "months", "A"),
        ("population", "city", "months", "P"),
        ("investment", "dollars", "months", "V"),
    ]

    for _ in range(200):
        base_info = rng_obj.choice(_BASES)
        ctx_info  = rng_obj.choice(_CONTEXTS)
        a0        = rng_obj.randint(100, 999)
        monthly_b = base_info["monthly"]
        context, unit, time_unit, fn_name = ctx_info

        params = {"monthly_b": monthly_b, "a0": a0, "context": context,
                  "tpl": "exponential_reparameterize", "variant": v}
        ph = param_hash(params)
        if ph in exclude_params:
            continue

        if v == "convert_time_base":
            # f(t) = a0·(b)^t monthly → f(12y) = a0·((b)^12)^y yearly
            # All choices wrapped in \(...\) so KaTeX renders exponents properly.
            ans  = f"\\(f(y) = {a0} \\cdot (({monthly_b})^{{12}})^y\\)"
            w1   = f"\\(f(y) = {a0} \\cdot ({monthly_b})^y\\)"           # forgot ×12
            w2   = f"\\(f(y) = {a0} \\cdot ({monthly_b})^{{y/12}}\\)"    # divided instead
            w3   = f"\\(f(y) = {12*a0} \\cdot ({monthly_b})^y\\)"        # scaled coefficient
            dist = make_distractors(ans, [w1, w2, w3])
            exact = (f"The {context} after t months is modeled by "
                     f"\\(f(t) = {a0} \\cdot ({monthly_b})^t\\). "
                     f"Which of the following expressions models the {context} after y years?")
            qctx = (f"t months = 12y → substitute: f = {a0}·({monthly_b})^(12y) = "
                    f"{a0}·(({monthly_b})^12)^y. "
                    f"CRITICAL — stem is locked (exactStem). "
                    f"DISTRACTOR ERRORS — "
                    f"'forgot ×12': used y directly without scaling. "
                    f"'divided by 12': divided instead of multiplying. "
                    f"'scaled coefficient': multiplied coefficient {a0} by 12 instead of exponent.")
            return _nlf(3, params, ph, ans, dist, "mcq", qctx, exact_stem=exact)

        else:  # find_percent_change
            b_float = float(monthly_b)
            annual  = b_float ** 12
            pct     = round((annual - 1) * 100, 1)
            # Monthly % for distractor
            monthly_pct = round((b_float - 1) * 100, 1)
            ans  = f"{pct}%"
            d1   = f"{monthly_pct}%"          # used monthly rate directly
            d2   = f"{round(monthly_pct*12,1)}%"  # multiplied monthly by 12 (linear error)
            d3   = f"{round(pct/2,1)}%"            # halved
            dist = make_distractors(ans, [d1, d2, d3])
            exact = (f"The {context} after t months is modeled by "
                     f"\\(f(t) = {a0} \\cdot ({monthly_b})^t\\). "
                     f"Which of the following is closest to the annual percentage "
                     f"increase in the {context}?")
            qctx = (f"Annual factor = ({monthly_b})^12 ≈ {round(annual,4)}. "
                    f"Annual % = ({round(annual,4)}−1)×100 ≈ {pct}%. "
                    f"CRITICAL — stem is locked (exactStem). "
                    f"DISTRACTOR ERRORS — "
                    f"'{d1}': used the monthly rate {monthly_pct}% directly. "
                    f"'{d2}': multiplied monthly rate by 12 ({monthly_pct}%×12) — linear error. "
                    f"'{d3}': halved the correct answer.")
            return _nlf(3, params, ph, ans, dist, "mcq", qctx, exact_stem=exact)

    raise RuntimeError("_d3_exponential_reparameterize: could not generate unique params")


def _d3_count_zeros_graph(rng_obj, exclude_params, variant=None):
    """count_x_intercepts — f(x)=a·bˣ+c; how many x-intercepts? MCQ.
    count_intersections — f(x)=a·bˣ vs y=k; how many intersections? MCQ."""
    v = variant or rng_obj.choice(["count_x_intercepts", "count_intersections"])

    for _ in range(200):
        a = rng_obj.choice([2, 3, 4, 5])
        b = rng_obj.choice([2, 3, 4])
        # For exactly 1 x-intercept: a and c must have opposite signs
        c = rng_obj.choice([-4, -9, -16, -25, -36])   # negative so a·bˣ+c=0 has solution

        params = {"a": a, "b": b, "c": c, "tpl": "count_zeros_graph", "variant": v}
        ph = param_hash(params)
        if ph in exclude_params:
            continue

        if v == "count_x_intercepts":
            ans   = "1"
            d1    = "0"
            d2    = "2"
            d3    = "3"
            dist  = make_distractors(ans, [d1, d2, d3])
            c_str = f" - {abs(c)}" if c < 0 else f" + {c}"
            exact = (f"How many x-intercepts does the graph of "
                     f"\\(f(x) = {a} \\cdot {b}^x{c_str}\\) have?")
            ctx   = (f"f(x) = {a}·{b}^x{c_str}. "
                     f"Exponential {a}·{b}^x is always positive and strictly increasing; "
                     f"it crosses the horizontal line y={-c} exactly once → 1 x-intercept. "
                     f"CRITICAL — stem is locked (exactStem). Do NOT rewrite it. "
                     f"DISTRACTOR ERRORS — "
                     f"'0': student thinks exponential never crosses the x-axis. "
                     f"'2': confused with quadratic (which can have 2 zeros). "
                     f"'3': no basis; a strictly increasing exponential has at most 1 zero.")
            return _nlf(3, params, ph, ans, dist, "mcq", ctx, exact_stem=exact)

        else:  # count_intersections
            k = abs(c) * a   # horizontal line y=k; a·bˣ = k has exactly 1 solution
            ans  = "1"
            d1   = "0"
            d2   = "2"
            d3   = "Infinitely many"
            dist = make_distractors(ans, [d1, d2, d3])
            ctx  = (f"f(x) = {a}·{b}^x; horizontal line y = {k}. "
                    f"Solve {a}·{b}^x = {k} → {b}^x = {k//a} → exactly one solution. "
                    f"Strictly increasing exponential crosses any horizontal line at most once. "
                    f"CRITICAL — do NOT state the answer in the stem. "
                    f"DISTRACTOR ERRORS — "
                    f"'0': student thinks the line is above the exponential's range. "
                    f"'2': confused with quadratic intersections. "
                    f"'Infinitely many': only if the line were y=0 for f(x)=0, which it is not.")
            exact = (f"How many times does the graph of \\(f(x) = {a} \\cdot {b}^x\\) "
                     f"intersect the line \\(y = {k}\\)?")
            return _nlf(3, params, ph, ans, dist, "mcq", ctx, exact_stem=exact)

    raise RuntimeError("_d3_count_zeros_graph: could not generate unique params")


def _d3_minimum_completing_square(rng_obj, exclude_params, variant=None):
    """find_minimum_value — x²+bx+c; min = c−(b/2)². MCQ or SPR.
    find_x_at_minimum  — x at min = −b/2. SPR."""
    v = variant or rng_obj.choice(["find_minimum_value", "find_x_at_minimum"])

    for _ in range(200):
        # b must be even for integer vertex
        b = rng_obj.choice([-8, -6, -4, -2, 2, 4, 6, 8, 10])
        c = rng_obj.randint(-5, 20)
        x_min  = -b // 2              # x at minimum
        f_min  = c - (b // 2) ** 2   # minimum value

        if abs(f_min) > 50:
            continue

        params = {"b": b, "c": c, "tpl": "minimum_completing_square", "variant": v}
        ph = param_hash(params)
        if ph in exclude_params:
            continue

        b_str = f" + {b}x" if b > 0 else f" − {abs(b)}x"
        c_str = f" + {c}" if c > 0 else (f" − {abs(c)}" if c < 0 else "")
        fn_str = f"f(x) = x²{b_str}{c_str}"

        if v == "find_minimum_value":
            ans = str(f_min)
            d1  = str(c)              # returned c without completing square
            d2  = str(x_min)          # returned x-value not y-value
            d3  = str(f_min + (b//2)**2)  # forgot to subtract (b/2)²
            dist = make_distractors(ans, [d1, d2, d3])
            ctx = (f"{fn_str}. "
                   f"Complete the square: (x + {b//2})² + ({c} − {(b//2)**2}) = "
                   f"(x + {b//2})² + {f_min}. "
                   f"Minimum value = {f_min}. "
                   f"CRITICAL — do NOT state the minimum in the stem. "
                   f"DISTRACTOR ERRORS — "
                   f"'{c}': returned c = {c} without completing the square. "
                   f"'{x_min}': returned the x-value of the vertex, not f(x). "
                   f"'{f_min + (b//2)**2}': forgot to subtract (b/2)² = {(b//2)**2}.")
            qt = rng_obj.choice(["mcq", "spr"])
            return _nlf(3, params, ph, ans, dist if qt == "mcq" else [], qt, ctx)

        else:
            ans = str(x_min)
            d1  = str(-x_min)         # wrong sign
            d2  = str(b)              # used b directly
            d3  = str(x_min + 1)      # off by 1
            dist = make_distractors(ans, [d1, d2, d3])
            ctx = (f"{fn_str}. "
                   f"x at minimum = −b/2 = −({b})/2 = {x_min}. "
                   f"CRITICAL — do NOT state the x-value in the stem. "
                   f"DISTRACTOR ERRORS — "
                   f"'{-x_min}': sign error, used b/2 instead of −b/2. "
                   f"'{b}': used b = {b} directly without dividing by 2. "
                   f"'{x_min+1}': off-by-one arithmetic error.")
            return _nlf(3, params, ph, ans, [], "spr", ctx)

    raise RuntimeError("_d3_minimum_completing_square: could not generate unique params")


def _d3_projectile_symmetry(rng_obj, exclude_params, variant=None):
    """find_time_to_return — use parabola symmetry t₂=2·axis−t₁. MCQ.
    find_max_height      — h at axis of symmetry. MCQ."""
    v = variant or rng_obj.choice(["find_time_to_return", "find_max_height"])

    _CONTEXTS = [
        ("ball", "feet", "seconds"),
        ("rocket", "meters", "seconds"),
        ("projectile", "feet", "seconds"),
    ]

    for _ in range(200):
        # h(t) = -at² + vt  (launched from ground, c=0 for simplicity)
        a_coef = rng_obj.choice([4, 16])         # 4 or 16 (common SAT values)
        v_coef = rng_obj.choice([24, 32, 48, 64, 96])
        # axis = v/(2a); must be integer or half-integer
        if (v_coef % (2 * a_coef)) != 0:
            if (2 * v_coef % (2 * a_coef)) != 0:
                continue
        axis = v_coef / (2 * a_coef)
        h_max = int(-a_coef * axis**2 + v_coef * axis)
        if h_max > 500 or h_max <= 0:
            continue

        obj, unit, time_unit = rng_obj.choice(_CONTEXTS)

        if v == "find_time_to_return":
            # Pick t1 < axis; compute h(t1); student finds t2 = 2·axis - t1
            t1 = rng_obj.choice([int(x * 0.5) for x in range(1, int(axis * 2))])
            if t1 <= 0 or t1 >= axis:
                continue
            h_t1 = int(-a_coef * t1**2 + v_coef * t1)
            if h_t1 <= 0:
                continue
            t2 = 2 * axis - t1
            if t2 != int(t2):
                continue
            t2 = int(t2)

            params = {"a": a_coef, "v": v_coef, "t1": t1, "obj": obj,
                      "tpl": "projectile_symmetry", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue

            ans  = str(t2)
            d1   = str(int(2 * axis))   # full flight time (return to ground)
            d2   = str(t1 + 1)          # naive +1
            d3   = str(int(axis))       # confused axis with return time
            dist = make_distractors(ans, [d1, d2, d3])

            exact = (f"The height of a {obj} in {unit} is modeled by "
                     f"h(t) = −{a_coef}t² + {v_coef}t, where t is in {time_unit}. "
                     f"At t = {t1} {time_unit}, the {obj} is at a height of {h_t1} {unit} "
                     f"and rising. At what value of t does the {obj} return to "
                     f"a height of {h_t1} {unit}?")
            ctx = (f"h(t) = −{a_coef}t² + {v_coef}t. "
                   f"Axis of symmetry = {v_coef}/(2·{a_coef}) = {axis}. "
                   f"By symmetry: t₂ = 2·{axis} − {t1} = {t2}. "
                   f"CRITICAL — stem is locked (exactStem). "
                   f"DISTRACTOR ERRORS — "
                   f"'{d1}': returned the full flight time (when h=0). "
                   f"'{d2}': added 1 to t1 naively. "
                   f"'{int(axis)}': confused the axis of symmetry with the return time.")

            # Diagram: parabola with labeled point (t1, h_t1) + dashed reference line
            x_max = int(2 * axis) + 1
            y_max = int(h_max * 1.25) + 5
            diag = {
                "shape": "coordinate_plane",
                "subtype": "function_graph",
                "xMin": 0, "xMax": x_max,
                "yMin": 0, "yMax": y_max,
                "xAxis": {"label": "t"},
                "yAxis": {"label": "h"},
                "functions": [
                    {
                        "type": "quadratic",
                        "params": {"a": -a_coef, "b": v_coef, "c": 0},
                        "style": {"stroke": "#334155", "strokeWidth": 2}
                    },
                    {
                        "type": "constant",
                        "params": {"value": h_t1},
                        "style": {"stroke": "#94a3b8", "strokeWidth": 1,
                                  "strokeDasharray": "5,4"}
                    }
                ],
                "points": [
                    {"x": t1, "y": h_t1,
                     "label": f"({t1}, {h_t1})", "color": "#2563eb"}
                ]
            }
            return _nlf(3, params, ph, ans, dist, "mcq", ctx,
                        exact_stem=exact, diagram=diag)

        else:  # find_max_height
            params = {"a": a_coef, "v": v_coef, "obj": obj,
                      "tpl": "projectile_symmetry", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue

            ans  = str(h_max)
            d1   = str(v_coef)          # returned initial velocity as height
            d2   = str(int(axis))       # returned t at max, not h
            d3   = str(h_max + a_coef)  # arithmetic error
            dist = make_distractors(ans, [d1, d2, d3])

            exact = (f"A {obj} is launched upward. Its height in {unit} after t {time_unit} "
                     f"is h(t) = −{a_coef}t² + {v_coef}t. "
                     f"What is the maximum height the {obj} reaches, in {unit}?")
            ctx = (f"Axis = {v_coef}/(2·{a_coef}) = {axis}. "
                   f"h({axis}) = −{a_coef}·{axis}² + {v_coef}·{axis} = {h_max}. "
                   f"CRITICAL — stem is locked (exactStem). "
                   f"DISTRACTOR ERRORS — "
                   f"'{v_coef}': returned the coefficient {v_coef} (initial speed). "
                   f"'{int(axis)}': returned t at max, not h at max. "
                   f"'{h_max+a_coef}': arithmetic error evaluating h({axis}).")

            # Diagram: clean parabola — no vertex label (student must compute it)
            x_max = int(2 * axis) + 1
            y_max = int(h_max * 1.25) + 5
            diag = {
                "shape": "coordinate_plane",
                "subtype": "function_graph",
                "xMin": 0, "xMax": x_max,
                "yMin": 0, "yMax": y_max,
                "xAxis": {"label": "t"},
                "yAxis": {"label": "h"},
                "functions": [
                    {
                        "type": "quadratic",
                        "params": {"a": -a_coef, "b": v_coef, "c": 0},
                        "style": {"stroke": "#334155", "strokeWidth": 2}
                    }
                ]
            }
            return _nlf(3, params, ph, ans, dist, "mcq", ctx,
                        exact_stem=exact, diagram=diag)

    raise RuntimeError("_d3_projectile_symmetry: could not generate unique params")


def _d3_model_setup_quadratic(rng_obj, exclude_params, variant=None):
    """identify_equation — rectangle/fence word problem → which equation for area? MCQ.
    write_equation     — projectile; at what t does h=target (first positive t)? SPR."""
    v = variant or rng_obj.choice(["identify_equation", "write_equation"])

    for _ in range(200):
        if v == "identify_equation":
            # Rectangle with perimeter P; side=x; area = x·(P/2 − x)
            half_p = rng_obj.randint(10, 20)   # P/2
            P = 2 * half_p
            # Correct area: A(x) = x(half_p − x) = half_p·x − x²
            # Distractors: wrong perimeter formula, area of square, etc.
            ans  = f"A(x) = x({half_p} − x)"
            w1   = f"A(x) = x({P} − x)"        # used full P instead of P/2
            w2   = f"A(x) = x({half_p} + x)"   # addition error
            w3   = f"A(x) = x²"                 # square assumption
            dist = make_distractors(ans, [w1, w2, w3])

            params = {"half_p": half_p, "tpl": "model_setup_quadratic", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue

            exact = (f"A rectangular garden has a perimeter of {P} feet. "
                     f"If one side of the garden has length x feet, which of the following "
                     f"represents the area of the garden, in square feet?")
            ctx = (f"Perimeter = 2(x + other_side) = {P} → other_side = {half_p} − x. "
                   f"Area = x·({half_p} − x). "
                   f"CRITICAL — stem is locked (exactStem). "
                   f"DISTRACTOR ERRORS — "
                   f"'{w1}': used full perimeter {P} instead of half-perimeter {half_p}. "
                   f"'{w2}': added instead of subtracting for the other side. "
                   f"'{w3}': assumed square (both sides = x).")
            return _nlf(3, params, ph, ans, dist, "mcq", ctx, exact_stem=exact)

        else:  # write_equation (SPR)
            # h(t) = -16t² + v0·t + h0; find first positive t where h = target
            v0 = rng_obj.choice([32, 40, 48, 64])
            h0 = rng_obj.choice([6, 10, 16])
            # Pick target height that gives a clean rational solution
            # h(t) = target → 16t² - v0·t + (target - h0) = 0
            # For t=0.5 to be a solution: 16·0.25 - v0·0.5 + (target-h0) = 0
            # → target = h0 + v0·0.5 - 4 = h0 + v0/2 - 4
            t_sol = rng_obj.choice([
                sp.Rational(1, 2), sp.Rational(1, 4), sp.Rational(3, 2),
                sp.Rational(1, 1), sp.Rational(2, 1)
            ])
            target = int(-16 * t_sol**2 + v0 * t_sol + h0)
            if target <= 0 or target >= h0 + v0**2 / 64:
                continue

            # Verify: -16t²+v0t+h0=target → 16t²-v0t+(target-h0)=0
            t_sym = sp.Symbol('t')
            solutions = sp.solve(16*t_sym**2 - v0*t_sym + (target - h0), t_sym)
            pos_sols = sorted([s for s in solutions if s > 0])
            if not pos_sols:
                continue
            t_ans = min(pos_sols)   # first positive time
            if t_ans.denominator > 10:
                continue

            ans_str = str(t_ans) if t_ans.denominator == 1 else \
                      f"{t_ans.numerator}/{t_ans.denominator}"

            params = {"v0": v0, "h0": h0, "target": target,
                      "tpl": "model_setup_quadratic", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue

            exact = (f"A ball is thrown upward from a height of {h0} feet with an "
                     f"initial speed of {v0} feet per second. Its height in feet after "
                     f"t seconds is modeled by h(t) = −16t² + {v0}t + {h0}. "
                     f"After how many seconds does the ball first reach a height of "
                     f"{target} feet?")
            ctx = (f"Set h(t) = {target}: −16t² + {v0}t + {h0} = {target}. "
                   f"→ 16t² − {v0}t + {target-h0} = 0. "
                   f"First positive solution: t = {ans_str}. "
                   f"CRITICAL — stem is locked (exactStem). "
                   f"Student must set up and solve the quadratic; answer is t = {ans_str}.")

            # Diagram: parabola h(t) = -16t² + v0t + h0 with dashed line at target height
            import math as _math
            landing_t = (v0 + _math.sqrt(v0**2 + 64 * h0)) / 32
            h_max_val = h0 + v0**2 // 64
            x_max_d = int(landing_t) + 2
            y_max_d = int(h_max_val * 1.3) + 5
            diag = {
                "shape": "coordinate_plane",
                "subtype": "function_graph",
                "xMin": 0, "xMax": x_max_d,
                "yMin": 0, "yMax": y_max_d,
                "xAxis": {"label": "t"},
                "yAxis": {"label": "h"},
                "functions": [
                    {
                        "type": "quadratic",
                        "params": {"a": -16, "b": v0, "c": h0},
                        "style": {"stroke": "#334155", "strokeWidth": 2}
                    },
                    {
                        "type": "constant",
                        "params": {"value": target},
                        "style": {"stroke": "#2563eb", "strokeWidth": 1,
                                  "strokeDasharray": "5,4"}
                    }
                ],
                "points": [
                    {"x": 0, "y": h0, "label": f"(0, {h0})", "color": "#64748b"}
                ]
            }
            smin, smax = spr_bounds(ans_str)
            result = _nlf(3, params, ph, ans_str, [], "spr", ctx,
                          exact_stem=exact, diagram=diag)
            result["sprMin"] = smin
            result["sprMax"] = smax
            return result

    raise RuntimeError("_d3_model_setup_quadratic: could not generate unique params")


_D3 = {
    "max_in_context":               {"fn": _d3_max_in_context,               "variants": ["find_x_at_max", "find_max_value"]},
    "compound_function_max":        {"fn": _d3_compound_function_max,        "variants": ["find_max_of_compound", "find_shift_from_max"]},
    "vertex_from_zeros":            {"fn": _d3_vertex_from_zeros,            "variants": ["find_vertex_x", "find_vertex_y"]},
    "identify_equivalent_form":     {"fn": _d3_identify_equivalent_form,     "variants": ["reveal_maximum", "reveal_zeros"]},
    "exponential_two_points":       {"fn": _d3_exponential_two_points,       "variants": ["find_parameter_value", "find_product_of_params"]},
    "quadratic_parameter_properties": {"fn": _d3_quadratic_parameter_properties, "variants": ["determine_sign_of_param", "identify_true_statements"]},
    "exponential_reparameterize":   {"fn": _d3_exponential_reparameterize,   "variants": ["convert_time_base", "find_percent_change"]},
    "count_zeros_graph":            {"fn": _d3_count_zeros_graph,            "variants": ["count_x_intercepts", "count_intersections"]},
    "minimum_completing_square":    {"fn": _d3_minimum_completing_square,    "variants": ["find_minimum_value", "find_x_at_minimum"]},
    "projectile_symmetry":          {"fn": _d3_projectile_symmetry,          "variants": ["find_time_to_return", "find_max_height"]},
    "model_setup_quadratic":        {"fn": _d3_model_setup_quadratic,        "variants": ["identify_equation", "write_equation"]},
}


# ── Routing ───────────────────────────────────────────────────────────────────

_D1 = {
    "evaluate_polynomial":          {"fn": _d1_evaluate_polynomial,           "variants": ["find_output"]},
    "evaluate_exponential":         {"fn": _d1_evaluate_exponential,          "variants": ["find_output"]},
    "evaluate_other_nonlinear":     {"fn": _d1_evaluate_other_nonlinear,      "variants": ["find_radical_output", "find_rational_output", "find_absolute_value_output"]},
    "interpret_y_intercept_context":{"fn": _d1_interpret_y_intercept_context, "variants": ["interpret_initial_value"]},
    "y_intercept_from_graph":       {"fn": _d1_y_intercept_from_graph,        "variants": ["identify_ordered_pair"]},
    "vertex_from_graph":            {"fn": _d1_vertex_from_graph,             "variants": ["find_minimum", "find_maximum"]},
    "graph_translation":            {"fn": _d1_graph_translation,             "variants": ["identify_shifted_graph", "find_output_after_shift"]},
}

_ROUTING = {1: _D1, 2: _D2, 3: _D3}


# ── Public API ────────────────────────────────────────────────────────────────

def nlf_variants(difficulty: int, template: str = None) -> dict:
    """Return available variants for the given difficulty (+ optional template filter)."""
    tbl = _ROUTING.get(difficulty, _D1)
    if template:
        entry = tbl.get(template)
        if not entry or not entry["variants"]:
            return {"error": f"Unknown template '{template}' for NLF difficulty {difficulty}"}
        return {"variants": entry["variants"]}
    return {tpl: entry["variants"] for tpl, entry in tbl.items() if entry["variants"]}


def gen_nonlinear_fn(difficulty: int, rng_obj: random.Random, exclude_params: set,
                     force_template: str = None, force_variant: str = None,
                     exclude_templates: set = None, **_) -> dict:
    """Main dispatcher — routes to the correct difficulty table and template."""
    tbl = _ROUTING.get(difficulty, _D1)

    if force_template:
        entry = tbl.get(force_template)
        if not entry:
            raise ValueError(
                f"Unknown NLF template '{force_template}' for difficulty {difficulty}")
        return entry["fn"](rng_obj, exclude_params, variant=force_variant)

    # Shuffle candidates; exclude templates already used in this batch
    candidates = [
        (tpl, entry) for tpl, entry in tbl.items()
        if not exclude_templates or tpl not in exclude_templates
    ]
    if not candidates:
        candidates = list(tbl.items())

    random.shuffle(candidates)
    for tpl, entry in candidates:
        try:
            return entry["fn"](rng_obj, exclude_params)
        except (RuntimeError, NotImplementedError):
            continue

    raise RuntimeError(
        f"gen_nonlinear_fn: no templates available for difficulty {difficulty}")
