import math as _math
import random
from sympy import symbols, solve, sqrt, Rational, discriminant, simplify
from .core import param_hash, spr_bounds, make_distractors, validate_math_object

_x = symbols("x")
_y = symbols("y")


# ── Format helpers ────────────────────────────────────────────────────────────

def _fr(a, b):
    """Reduce fraction a/b, return (num, den)."""
    g = _math.gcd(abs(a), abs(b))
    return a // g, b // g


def _fr_str(a, b):
    """Fraction string p/q (reduced)."""
    p, q = _fr(a, b)
    if q == 1:
        return str(p)
    return f"{p}/{q}"


def _abc(a, b, c, var="x"):
    """Format ax^2 + bx + c cleanly."""
    parts = []
    if a == 1:
        parts.append(f"{var}^2")
    elif a == -1:
        parts.append(f"-{var}^2")
    elif a != 0:
        parts.append(f"{a}{var}^2")
    if b != 0:
        bv = abs(b)
        bt = var if bv == 1 else f"{bv}{var}"
        parts.append((f"+ {bt}" if b > 0 else f"- {bt}") if parts else (f"{b}{var}" if bv != 1 else (var if b > 0 else f"-{var}")))
    if c != 0:
        parts.append((f"+ {abs(c)}" if c > 0 else f"- {abs(c)}") if parts else str(c))
    return " ".join(parts) if parts else "0"


def _lat(s):
    return f"\\({s}\\)"


# ── Result helper ─────────────────────────────────────────────────────────────

def _nle_result(d, params, ph, ans, distractors, qt="mcq", ctx="", exact_stem=""):
    sm, sx = (None, None)
    if qt == "spr":
        try:
            sm, sx = spr_bounds(str(ans))
        except Exception:
            pass
    return {
        "skill": "nonlinear_equations",
        "difficulty": d,
        "questionType": qt,
        "params": params,
        "paramHash": ph,
        "verifiedAnswer": str(ans),
        "distractors": [str(d_) for d_ in distractors],
        "sprMin": sm,
        "sprMax": sx,
        "scenarioTag": None,
        "diagramSpec": None,
        "questionContext": ctx,
        "exactStem": exact_stem if exact_stem else None,
    }


# ── D1 template functions ─────────────────────────────────────────────────────

def _d1_perfect_square_solve(rng_obj, exclude_params, variant=None):
    """x^2 = k^2 → positive root. SPR or MCQ."""
    v = variant or rng_obj.choice(["spr_root", "mcq_with_coeff"])
    for _ in range(200):
        if v == "spr_root":
            k = rng_obj.randint(2, 12)
            params = {"k": k, "tpl": "perfect_square_solve", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(k)
            exact = f"If x² = {k*k}, what is the positive value of x?"
            ctx = (f"x² = {k*k} → x = ±{k}. Positive root: {k}. "
                   f"Answer: {k}. CRITICAL: stem is locked. "
                   f"DISTRACTOR ERRORS — "
                   f"SPR: common errors are writing {k*k} (original RHS) or {2*k} (doubling the root).")
            result = _nle_result(1, params, ph, ans, [], "spr", ctx, exact)
            if not validate_math_object(result):
                return result

        else:  # mcq_with_coeff: ax^2 = b → positive root
            a = rng_obj.randint(2, 5)
            k = rng_obj.randint(2, 10)
            rhs = a * k * k
            params = {"a": a, "k": k, "rhs": rhs, "tpl": "perfect_square_solve", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(k)
            d_no_div  = str(_math.isqrt(rhs)) if _math.isqrt(rhs) ** 2 == rhs else str(k * a)
            d_half    = str(rhs // 2)
            d_rhs_val = str(rhs)
            dist = make_distractors(ans, [d_no_div, d_half, d_rhs_val])
            exact = f"If {a}x² = {rhs}, what is the positive value of x?"
            ctx = (f"{a}x² = {rhs} → x² = {k*k} → x = {k}. "
                   f"Answer: {k}. CRITICAL: stem is locked. "
                   f"DISTRACTOR ERRORS — "
                   f"'{d_no_div}': took √{rhs} without dividing by {a} first. "
                   f"'{d_half}': divided {rhs} by 2 instead of {a}. "
                   f"'{d_rhs_val}': reported the RHS {rhs} directly instead of solving.")
            result = _nle_result(1, params, ph, ans, dist, "mcq", ctx, exact)
            if not validate_math_object(result):
                return result

    raise RuntimeError("perfect_square_solve d1: could not generate unique params")


def _d1_factored_form_solve(rng_obj, exclude_params, variant=None):
    """(x−r1)(x+r2)=0 or x(x−r1)(x+r2)=0."""
    v = variant or rng_obj.choice(["two_factors", "three_factors"])
    for _ in range(200):
        r1 = rng_obj.randint(2, 12)
        r2 = rng_obj.randint(1, 10)
        if r1 == r2:
            continue

        if v == "two_factors":
            # (x − r1)(x + r2) = 0; roots: r1, −r2; positive root = r1
            params = {"r1": r1, "r2": r2, "tpl": "factored_form_solve", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(r1)
            d_neg_r1 = str(-r1)          # sign-flipped the answer
            d_neg_r2 = str(-r2)          # picked the other (negative) root
            d_sum_neg = str(-(r1 + r2))  # summed zeros with wrong signs — keeps 3 negatives so "positive" qualifier doesn't narrow by sign
            if len({ans, d_neg_r1, d_neg_r2, d_sum_neg}) < 4:
                continue
            dist = make_distractors(ans, [d_neg_r1, d_neg_r2, d_sum_neg])
            exact = f"(x − {r1})(x + {r2}) = 0\nWhat is the positive solution to the equation above?"
            ctx = (f"Roots: x = {r1} and x = -{r2}. Positive root: {r1}. "
                   f"Answer: {r1}. CRITICAL: stem is locked. "
                   f"DISTRACTOR ERRORS — "
                   f"'{d_neg_r1}': sign-flipped the answer, wrote -{r1} instead of {r1}. "
                   f"'{d_neg_r2}': picked the negative root -{r2} instead of the positive one. "
                   f"'{d_sum_neg}': summed the two zero-values {r1} and {r2} with a wrong sign.")
            result = _nle_result(1, params, ph, ans, dist, "mcq", ctx, exact)
            if not validate_math_object(result):
                return result

        else:  # three_factors: x(x − r1)(x + r2) = 0; roots: 0, r1, −r2; greatest = r1
            params = {"r1": r1, "r2": r2, "tpl": "factored_form_solve", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(r1)
            d_zero   = "0"
            d_neg_r2 = str(-r2)
            d_sum    = str(r1 + r2)      # summed two zeros — BIGGER than ans, traps "pick the biggest" heuristic
            if len({ans, d_zero, d_neg_r2, d_sum}) < 4:
                continue
            dist = make_distractors(ans, [d_zero, d_neg_r2, d_sum])
            exact = f"x(x − {r1})(x + {r2}) = 0\nWhat is the greatest solution to the equation above?"
            ctx = (f"Roots: x=0, x={r1}, x=-{r2}. Greatest: {r1}. "
                   f"Answer: {r1}. CRITICAL: stem is locked. "
                   f"DISTRACTOR ERRORS — "
                   f"'0': picked the zero factor instead of the largest root. "
                   f"'{d_neg_r2}': picked the negative root -{r2}. "
                   f"'{d_sum}': picked the largest NUMBER in the choices ({r1+r2}) — "
                   f"but {r1+r2} is not a solution; the greatest actual root is {r1}.")
            result = _nle_result(1, params, ph, ans, dist, "mcq", ctx, exact)
            if not validate_math_object(result):
                return result

    raise RuntimeError("factored_form_solve d1: could not generate unique params")


def _d1_absolute_value_easy(rng_obj, exclude_params, variant=None):
    """|x − c| = d or |x + c| = d."""
    v = variant or rng_obj.choice(["find_positive", "sum_of_solutions"])
    for _ in range(200):
        c = rng_obj.randint(1, 8)
        d = rng_obj.randint(1, 8)
        if c == d:
            continue

        if v == "find_positive":
            # |x − c| = d → x = c+d (positive) or x = c−d
            # Need d > c so root_neg = c−d < 0 (exactly one positive root)
            root_pos = c + d
            root_neg = c - d
            if root_neg >= 0:
                continue
            params = {"c": c, "d": d, "tpl": "absolute_value_easy", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(root_pos)
            d1 = str(root_neg)
            d2 = str(c)      # forgot to add d
            d3 = str(d)      # gave d instead of c+d
            dist = make_distractors(ans, [d1, d2, d3])
            exact = f"If |x − {c}| = {d}, what is the positive value of x?"
            ctx = (f"|x-{c}|={d} → x-{c}={d} gives x={root_pos}, or x-{c}=-{d} gives x={root_neg}. "
                   f"Positive root: {root_pos}. Answer: {root_pos}. CRITICAL: stem is locked. "
                   f"DISTRACTOR ERRORS — "
                   f"'{d1}': used x={c}-{d}={root_neg} (the other solution). "
                   f"'{d2}': stopped at x-{c}=0, forgot to add {d}. "
                   f"'{d3}': reported d={d} instead of solving.")
            result = _nle_result(1, params, ph, ans, dist, "mcq", ctx, exact)
            if not validate_math_object(result):
                return result

        else:  # sum_of_solutions: |x + c| = d → sum = 2*(−c) = −2c
            root1 = -c + d
            root2 = -c - d
            total = root1 + root2  # = -2c
            params = {"c": c, "d": d, "tpl": "absolute_value_easy", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(total)
            d1 = str(2 * d)       # added d twice instead of summing roots
            d2 = str(d)           # gave only d
            d3 = str(-c)          # gave one root
            dist = make_distractors(ans, [d1, d2, d3])
            exact = f"If |x + {c}| = {d}, what is the sum of all solutions?"
            ctx = (f"|x+{c}|={d} → x={-c+d} or x={-c-d}. Sum = {root1}+{root2} = {total}. "
                   f"Answer: {total}. CRITICAL: stem is locked. "
                   f"DISTRACTOR ERRORS — "
                   f"'{d1}': computed 2*{d}={2*d} — doubled d instead of summing roots. "
                   f"'{d2}': reported d={d} without solving. "
                   f"'{d3}': gave one root {-c} instead of the sum.")
            result = _nle_result(1, params, ph, ans, dist, "mcq", ctx, exact)
            if not validate_math_object(result):
                return result

    raise RuntimeError("absolute_value_easy d1: could not generate unique params")


def _d1_system_from_graph(rng_obj, exclude_params, variant=None):
    """Parabola+line system read from graph description."""
    v = variant or rng_obj.choice(["read_coordinates", "count_intersections"])
    for _ in range(200):
        if v == "read_coordinates":
            # y = x² − ax, y = x → intersection at x(x-a-1)=0 → x=0 or x=a+1; non-zero = a+1
            a = rng_obj.randint(2, 7)
            x_non_zero = a + 1
            y_non_zero = x_non_zero  # since y=x
            params = {"a": a, "x_ans": x_non_zero, "y_ans": y_non_zero,
                      "tpl": "system_from_graph", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(x_non_zero)
            d1 = str(a)
            d2 = str(x_non_zero + 1)
            d3 = str(x_non_zero - 1)
            dist = make_distractors(ans, [d1, d2, d3])
            exact = (f"The graph of y = x² − {a}x and y = x intersect at the origin and one other point. "
                     f"What is the x-coordinate of the other intersection point?")
            ctx = (f"Set equal: x²-{a}x=x → x²-{a+1}x=0 → x(x-{a+1})=0 → x=0 or x={a+1}. "
                   f"Non-zero x-coordinate: {x_non_zero}. Answer: {x_non_zero}. CRITICAL: stem is locked. "
                   f"DISTRACTOR ERRORS — "
                   f"'{d1}': used x={a} (the coefficient) instead of solving the system. "
                   f"'{d2}': off-by-one, computed {a}+2={x_non_zero+1} instead of {a}+1. "
                   f"'{d3}': off-by-one error in the other direction.")
            result = _nle_result(1, params, ph, ans, dist, "mcq", ctx, exact)
            if not validate_math_object(result):
                return result

        else:  # count_intersections: y=x²+k vs y=n → how many intersections
            # choose k and n so x²+(k-n)=0 has 0, 1, or 2 solutions
            diff_options = [
                ("0", "no solution"),
                ("1", "exactly one solution"),
                ("2", "two solutions"),
            ]
            case_cnt, case_label = rng_obj.choice(diff_options)
            if case_cnt == "2":
                k = rng_obj.randint(-8, -2)
                n = rng_obj.randint(k + 2, -1)  # n > k means k−n < 0, two real roots
            elif case_cnt == "1":
                k = rng_obj.randint(-5, 5)
                n = k  # x²+(k-n)=0 → x²=0 → one root at x=0
            else:
                k = rng_obj.randint(-8, 8)
                n = k - rng_obj.randint(1, 5)  # k−n > 0 → no real roots
            params = {"k": k, "n": n, "cnt": case_cnt, "tpl": "system_from_graph", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            xdiff = n - k  # x² = n−k; positive → 2 roots, zero → 1, negative → 0
            ans = case_cnt
            d1 = str((int(case_cnt) + 1) % 3)
            d2 = str((int(case_cnt) + 2) % 3)
            d3 = "3"   # plausible over-count (student thinks parabola crosses more than twice)
            dist = make_distractors(ans, [d1, d2, d3])
            k_sign = "+" if k >= 0 else "-"
            abs_k = abs(k)
            exact = (f"y = x² {k_sign} {abs_k}\ny = {n}\n"
                     f"How many times do the graphs of the two equations above intersect?")
            ctx = (f"Set equal: x²{k_sign}{abs_k}={n} → x²={xdiff}. "
                   f"Sign of {xdiff}: positive means 2 real solutions, zero means 1, negative means 0. "
                   f"Intersections: {case_cnt}. Answer: {case_cnt}. CRITICAL: stem is locked. "
                   f"DISTRACTOR ERRORS — "
                   f"'{d1}' / '{d2}': misread the sign and reported a different count. "
                   f"'3': over-counted — a parabola and a horizontal line can have at most 2 intersections.")
            result = _nle_result(1, params, ph, ans, dist, "mcq", ctx, exact)
            if not validate_math_object(result):
                return result

    raise RuntimeError("system_from_graph d1: could not generate unique params")


def _d1_literal_equation(rng_obj, exclude_params, variant=None):
    """Literal equation rearrangement (d1 — linear in target variable)."""
    v = variant or rng_obj.choice(["two_var_linear", "three_var_linear"])
    for _ in range(200):
        if v == "two_var_linear":
            # ap − bq = c → p = (c + bq) / a
            a = rng_obj.randint(2, 6)
            b = rng_obj.randint(1, 5)
            c = rng_obj.randint(1, 8)
            params = {"a": a, "b": b, "c": c, "tpl": "literal_equation", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = f"(c + {b}q) / {a}" if b != 1 else f"(c + q) / {a}"
            d1 = f"(c - {b}q) / {a}"   # wrong sign: subtracted bq
            d2 = f"(c + {b}q) * {a}"   # multiplied by a instead of dividing
            d3 = f"c / {a} + {b}q"     # didn't divide bq by a
            dist = make_distractors(ans, [d1, d2, d3])
            exact = f"If {a}p − {b}q = c, which of the following gives p in terms of q and c?"
            ctx = (f"{a}p = c + {b}q → p = (c + {b}q)/{a}. "
                   f"Answer: (c + {b}q)/{a}. CRITICAL: stem is locked. "
                   f"DISTRACTOR ERRORS — "
                   f"'{d1}': subtracted {b}q instead of adding when moving term. "
                   f"'{d2}': multiplied by {a} instead of dividing. "
                   f"'{d3}': only divided c by {a}, forgot to also divide the {b}q term.")
            result = _nle_result(1, params, ph, ans, dist, "mcq", ctx, exact)
            if not validate_math_object(result):
                return result

        else:  # three_var_linear: ax + by − z = c → x = (c − by + z) / a
            a = rng_obj.randint(2, 5)
            b = rng_obj.randint(2, 6)
            params = {"a": a, "b": b, "tpl": "literal_equation", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = f"(c - {b}y + z) / {a}"
            d1 = f"(c + {b}y - z) / {a}"   # both signs flipped
            d2 = f"(c - {b}y + z) * {a}"   # multiplied by a
            d3 = f"(c - {b}y) / {a}"       # dropped z term
            dist = make_distractors(ans, [d1, d2, d3])
            exact = f"If {a}x + {b}y − z = c, which of the following gives x in terms of y, z, and c?"
            ctx = (f"{a}x = c - {b}y + z → x = (c - {b}y + z)/{a}. "
                   f"Answer: (c - {b}y + z)/{a}. CRITICAL: stem is locked. "
                   f"DISTRACTOR ERRORS — "
                   f"'{d1}': wrong signs — moved +{b}y as +{b}y and -z as -z instead of reversing both. "
                   f"'{d2}': multiplied by {a} instead of dividing. "
                   f"'{d3}': dropped the z term when rearranging.")
            result = _nle_result(1, params, ph, ans, dist, "mcq", ctx, exact)
            if not validate_math_object(result):
                return result

    raise RuntimeError("literal_equation d1: could not generate unique params")


# ── D2 template functions ─────────────────────────────────────────────────────

def _d2_solve_by_factoring(rng_obj, exclude_params, variant=None):
    """x^2 + bx + c = 0 — factor to find roots."""
    v = variant or rng_obj.choice(["find_root", "find_sum"])
    for _ in range(200):
        r1 = rng_obj.randint(1, 8)
        r2 = rng_obj.randint(1, 8)
        if r1 == r2:
            continue
        b = -(r1 + r2)   # sum of roots negated (both positive roots → b negative)
        c = r1 * r2      # product
        if c <= 0 or b >= 0:
            continue
        params = {"r1": r1, "r2": r2, "b": b, "c": c, "tpl": "solve_by_factoring", "variant": v}
        ph = param_hash(params)
        if ph in exclude_params:
            continue

        if v == "find_root":
            larger = max(r1, r2)
            ans = str(larger)
            d1 = str(min(r1, r2))        # smaller root
            d2 = str(-larger)            # negated root
            d3 = str(abs(b))             # sum, not individual root
            dist = make_distractors(ans, [d1, d2, d3])
            exact = (f"x² {b}x + {c} = 0\n"
                     f"What is the largest solution to the equation above?")
            ctx = (f"Factor: (x-{r1})(x-{r2})=0 → x={r1} or x={r2}. Largest: {larger}. "
                   f"Answer: {larger}. CRITICAL: stem is locked. "
                   f"DISTRACTOR ERRORS — "
                   f"'{d1}': chose the smaller root {min(r1,r2)} instead of the largest. "
                   f"'{d2}': negated the correct root: -{larger} is not a solution. "
                   f"'{d3}': reported the sum of roots |b|={abs(b)} instead of an individual root.")
            result = _nle_result(2, params, ph, ans, dist, "mcq", ctx, exact)
            if not validate_math_object(result):
                return result

        else:  # find_sum: SPR — sum of solutions = −b/a = b (b is negative here so sum = r1+r2)
            root_sum = r1 + r2
            ans = str(root_sum)
            exact = (f"x² {b}x + {c} = 0\n"
                     f"What is the sum of all solutions to the equation above?")
            ctx = (f"Roots: {r1} and {r2}. Sum = {root_sum} (= -b = {-b} = {root_sum}). "
                   f"Answer: {root_sum}. CRITICAL: stem is locked. "
                   f"DISTRACTOR ERRORS — "
                   f"SPR: common error is writing the negative {b} (the coefficient) instead of {root_sum}.")
            result = _nle_result(2, params, ph, ans, [], "spr", ctx, exact)
            if not validate_math_object(result):
                return result

    raise RuntimeError("solve_by_factoring d2: could not generate unique params")


def _d2_solve_from_context_area(rng_obj, exclude_params, variant=None):
    """Word problem leading to quadratic: area or projectile."""
    v = variant or rng_obj.choice(["rectangle_area", "projectile_context"])
    for _ in range(200):
        if v == "rectangle_area":
            # width w, length w+e, area A = w(w+e); w positive root
            e = rng_obj.randint(2, 8)
            w = rng_obj.randint(3, 12)
            A = w * (w + e)
            params = {"e": e, "w": w, "A": A, "tpl": "solve_from_context_area", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(w)
            d1 = str(w + e)           # gave length instead of width
            d2 = str(e)               # gave the "extra" {e} instead of width
            d3 = str(w + 1)           # off-by-one arithmetic slip
            dist = make_distractors(ans, [d1, d2, d3])
            exact = (f"The length of a rectangle is {e} more than its width. "
                     f"If the area of the rectangle is {A} square units, "
                     f"what is the width of the rectangle?")
            ctx = (f"Let width = w. Then w(w+{e}) = {A} → w²+{e}w-{A}=0 → w={w} (positive root). "
                   f"Width: {w}. Answer: {w}. CRITICAL: stem is locked. "
                   f"DISTRACTOR ERRORS — "
                   f"'{d1}': found the length {w+e} instead of width {w}. "
                   f"'{d2}': misread 'length is {e} more' as the width itself. "
                   f"'{d3}': arithmetic slip, off-by-one.")
            result = _nle_result(2, params, ph, ans, dist, "mcq", ctx, exact)
            if not validate_math_object(result):
                return result

        else:  # projectile_context: h(t) = −16t² + vel*t; find first t when h = H
            # Choose t1, t2 such that roots are positive integers
            t1 = rng_obj.randint(1, 4)
            t2 = rng_obj.randint(t1 + 1, t1 + 4)
            vel = 16 * (t1 + t2)
            H = 16 * t1 * t2
            if vel > 200 or H > 400:
                continue
            params = {"vel": vel, "H": H, "t1": t1, "t2": t2,
                      "tpl": "solve_from_context_area", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(t1)  # first (smaller) time
            d1 = str(t2)
            d2 = str(t1 + t2)
            d3 = str(t2 - t1)
            dist = make_distractors(ans, [d1, d2, d3])
            exact = (f"The height h, in feet, of a ball thrown upward is given by "
                     f"h = −16t² + {vel}t, where t is the time in seconds after the ball is thrown. "
                     f"At what time, in seconds, does the ball first reach a height of {H} feet?")
            ctx = (f"-16t²+{vel}t={H} → 16t²-{vel}t+{H}=0 → roots t={t1} and t={t2}. First: {t1}. "
                   f"Answer: {t1}. CRITICAL: stem is locked. "
                   f"DISTRACTOR ERRORS — "
                   f"'{d1}': gave the second time {t2} (when ball returns to height {H}). "
                   f"'{d2}': computed sum of roots {t1+t2} instead of individual time. "
                   f"'{d3}': took difference of roots instead of smaller root.")
            result = _nle_result(2, params, ph, ans, dist, "mcq", ctx, exact)
            if not validate_math_object(result):
                return result

    raise RuntimeError("solve_from_context_area d2: could not generate unique params")


def _d2_rational_equation_solve(rng_obj, exclude_params, variant=None):
    """Rational equation: k/(ax+b)=c or x+c/x=d."""
    v = variant or rng_obj.choice(["simple_rational", "rational_with_quadratic"])
    for _ in range(200):
        if v == "simple_rational":
            # k/(ax+b) = c → ax+b = k/c → x = (k/c - b) / a
            a = rng_obj.randint(1, 4)
            c_coeff = rng_obj.randint(2, 6)
            b = rng_obj.randint(1, 8)
            # pick k as multiple of c_coeff for clean answer
            mult = rng_obj.randint(2, 6)
            k = c_coeff * mult
            # ax + b = k/c = mult → x = (mult - b) / a
            if (mult - b) % a != 0:
                continue
            x_ans = (mult - b) // a
            if x_ans == 0:
                continue
            params = {"a": a, "b": b, "k": k, "c": c_coeff, "mult": mult,
                      "tpl": "rational_equation_solve", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(x_ans)
            d1 = str(mult)               # stopped after ax+b=mult, forgot /a
            d2 = str(-x_ans)             # sign error
            d3 = str(x_ans + 1)         # arithmetic slip
            dist = make_distractors(ans, [d1, d2, d3])
            lhs = f"{k}/({a}x + {b})" if a != 1 else f"{k}/(x + {b})"
            exact = f"If {lhs} = {c_coeff}, what is the value of x?"
            ctx = (f"{lhs}={c_coeff} → {a}x+{b}={k}/{c_coeff}={mult} → {a}x={mult-b} → x={x_ans}. "
                   f"Answer: {x_ans}. CRITICAL: stem is locked. "
                   f"DISTRACTOR ERRORS — "
                   f"'{d1}': found {a}x+{b}={mult} but stopped — gave {mult} as the answer. "
                   f"'{d2}': sign error somewhere, wrote -{x_ans}. "
                   f"'{d3}': arithmetic slip, off by one.")
            result = _nle_result(2, params, ph, ans, dist, "mcq", ctx, exact)
            if not validate_math_object(result):
                return result

        else:  # rational_with_quadratic: x + k/x = d → x²−dx+k=0
            r1 = rng_obj.randint(1, 8)
            r2 = rng_obj.randint(1, 8)
            if r1 == r2:
                continue
            d_val = r1 + r2
            k = r1 * r2
            larger = max(r1, r2)
            # Guard: the stem shows k and d_val as constants. If the answer (larger root)
            # equals either, the answer is visible in the stem.
            if larger == k or larger == d_val:
                continue
            params = {"r1": r1, "r2": r2, "d": d_val, "k": k,
                      "tpl": "rational_equation_solve", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(larger)
            d1 = str(min(r1, r2))
            d2 = str(d_val)
            d3 = str(k)
            dist = make_distractors(ans, [d1, d2, d3])
            exact = f"If x + {k}/x = {d_val}, what is the largest value of x?"
            ctx = (f"Multiply by x: x²+{k}={d_val}x → x²-{d_val}x+{k}=0 → (x-{r1})(x-{r2})=0. "
                   f"Largest root: {larger}. Answer: {larger}. CRITICAL: stem is locked. "
                   f"DISTRACTOR ERRORS — "
                   f"'{min(r1,r2)}': chose the smaller root {min(r1,r2)} instead of the larger. "
                   f"'{d_val}': reported d={d_val} (sum of roots) instead of the larger root. "
                   f"'{k}': reported k={k} (product of roots) instead of a root.")
            result = _nle_result(2, params, ph, ans, dist, "mcq", ctx, exact)
            if not validate_math_object(result):
                return result

    raise RuntimeError("rational_equation_solve d2: could not generate unique params")


def _d2_literal_equation_rational(rng_obj, exclude_params, variant=None):
    """Literal equation with rational form or square root."""
    v = variant or rng_obj.choice(["rational_form", "square_root_form"])
    for _ in range(200):
        if v == "rational_form":
            # PV = nRT → T = PV/(nR); use single letters for readability
            # Generic: solve for T given PV=nRT
            params = {"tpl": "literal_equation_rational", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = "PV / (nR)"
            d1 = "nR / (PV)"    # inverted
            d2 = "PV − nR"      # subtracted instead of divided
            d3 = "PV * nR"      # multiplied instead of divided
            dist = make_distractors(ans, [d1, d2, d3])
            exact = "The ideal gas law states that PV = nRT, where P, V, n, R, and T are constants. Which of the following gives T in terms of P, V, n, and R?"
            ctx = ("PV = nRT → T = PV/(nR). Answer: PV/(nR). CRITICAL: stem is locked. "
                   "DISTRACTOR ERRORS — "
                   "'nR/(PV)': inverted the fraction, giving T=nR/PV. "
                   "'PV − nR': subtracted nR from PV instead of dividing. "
                   "'PV * nR': multiplied instead of dividing.")
            result = _nle_result(2, params, ph, ans, dist, "mcq", ctx, exact)
            if not validate_math_object(result):
                return result

        else:  # square_root_form: v = √(2gh) → h = v²/(2g)
            params = {"tpl": "literal_equation_rational", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = "v² / (2g)"
            d1 = "v / (2g)"       # forgot to square v
            d2 = "2gv²"           # multiplied by 2g instead of dividing
            d3 = "v² − 2g"        # subtracted 2g
            dist = make_distractors(ans, [d1, d2, d3])
            exact = "If v = √(2gh), which of the following gives h in terms of v and g?"
            ctx = ("v=√(2gh) → v²=2gh → h=v²/(2g). Answer: v²/(2g). CRITICAL: stem is locked. "
                   "DISTRACTOR ERRORS — "
                   "'v/(2g)': forgot to square v after squaring both sides. "
                   "'2gv²': moved 2g to numerator instead of denominator. "
                   "'v²−2g': subtracted 2g instead of dividing.")
            result = _nle_result(2, params, ph, ans, dist, "mcq", ctx, exact)
            if not validate_math_object(result):
                return result

    raise RuntimeError("literal_equation_rational d2: could not generate unique params")


def _d2_absolute_value_medium(rng_obj, exclude_params, variant=None):
    """|ax + b| = c (find_sum) or |ax + b| = negative (no_solution, 0 real solutions)."""
    v = variant or rng_obj.choice(["find_sum", "no_solution"])

    if v == "find_sum":
        for _ in range(200):
            a = rng_obj.randint(2, 5)
            b = rng_obj.choice([-1, 1]) * rng_obj.randint(1, 8)
            c = rng_obj.randint(2, 10)
            # roots: x = (-b + c)/a and x = (-b - c)/a
            num1 = -b + c
            num2 = -b - c
            if num1 % a != 0 or num2 % a != 0:
                continue
            r1 = num1 // a
            r2 = num2 // a
            if r1 == r2 or r1 == 0 or r2 == 0:
                continue
            total = r1 + r2   # = -2b/a
            params = {"a": a, "b": b, "c": c, "r1": r1, "r2": r2,
                      "tpl": "absolute_value_medium", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(total)
            d1 = str(2 * c // a)       # used 2c/a instead of -2b/a
            d2 = str(-b)               # forgot /a
            d3 = str(max(r1, r2))      # gave one root instead of sum
            dist = make_distractors(ans, [d1, d2, d3])
            b_sign = "+" if b >= 0 else "-"
            abs_b = abs(b)
            exact = f"If |{a}x {b_sign} {abs_b}| = {c}, what is the sum of all solutions?"
            ctx = (f"|{a}x{b:+d}|={c} → {a}x{b:+d}=±{c}. "
                   f"x=({-b}+{c})/{a}={r1} and x=({-b}-{c})/{a}={r2}. Sum={total}. "
                   f"Answer: {total}. CRITICAL: stem is locked. "
                   f"DISTRACTOR ERRORS — "
                   f"'{d1}': used 2c/a={d1} — applied formula for |x|=c not |ax+b|=c. "
                   f"'{d2}': computed -b={-b} but forgot to divide by a={a}. "
                   f"'{max(r1,r2)}': gave one root instead of the sum.")
            result = _nle_result(2, params, ph, ans, dist, "mcq", ctx, exact)
            if not validate_math_object(result):
                return result
        raise RuntimeError("absolute_value_medium/find_sum d2: could not generate unique params")

    else:  # no_solution: |ax + b| = -(positive) has 0 real solutions
        # Cognitively distinct from d1: tests that |expression| ≥ 0 always — negative RHS is impossible
        for _ in range(200):
            a = rng_obj.randint(2, 6)
            b = rng_obj.choice([-1, 1]) * rng_obj.randint(1, 9)
            c_pos = rng_obj.randint(1, 10)
            params = {"a": a, "b": b, "c": -c_pos,
                      "tpl": "absolute_value_medium", "variant": "no_solution"}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = "0"
            d1 = "1"
            d2 = "2"
            d3 = "Infinitely many"
            dist = make_distractors(ans, [d1, d2, d3])
            b_sign = "+" if b >= 0 else "-"
            abs_b = abs(b)
            exact = (f"How many real solutions does the equation "
                     f"|{a}x {b_sign} {abs_b}| = {-c_pos} have?")
            ctx = (f"The absolute value |{a}x{b:+d}| ≥ 0 for all real x. "
                   f"It can never equal the negative number {-c_pos}. "
                   f"Therefore this equation has 0 real solutions. "
                   f"Answer: 0. CRITICAL: stem is locked — do not change the RHS {-c_pos}. "
                   f"DISTRACTOR ERRORS — "
                   f"'1': student ignores the sign of the RHS and solves one case as if valid. "
                   f"'2': student mechanically sets up ±({-c_pos}) and finds two 'solutions' without "
                   f"checking that {-c_pos} is negative. "
                   f"'Infinitely many': student confuses this with an identity like |x − x| = 0.")
            result = _nle_result(2, params, ph, ans, dist, "mcq", ctx, exact)
            if not validate_math_object(result):
                return result
        raise RuntimeError("absolute_value_medium/no_solution d2: could not generate unique params")


def _d2_count_solutions_discriminant(rng_obj, exclude_params, variant=None):
    """Use discriminant b²−4ac to count solutions or find k."""
    v = variant or rng_obj.choice(["count_roots", "find_k"])
    for _ in range(200):
        if v == "count_roots":
            # Generate a quadratic and ask how many real solutions
            a = rng_obj.randint(1, 4)
            b = rng_obj.randint(-6, 6)
            if b == 0:
                continue
            # Pick discriminant case
            case = rng_obj.choice(["two", "one", "zero"])
            if case == "two":
                # D > 0: b² > 4ac → pick c so that D > 0
                c = rng_obj.choice([-1, 1]) * rng_obj.randint(1, (b*b // (4*a)))
                if b*b - 4*a*c <= 0:
                    continue
                cnt = "2"
            elif case == "one":
                # D = 0: c = b²/(4a) — need integer c
                if (b * b) % (4 * a) != 0:
                    continue
                c = (b * b) // (4 * a)
                cnt = "1"
            else:
                # D < 0: b² < 4ac → pick c so that 4ac > b²
                c = rng_obj.randint(b*b // (4*a) + 1, b*b // (4*a) + 6)
                if b*b - 4*a*c >= 0:
                    continue
                cnt = "0"
            D = b*b - 4*a*c
            params = {"a": a, "b": b, "c": c, "D": D, "cnt": cnt,
                      "tpl": "count_solutions_discriminant", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = cnt
            all_cnts = ["0", "1", "2"]
            distr = [x for x in all_cnts if x != cnt]
            d1, d2 = distr[0], distr[1]
            d3 = "3"   # plausible over-count; replaces "infinite" which was trivially invalid
            dist = make_distractors(ans, [d1, d2, d3])
            c_sign = "+" if c >= 0 else "-"
            abs_c = abs(c)
            b_sign = "+" if b >= 0 else "-"
            abs_b = abs(b)
            exact = (f"How many real solutions does the equation "
                     f"{a}x² {b_sign} {abs_b}x {c_sign} {abs_c} = 0 have?")
            ctx = (f"Discriminant: {b}²-4*{a}*{c} = {D}. "
                   f"{'D>0: 2 solutions' if D > 0 else ('D=0: 1 solution' if D == 0 else 'D<0: 0 real solutions')}. "
                   f"Answer: {cnt}. CRITICAL: stem is locked. "
                   f"DISTRACTOR ERRORS — "
                   f"Wrong count: students misread the discriminant sign or forget to compute 4ac correctly.")
            result = _nle_result(2, params, ph, ans, dist, "mcq", ctx, exact)
            if not validate_math_object(result):
                return result

        else:  # find_k: x² + kx + c = 0 has exactly one solution → k² = 4c → k = 2√c
            # choose c = perfect square for integer answer
            sqrt_c = rng_obj.randint(2, 6)
            c = sqrt_c * sqrt_c
            k_pos = 2 * sqrt_c
            k_neg = -k_pos
            # ask for positive k
            params = {"c": c, "k": k_pos, "sqrt_c": sqrt_c,
                      "tpl": "count_solutions_discriminant", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(k_pos)
            d1 = str(k_neg)          # negative k (other valid answer but negative)
            d2 = str(sqrt_c)         # forgot to double
            d3 = str(4 * c)          # reported 4c instead of 2√c
            dist = make_distractors(ans, [d1, d2, d3])
            exact = (f"If the equation x² + kx + {c} = 0 has exactly one real solution, "
                     f"what is the positive value of k?")
            ctx = (f"D=0: k²-4*{c}=0 → k²={4*c} → k=±{k_pos}. Positive: {k_pos}. "
                   f"Answer: {k_pos}. CRITICAL: stem is locked. "
                   f"DISTRACTOR ERRORS — "
                   f"'{k_neg}': found negative k={k_neg} instead of positive. "
                   f"'{sqrt_c}': found √{c}={sqrt_c} but forgot to multiply by 2 (k=2√c). "
                   f"'{4*c}': computed 4c={4*c} instead of solving k²=4c for k.")
            result = _nle_result(2, params, ph, ans, dist, "mcq", ctx, exact)
            if not validate_math_object(result):
                return result

    raise RuntimeError("count_solutions_discriminant d2: could not generate unique params")


def _d2_system_linear_quadratic_solve(rng_obj, exclude_params, variant=None):
    """Substitute linear into quadratic, find intersection point."""
    v = variant or rng_obj.choice(["find_coordinates", "find_y"])
    for _ in range(200):
        # y = x² + px + q, y = mx + n; intersection at integer x values
        m = rng_obj.randint(-3, 3)
        n = rng_obj.randint(-5, 5)
        r1 = rng_obj.randint(-5, 5)
        r2 = rng_obj.randint(-5, 5)
        if r1 == r2 or m == 0:
            continue
        # Avoid x=0 as an intersection root: answer (0, n) is readable directly from stem
        if r1 == 0 or r2 == 0:
            continue
        # Substituting y=mx+n into y=x²+px+q:
        # x² + px + q = mx + n → x² + (p-m)x + (q-n) = 0
        # roots r1, r2 → (p-m) = -(r1+r2), (q-n) = r1*r2
        pm_coeff = -(r1 + r2)
        qn_const = r1 * r2
        p = pm_coeff + m
        q = qn_const + n
        # Avoid 0x term in stem (looks weird and can hint at x=0 root)
        if p == 0:
            continue
        # y values at intersections
        y1 = m * r1 + n
        y2 = m * r2 + n
        larger_x = max(r1, r2)
        smaller_x = min(r1, r2)
        y_at_larger = m * larger_x + n
        if abs(p) > 15 or abs(q) > 20:
            continue

        params = {"m": m, "n": n, "p": p, "q": q, "r1": r1, "r2": r2,
                  "tpl": "system_linear_quadratic_solve", "variant": v}
        ph = param_hash(params)
        if ph in exclude_params:
            continue

        if v == "find_coordinates":
            # Ask for intersection with the greater x-value (disambiguates which of the two points)
            ans = f"({larger_x}, {y_at_larger})"
            d1 = f"({larger_x}, {m * larger_x})"       # forgot n
            d2 = f"({larger_x}, {larger_x**2})"        # used x² not line
            d3 = f"({larger_x}, {larger_x + n})"       # dropped the coefficient m
            dist = make_distractors(ans, [d1, d2, d3])
            p_sign = "+" if p >= 0 else "-"
            abs_p = abs(p)
            q_sign = "+" if q >= 0 else "-"
            abs_q = abs(q)
            n_sign = "+" if n >= 0 else "-"
            abs_n = abs(n)
            exact = (f"y = x² {p_sign} {abs_p}x {q_sign} {abs_q}\n"
                     f"y = {m}x {n_sign} {abs_n}\n"
                     f"The two equations above intersect at two points. Which of the following is the "
                     f"intersection point with the greater x-coordinate?")
            ctx = (f"SOLUTION — write steps in this exact order, use these values verbatim: "
                   f"Step 1 — Substitute y={m}x{n:+d} into y=x²{p:+d}x{q:+d}: "
                   f"x²{p:+d}x{q:+d}={m}x{n:+d} → x²{pm_coeff:+d}x{qn_const:+d}=0. "
                   f"Step 2 — Factor: (x-{r1})(x-{r2})=0, so x={r1} or x={r2}. "
                   f"Step 3 — The greater x-value is {larger_x}; y={m}({larger_x}){n:+d}={y_at_larger}. "
                   f"Answer: ({larger_x},{y_at_larger}). "
                   f"CRITICAL: stem is locked — keep 'greater x-coordinate'. Do NOT re-derive. "
                   f"DISTRACTOR ERRORS — "
                   f"'{d1}': forgot the +{n} constant in y-computation. "
                   f"'{d2}': substituted x back into the quadratic instead of the line. "
                   f"'{d3}': dropped the coefficient m={m}, computed y = x + n.")
            result = _nle_result(2, params, ph, ans, dist, "mcq", ctx, exact)
            if not validate_math_object(result):
                return result

        else:  # find_y at the greater x
            ans = str(y_at_larger)
            other_y = m * smaller_x + n
            d1 = str(other_y)
            d2 = str(m * larger_x)        # forgot n in linear
            d3 = str(larger_x ** 2)       # used x² instead of y
            dist = make_distractors(ans, [d1, d2, d3])
            p_sign = "+" if p >= 0 else "-"
            abs_p = abs(p)
            q_sign = "+" if q >= 0 else "-"
            abs_q = abs(q)
            n_sign = "+" if n >= 0 else "-"
            abs_n = abs(n)
            exact = (f"y = x² {p_sign} {abs_p}x {q_sign} {abs_q}\n"
                     f"y = {m}x {n_sign} {abs_n}\n"
                     f"At the intersection point with the greater x-value, what is the value of y?")
            ctx = (f"SOLUTION — write steps in this exact order, use these values verbatim: "
                   f"Step 1 — Substitute y={m}x{n:+d} into y=x²{p:+d}x{q:+d}: "
                   f"x²{p:+d}x{q:+d}={m}x{n:+d} → x²{pm_coeff:+d}x{qn_const:+d}=0. "
                   f"Step 2 — Factor: (x-{r1})(x-{r2})=0, so x={r1} or x={r2}. "
                   f"Step 3 — The greater x-value is {larger_x}. "
                   f"Step 4 — Substitute into the linear equation: y={m}({larger_x}){n:+d}={y_at_larger}. "
                   f"Answer: y={y_at_larger}. CRITICAL: stem is locked — do not rewrite it. "
                   f"Do NOT re-derive, second-guess, or self-correct — write steps as given above. "
                   f"DISTRACTOR ERRORS — "
                   f"'{other_y}': used y at the smaller x={smaller_x} instead of the greater. "
                   f"'{m*larger_x}': forgot the y-intercept {n} in the linear equation. "
                   f"'{larger_x**2}': plugged x into x² instead of into y=mx+n.")
            result = _nle_result(2, params, ph, ans, dist, "mcq", ctx, exact)
            if not validate_math_object(result):
                return result

    raise RuntimeError("system_linear_quadratic_solve d2: could not generate unique params")


# ── D3 template functions ─────────────────────────────────────────────────────

def _d3_system_one_intersection(rng_obj, exclude_params, variant=None):
    """Linear-quadratic system with exactly one intersection (tangent). Find k or x."""
    v = variant or rng_obj.choice(["find_k_in_quadratic", "find_x"])
    for _ in range(200):
        if v == "find_k_in_quadratic":
            # y = x² + kx + c, y = mx + n; one intersection → D=0
            # Tangency gives (k-m)² = 4(c-n), so k = m ± 2·|x_t| — TWO solutions.
            # Ask for the POSITIVE value of k, and guard so only one root is positive.
            m = rng_obj.randint(-4, 4)
            n = rng_obj.randint(-6, 6)
            x_t_abs = rng_obj.randint(2, 4)   # |x_t| ∈ {2,3,4}
            k_pos = m + 2 * x_t_abs           # the positive tangency root
            k_neg_alt = m - 2 * x_t_abs       # the other tangency root
            # Uniqueness: want k_pos > 0 AND k_neg_alt ≤ 0 so "positive value of k" is unique.
            if k_pos <= 0 or k_neg_alt > 0:
                continue
            k = k_pos
            c = n + x_t_abs * x_t_abs         # so (x + x_t_abs)² = 0 at tangent
            params = {"m": m, "n": n, "k": k, "c": c, "x_t_abs": x_t_abs,
                      "tpl": "system_one_intersection", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(k)
            d1 = str(k_neg_alt)        # other tangency root — forgot "positive"
            d2 = str(m + x_t_abs)      # forgot factor of 2
            d3 = str(-k)               # sign flip
            dist = make_distractors(ans, [d1, d2, d3])
            c_sign = "+" if c >= 0 else "-"
            abs_c = abs(c)
            # Format the line y = mx + n cleanly: handle m∈{-1,0,1} and sign of n.
            if m == 0:
                line_expr = f"{n}"
            else:
                if m == 1:
                    mx = "x"
                elif m == -1:
                    mx = "-x"
                else:
                    mx = f"{m}x"
                if n == 0:
                    line_expr = mx
                else:
                    n_sign = "+" if n > 0 else "-"
                    line_expr = f"{mx} {n_sign} {abs(n)}"
            exact = (f"y = x² + kx {c_sign} {abs_c}\n"
                     f"y = {line_expr}\n"
                     f"In the system of equations above, the two equations intersect at exactly one point. "
                     f"What is the positive value of k?")
            ctx = (f"Substitute: x²+kx{c:+d}={m}x{n:+d} → x²+(k-{m})x+{c-n}=0. "
                   f"D=0: (k-{m})²=4·{c-n}={4*(c-n)} → k-{m}=±{2*x_t_abs} → k={k} or k={k_neg_alt}. "
                   f"Stem asks for the POSITIVE value → k={k}. "
                   f"Answer: {k}. CRITICAL: stem is locked — keep 'positive value of k'. "
                   f"DISTRACTOR ERRORS — "
                   f"'{d1}': picked the other tangency root, forgot the stem says 'positive'. "
                   f"'{d2}': forgot the factor of 2 in the discriminant condition. "
                   f"'{d3}': sign flip on the final answer.")
            result = _nle_result(3, params, ph, ans, dist, "mcq", ctx, exact)
            if not validate_math_object(result):
                return result

        else:  # find_x: y=x²+bx+c, y=n (horizontal); tangent → x = -b/2
            b = rng_obj.choice([-1, 1]) * rng_obj.randint(2, 10)
            if b % 2 != 0:
                continue
            x_t = -b // 2
            n = rng_obj.randint(1, 6)
            c = n + x_t * x_t  # so that quadratic vertex is at (x_t, n)
            params = {"b": b, "c": c, "n": n, "x_t": x_t,
                      "tpl": "system_one_intersection", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(x_t)
            d1 = str(-x_t)           # sign flip
            d2 = str(b)              # used b instead of -b/2
            d3 = str(x_t * 2)        # forgot to divide by 2
            dist = make_distractors(ans, [d1, d2, d3])
            b_sign = "+" if b >= 0 else "-"
            abs_b = abs(b)
            c_sign = "+" if c >= 0 else "-"
            abs_c = abs(c)
            exact = (f"y = x² {b_sign} {abs_b}x {c_sign} {abs_c}\n"
                     f"y = {n}\n"
                     f"If the system of equations above has exactly one solution, what is the value of x?")
            ctx = (f"x²{b:+d}x{c:+d}={n} → x²{b:+d}x{c-n:+d}=0. "
                   f"D=0: b²=4(c-n) check: {b}²={b*b}=4*{c-n}={4*(c-n)}. "
                   f"x=-b/2={-b//2}={x_t}. "
                   f"Answer: {x_t}. CRITICAL: stem is locked. "
                   f"DISTRACTOR ERRORS — "
                   f"'{d1}': sign error — used +b/2={-x_t} instead of -b/2={x_t}. "
                   f"'{d2}': gave the coefficient b={b} directly instead of x=-b/2. "
                   f"'{d3}': forgot the /2: computed -b={-b} instead of {x_t}.")
            result = _nle_result(3, params, ph, ans, dist, "mcq", ctx, exact)
            if not validate_math_object(result):
                return result

    raise RuntimeError("system_one_intersection d3: could not generate unique params")


def _d3_vieta_sum_of_roots(rng_obj, exclude_params, variant=None):
    """Vieta's formulas: r+s = -b/a, rs = c/a."""
    v = variant or rng_obj.choice(["sum_of_roots", "product_of_roots"])
    for _ in range(200):
        a = rng_obj.randint(1, 4)
        b = rng_obj.choice([-1, 1]) * rng_obj.randint(2, 12)
        c = rng_obj.choice([-1, 1]) * rng_obj.randint(1, 15)
        D = b * b - 4 * a * c
        if D < 0:
            continue  # need real roots for context

        if v == "sum_of_roots":
            # sum = -b/a
            p, q = _fr(-b, a)
            if q == 1:
                ans = str(p)
            else:
                ans = f"{p}/{q}"
            d1 = _fr_str(b, a)         # used +b/a instead of -b/a
            d2 = _fr_str(-b, a * 2)    # divided by 2a instead of a
            d3 = _fr_str(c, a)         # used product formula instead of sum
            dist = make_distractors(ans, [d1, d2, d3])
            b_sign = "+" if b >= 0 else "-"
            abs_b = abs(b)
            c_sign = "+" if c >= 0 else "-"
            abs_c = abs(c)
            exact = (f"In the equation {a}x² {b_sign} {abs_b}x {c_sign} {abs_c} = 0, "
                     f"r and s are the two solutions. What is the value of r + s?")
            ctx = (f"Vieta: r+s = -b/a = {-b}/{a} = {ans}. "
                   f"Answer: {ans}. CRITICAL: stem is locked. "
                   f"DISTRACTOR ERRORS — "
                   f"'{d1}': used b/a={_fr_str(b,a)} (wrong sign). "
                   f"'{d2}': divided by 2a={2*a} instead of a={a} (quadratic formula denominator). "
                   f"'{d3}': used product formula c/a={_fr_str(c,a)} instead of sum formula.")
            params = {"a": a, "b": b, "c": c, "tpl": "vieta_sum_of_roots", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            result = _nle_result(3, params, ph, ans, dist, "mcq", ctx, exact)
            if not validate_math_object(result):
                return result

        else:  # product_of_roots: rs = c/a
            p, q = _fr(c, a)
            if q == 1:
                ans = str(p)
            else:
                ans = f"{p}/{q}"
            d1 = _fr_str(-c, a)        # used -c/a (wrong sign)
            d2 = _fr_str(-b, a)        # used sum formula instead
            d3 = _fr_str(c, a * 2)     # divided by 2a
            # Guard: ensure distractors are distinct from ans and from each other.
            if len({ans, d1, d2, d3}) < 4:
                continue
            dist = make_distractors(ans, [d1, d2, d3])
            b_sign = "+" if b >= 0 else "-"
            abs_b = abs(b)
            c_sign = "+" if c >= 0 else "-"
            abs_c = abs(c)
            exact = (f"In the equation {a}x² {b_sign} {abs_b}x {c_sign} {abs_c} = 0, "
                     f"r and s are the two solutions. What is the value of r · s?")
            ctx = (f"Vieta: rs = c/a = {c}/{a} = {ans}. "
                   f"Answer: {ans}. CRITICAL: stem is locked. "
                   f"DISTRACTOR ERRORS — "
                   f"'{d1}': used -c/a (wrong sign, common for Vieta confusion). "
                   f"'{d2}': used sum formula -b/a instead of product c/a. "
                   f"'{d3}': divided by 2a={2*a} instead of a={a}.")
            params = {"a": a, "b": b, "c": c, "tpl": "vieta_sum_of_roots", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            result = _nle_result(3, params, ph, ans, dist, "mcq", ctx, exact)
            if not validate_math_object(result):
                return result

    raise RuntimeError("vieta_sum_of_roots d3: could not generate unique params")


def _d3_discriminant_no_solution(rng_obj, exclude_params, variant=None):
    """Find integer k so that ax² + bx + c = 0 has no real solutions (D < 0)."""
    v = variant or rng_obj.choice(["least_integer_k", "greatest_integer_b"])
    for _ in range(200):
        if v == "least_integer_k":
            # x² + bx + k = 0 has no real solution → b²−4k < 0 → k > b²/4
            b = rng_obj.choice([-1, 1]) * rng_obj.randint(2, 8)
            threshold = (b * b) / 4.0
            least_k = _math.floor(threshold) + 1
            params = {"b": b, "k": least_k, "tpl": "discriminant_no_solution", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(least_k)
            d1 = str(least_k - 1)      # exactly at boundary (D=0 means one solution, not zero)
            d2 = str(b * b // 4)       # computed b²/4 but didn't add 1
            d3 = str(least_k + 1)      # right direction but off by one
            dist = make_distractors(ans, [d1, d2, d3])
            b_sign = "+" if b >= 0 else "-"
            abs_b = abs(b)
            exact = (f"If the equation x² {b_sign} {abs_b}x + k = 0 has no real solutions, "
                     f"what is the least integer value of k?")
            ctx = (f"No real solutions: D<0 → {b}²-4k<0 → {b*b}-4k<0 → k>{b*b}/4={threshold:.2f}. "
                   f"Least integer k: {least_k}. "
                   f"Answer: {least_k}. CRITICAL: stem is locked. "
                   f"DISTRACTOR ERRORS — "
                   f"'{d1}': used D≤0 (one solution) instead of strict D<0 (no solutions). "
                   f"'{d2}': computed b²/4={b*b//4} as the threshold but didn't add 1. "
                   f"'{least_k+1}': off by one in the ceiling computation.")
            result = _nle_result(3, params, ph, ans, dist, "mcq", ctx, exact)
            if not validate_math_object(result):
                return result

        else:  # greatest_integer_b: x² + bx + c = 0 has no real solution → b² < 4c → b < 2√c
            # pick c = perfect square for clean bound
            sqrt_c = rng_obj.randint(2, 6)
            c = sqrt_c * sqrt_c
            # b < 2*sqrt_c and b > -2*sqrt_c; greatest positive b satisfying:
            # b² < 4c → |b| < 2√c → greatest integer b_max = 2*sqrt_c - 1
            b_max = 2 * sqrt_c - 1
            params = {"c": c, "sqrt_c": sqrt_c, "b_max": b_max,
                      "tpl": "discriminant_no_solution", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(b_max)
            d1 = str(2 * sqrt_c)       # included boundary (D=0)
            d2 = str(sqrt_c)           # forgot the 2 factor
            d3 = str(b_max - 1)        # off by one below
            dist = make_distractors(ans, [d1, d2, d3])
            exact = (f"If the equation x² + bx + {c} = 0 has no real solutions, "
                     f"what is the greatest integer value of b?")
            ctx = (f"No real solutions: b²-4*{c}<0 → b²<{4*c} → |b|<{2*sqrt_c}. "
                   f"Greatest integer b: {b_max} (since b={2*sqrt_c} would give D=0). "
                   f"Answer: {b_max}. CRITICAL: stem is locked. "
                   f"DISTRACTOR ERRORS — "
                   f"'{2*sqrt_c}': included D=0 boundary — that gives exactly one solution, not zero. "
                   f"'{sqrt_c}': forgot to multiply by 2 (used √c instead of 2√c). "
                   f"'{b_max-1}': off-by-one error, {b_max} still satisfies b²<{4*c}.")
            result = _nle_result(3, params, ph, ans, dist, "mcq", ctx, exact)
            if not validate_math_object(result):
                return result

    raise RuntimeError("discriminant_no_solution d3: could not generate unique params")


def _d3_tangent_condition(rng_obj, exclude_params, variant=None):
    """Line tangent to parabola: discriminant=0. Find c or slope m."""
    v = variant or rng_obj.choice(["find_c", "find_slope"])
    for _ in range(200):
        if v == "find_c":
            # y = x² + bx + c, y = mx + n; tangent → (b-m)² = 4(c-n)
            # Fix m and n; choose integer x_t for tangency → k = m-2x_t, c=n+x_t²
            m = rng_obj.randint(-3, 3)
            n = rng_obj.randint(-8, 8)
            x_t = rng_obj.choice([-3, -2, -1, 1, 2, 3])
            b = m - 2 * x_t
            c = n + x_t * x_t
            params = {"m": m, "n": n, "b": b, "c": c, "x_t": x_t,
                      "tpl": "tangent_condition", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(c)
            d1 = str(c + 1)
            d2 = str(c - 1)
            d3 = str(n + x_t)   # forgot to square x_t
            dist = make_distractors(ans, [d1, d2, d3])
            b_sign = "+" if b >= 0 else "-"
            abs_b = abs(b)
            n_sign = "+" if n >= 0 else "-"
            abs_n = abs(n)
            exact = (f"For what value of c does the line y = {m}x {n_sign} {abs_n} "
                     f"intersect the parabola y = x² {b_sign} {abs_b}x + c at exactly one point?")
            ctx = (f"Set equal: x²{b:+d}x+c={m}x{n:+d} → x²{b-m:+d}x+{c}-{n}=0. "
                   f"D=0: ({b-m})²-4({c}-{n})=0 → {(b-m)**2}=4({c-n}) → c={c}. "
                   f"Answer: {c}. CRITICAL: stem is locked. "
                   f"DISTRACTOR ERRORS — "
                   f"'{c+1}': off-by-one arithmetic error. "
                   f"'{c-1}': off-by-one arithmetic error in other direction. "
                   f"'{n+x_t}': computed n+x_t instead of n+x_t² (forgot to square).")
            result = _nle_result(3, params, ph, ans, dist, "mcq", ctx, exact)
            if not validate_math_object(result):
                return result

        else:  # find_slope: y = mx + n tangent to y = x² + bx + c → (b-m)² = 4(c-n)
            # Tangency gives TWO m solutions: m = b ± 2·|x_t|. Ask for the NEGATIVE value
            # and guard so only one root is negative.
            b = rng_obj.choice([-1, 1]) * rng_obj.randint(1, 6)
            n = rng_obj.randint(-10, 10)
            x_t_abs = rng_obj.randint(1, 3)          # |x_t| ∈ {1,2,3}
            m_neg = b - 2 * x_t_abs                  # the negative tangency root
            m_pos = b + 2 * x_t_abs                  # the other tangency root
            # Uniqueness: m_neg < 0 AND m_pos ≥ 0 so "negative value of m" is unique.
            if m_neg >= 0 or m_pos < 0:
                continue
            m = m_neg
            c = n + x_t_abs * x_t_abs                # tangency: c - n = x_t²
            params = {"b": b, "c": c, "n": n, "m": m, "x_t_abs": x_t_abs,
                      "tpl": "tangent_condition", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(m)
            d1 = str(m_pos)            # other tangency root (positive) — forgot stem says "negative"
            d2 = str(-m_pos)           # sign-flipped wrong root — negative, prevents answer-leak by "only negative"
            d3 = str(b)                # just gave coefficient b (mixed sign)
            dist = make_distractors(ans, [d1, d2, d3])
            b_sign = "+" if b >= 0 else "-"
            abs_b = abs(b)
            c_sign = "+" if c >= 0 else "-"
            abs_c = abs(c)
            n_sign = "+" if n >= 0 else "-"
            abs_n = abs(n)
            exact = (f"For what negative value of m does the line y = mx {n_sign} {abs_n} "
                     f"intersect the parabola y = x² {b_sign} {abs_b}x {c_sign} {abs_c} at exactly one point?")
            ctx = (f"Set equal: x²{b:+d}x{c:+d}=mx{n:+d} → x²+({b}-m)x+({c-n})=0. "
                   f"D=0: ({b}-m)²=4·{c-n}={4*(c-n)} → {b}-m=±{2*x_t_abs} → m={m_neg} or m={m_pos}. "
                   f"Stem asks for the NEGATIVE value → m={m}. "
                   f"Answer: {m}. CRITICAL: stem is locked — keep 'negative value of m'. "
                   f"DISTRACTOR ERRORS — "
                   f"'{d1}': picked the other tangency root (positive), forgot stem says 'negative'. "
                   f"'{d2}': sign-flipped the positive root, got {-m_pos} instead of the correct negative root. "
                   f"'{d3}': reported coefficient b={b} instead of solving for m.")
            result = _nle_result(3, params, ph, ans, dist, "mcq", ctx, exact)
            if not validate_math_object(result):
                return result

    raise RuntimeError("tangent_condition d3: could not generate unique params")


def _d3_radical_equation_solve(rng_obj, exclude_params, variant=None):
    """Radical equations — square both sides, reject extraneous roots."""
    v = variant or rng_obj.choice(["simple_radical", "square_both_sides"])
    for _ in range(200):
        if v == "simple_radical":
            # √(x + c) = x → x + c = x² → x² - x - c = 0; pick c so root is positive integer
            # x = (1 + √(1 + 4c)) / 2; need 1+4c = perfect square
            t = rng_obj.randint(2, 15)  # t = √(1+4c); valid odd t∈{5,7,9,11,13,15}
            if (t * t - 1) % 4 != 0:
                continue
            c = (t * t - 1) // 4
            if c <= 0:
                continue
            x_pos = (1 + t) // 2
            if (1 + t) % 2 != 0 or x_pos <= 0:
                continue
            # Check: x_pos satisfies √(x_pos + c) = x_pos?
            if _math.isqrt(x_pos + c) != x_pos:
                continue
            # Guard: stem constant must differ from the answer (otherwise answer leaks).
            if c == x_pos:
                continue
            x_neg = (1 - t) // 2   # extraneous
            params = {"c": c, "x_pos": x_pos, "x_neg": x_neg, "t": t,
                      "tpl": "radical_equation_solve", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(x_pos)
            d1 = str(x_neg)           # extraneous root
            d2 = str(c)               # constant in the radical
            d3 = str(x_pos + c)       # computed x+c instead of solving
            dist = make_distractors(ans, [d1, d2, d3])
            exact = f"If √(x + {c}) = x, what is the value of x?"
            ctx = (f"The equation is √(x+{c}) = x. "
                   f"Square both sides: (√(x+{c}))² = x² → x+{c}=x² → x²-x-{c}=0 → "
                   f"(x-{x_pos})(x+{-x_neg})=0 → x={x_pos} or x={x_neg}. "
                   f"Substitute x={x_pos} into the original: √({x_pos}+{c})=√{x_pos+c}={x_pos} ✓. "
                   f"Substitute x={x_neg} into the original: x={x_neg} is negative, "
                   f"but √(...) ≥ 0, so x={x_neg} is extraneous. "
                   f"Answer: {x_pos}. CRITICAL: stem is locked. "
                   f"DISTRACTOR ERRORS — "
                   f"'{x_neg}': extraneous root — a square root cannot equal a negative number. "
                   f"'{c}': reported constant c={c} from inside the radical. "
                   f"'{x_pos+c}': computed x+{c}={x_pos+c} instead of solving the quadratic.")
            result = _nle_result(3, params, ph, ans, dist, "mcq", ctx, exact)
            if not validate_math_object(result):
                return result

        else:  # square_both_sides: √(ax + b) = x − c
            # Square: ax + b = x² − 2cx + c² → x² − (2c+a)x + (c²−b) = 0
            # r1 > c_val (valid: r1 − c_val > 0), r2 < c_val (extraneous: r2 − c_val < 0)
            c_val = rng_obj.randint(2, 5)
            r1 = rng_obj.randint(c_val + 1, c_val + 7)
            r2 = rng_obj.randint(c_val - 4, c_val - 1)  # r2 < c_val → extraneous
            if r2 >= c_val:
                continue
            # sum: r1+r2 = 2c_val + a → a = r1+r2 - 2*c_val
            a = r1 + r2 - 2 * c_val
            if a <= 0:
                continue
            # product: r1*r2 = c_val² − b → b = c_val² − r1*r2
            b = c_val * c_val - r1 * r2
            # Verify valid root r1: √(a*r1 + b) = r1 − c_val
            lhs_sq = a * r1 + b
            rhs_val = r1 - c_val
            if lhs_sq < 0 or rhs_val <= 0:
                continue
            if _math.isqrt(lhs_sq) * _math.isqrt(lhs_sq) != lhs_sq:
                continue
            if _math.isqrt(lhs_sq) != rhs_val:
                continue
            # r2 is extraneous because r2 − c_val < 0 (RHS negative, can't equal √(...))

            params = {"a": a, "b": b, "c": c_val, "r1": r1, "r2": r2,
                      "tpl": "radical_equation_solve", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(r1)  # valid root
            d1 = str(r2)              # extraneous
            d2 = str(r1 + r2)         # sum of roots
            d3 = str(c_val)           # reported c instead of solving
            dist = make_distractors(ans, [d1, d2, d3])
            b_sign = "+" if b >= 0 else "-"
            abs_b = abs(b)
            ax_str = "x" if a == 1 else f"{a}x"
            exact = f"If √({ax_str} {b_sign} {abs_b}) = x − {c_val}, what is the value of x?"
            ctx = (f"The equation is √({ax_str}{b:+d}) = x-{c_val}. "
                   f"Square both sides: (√({ax_str}{b:+d}))² = (x-{c_val})² → "
                   f"{ax_str}{b:+d} = x²-{2*c_val}x+{c_val**2} → "
                   f"x²-{2*c_val+a}x+{c_val**2-b}=0 → x={r1} or x={r2}. "
                   f"Substitute x={r1} into the original: LHS=√({a*r1}{b:+d})=√{lhs_sq}={rhs_val}; RHS={r1}-{c_val}={rhs_val}. LHS=RHS ✓. "
                   f"Substitute x={r2} into the original: RHS={r2}-{c_val}={r2-c_val} is negative, but √(...) ≥ 0, so x={r2} is extraneous. "
                   f"Answer: {r1}. CRITICAL: stem is locked. "
                   f"DISTRACTOR ERRORS — "
                   f"'{r2}': extraneous root — RHS is negative, but √(...) cannot be negative. "
                   f"'{r1+r2}': reported sum of roots from quadratic formula. "
                   f"'{c_val}': reported the constant c={c_val} from inside the radical.")
            result = _nle_result(3, params, ph, ans, dist, "mcq", ctx, exact)
            if not validate_math_object(result):
                return result

    raise RuntimeError("radical_equation_solve d3: could not generate unique params")


def _d3_literal_rearrangement_hard(rng_obj, exclude_params, variant=None):
    """Hard literal: ap/q = b√(r+c) → solve for r."""
    v = variant or "solve_for_var"
    for _ in range(200):
        a = rng_obj.randint(2, 5)
        b = rng_obj.randint(2, 5)
        q = rng_obj.randint(2, 4)
        # ap/q = b√(r+c) → √(r+c) = ap/(bq) → r+c = (ap)²/(bq)² → r = (ap/(bq))² - c
        # Use symbolic letters; just check the algebraic expression form
        params = {"a": a, "b": b, "q": q, "tpl": "literal_rearrangement_hard", "variant": v}
        ph = param_hash(params)
        if ph in exclude_params:
            continue
        ans = f"(ap)² / ({b*q})² - c" if b * q != 1 else "(ap)² - c"
        bq_sq = (b * q) ** 2
        d1 = f"(ap)² / ({b}²q²) + c"   # added c instead of subtracting
        d2 = f"ap / ({b*q}) - c"         # forgot to square
        d3 = f"(ap)² / {b*q} - c"        # only squared the numerator
        dist = make_distractors(ans, [d1, d2, d3])
        exact = (f"If {a}p / {q} = {b}√(r + c), which of the following gives r in terms of a, p, b, q, and c? "
                 f"(Note: a, p, q, b, c are all positive.)")
        ctx = (f"{a}p/q = {b}√(r+c). "
               f"Isolate radical: √(r+c) = {a}p/(bq). "
               f"Square: r+c = ({a}p)²/(bq)². "
               f"r = ({a}p)²/(bq)² - c. "
               f"Answer: ({a}p)²/(bq)² - c. CRITICAL: stem is locked. "
               f"DISTRACTOR ERRORS — "
               f"'{d1}': added c instead of subtracting. "
               f"'{d2}': forgot to square after isolating the radical. "
               f"'{d3}': squared only the numerator but not denominator.")
        result = _nle_result(3, params, ph, ans, dist, "mcq", ctx, exact)
        if not validate_math_object(result):
            return result

    raise RuntimeError("literal_rearrangement_hard d3: could not generate unique params")


def _d3_count_distinct_zeros(rng_obj, exclude_params, variant=None):
    """Count distinct zeros from factored polynomial (with repeated factors)."""
    v = variant or rng_obj.choice(["factored_form", "identify_factor"])
    for _ in range(200):
        if v == "factored_form":
            # Rotate the "structure" to vary answer count ∈ {2, 3, 4}.
            # struct 2: (x-a)² * (x-b) — 2 distinct zeros
            # struct 3: (x-a)² * (x-b) * (x+c) — 3 distinct zeros
            # struct 4: (x-a) * (x-b) * (x+c) * (x+d) — 4 distinct zeros
            struct = rng_obj.choice([2, 3, 4])
            if struct == 2:
                a = rng_obj.randint(1, 5)
                b = rng_obj.randint(1, 5)
                if a == b:
                    continue
                zeros = {a, b}
                n_distinct = 2
                exact = (f"How many distinct zeros does the function "
                         f"f(x) = (x − {a})²(x − {b}) have?")
                zeros_note = f"x={a} (from (x-{a})², multiplicity 2) and x={b}"
                params_extra = {"a": a, "b": b, "struct": 2}
            elif struct == 3:
                a = rng_obj.randint(1, 5)
                b = rng_obj.randint(1, 5)
                cc = rng_obj.randint(1, 5)
                if len({a, b, -cc}) < 3:
                    continue
                zeros = {a, b, -cc}
                n_distinct = 3
                exact = (f"How many distinct zeros does the function "
                         f"f(x) = (x − {a})²(x − {b})(x + {cc}) have?")
                zeros_note = (f"x={a} (from (x-{a})², multiplicity 2), x={b}, and x=-{cc}")
                params_extra = {"a": a, "b": b, "c": cc, "struct": 3}
            else:  # struct == 4
                a = rng_obj.randint(1, 5)
                b = rng_obj.randint(1, 5)
                cc = rng_obj.randint(1, 5)
                dd = rng_obj.randint(1, 5)
                if len({a, b, -cc, -dd}) < 4:
                    continue
                zeros = {a, b, -cc, -dd}
                n_distinct = 4
                exact = (f"How many distinct zeros does the function "
                         f"f(x) = (x − {a})(x − {b})(x + {cc})(x + {dd}) have?")
                zeros_note = f"x={a}, x={b}, x=-{cc}, and x=-{dd}"
                params_extra = {"a": a, "b": b, "c": cc, "d": dd, "struct": 4}
            params = {**params_extra, "n": n_distinct,
                      "tpl": "count_distinct_zeros", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(n_distinct)
            # Distractors: the other plausible counts. Always pick 3 distinct from {1,2,3,4,5}\{ans}.
            all_cnts = ["1", "2", "3", "4", "5"]
            wrong = [c for c in all_cnts if c != ans][:3]
            d1, d2, d3 = wrong[0], wrong[1], wrong[2]
            dist = make_distractors(ans, [d1, d2, d3])
            ctx = (f"Zeros: {zeros_note}. Distinct zeros: {n_distinct}. "
                   f"Answer: {n_distinct}. CRITICAL: stem is locked. "
                   f"DISTRACTOR ERRORS — "
                   f"other counts reflect miscounting repeated factors or skipping a factor.")
            result = _nle_result(3, params, ph, ans, dist, "mcq", ctx, exact)
            if not validate_math_object(result):
                return result

        else:  # identify_factor: zeros given; find which expression is a factor
            # Both zeros positive and distinct; guard so that sign-flipped distractors
            # never coincidentally become valid factors of a zero the stem listed.
            r1 = rng_obj.randint(2, 7)
            r2 = rng_obj.randint(2, 7)
            if r1 == r2:
                continue
            params = {"r1": r1, "r2": r2, "tpl": "count_distinct_zeros", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = f"(x − {r1})"
            d1 = f"(x + {r1})"        # sign flip — (x+r1) has zero at −r1, not listed
            d2 = f"(x + {r2})"        # sign flip — (x+r2) has zero at −r2, not listed
            d3 = f"(x − {r1 + r2})"   # summed the two zeros
            dist = make_distractors(ans, [d1, d2, d3])
            exact = (f"A polynomial function p has zeros at x = {r1} and x = {r2}. "
                     f"Which of the following must be a factor of p(x)?")
            ctx = (f"Zero at x={r1} ↔ factor (x-{r1}). Answer: (x-{r1}). "
                   f"CRITICAL: stem is locked. The listed zeros are both POSITIVE ({r1}, {r2}); "
                   f"no sign-flipped or summed expression corresponds to a listed zero. "
                   f"DISTRACTOR ERRORS — "
                   f"'(x+{r1})': sign flip — has zero at -{r1}, which is NOT a listed zero. "
                   f"'(x+{r2})': sign flip on the other zero — has zero at -{r2}, not listed. "
                   f"'(x-{r1+r2})': summed the two zeros; has zero at {r1+r2}, not listed.")
            result = _nle_result(3, params, ph, ans, dist, "mcq", ctx, exact)
            if not validate_math_object(result):
                return result

    raise RuntimeError("count_distinct_zeros d3: could not generate unique params")


def _d3_discriminant_constant_find(rng_obj, exclude_params, variant=None):
    """Find constant c so D=0 (repeated root). ax² + bx + c = 0."""
    v = variant or "find_constant"
    for _ in range(200):
        a = rng_obj.randint(1, 4)
        b = rng_obj.choice([-1, 1]) * rng_obj.randint(2, 10)
        # D=0: c = b²/(4a); need integer result
        if (b * b) % (4 * a) != 0:
            continue
        c = b * b // (4 * a)
        params = {"a": a, "b": b, "c": c, "tpl": "discriminant_constant_find", "variant": v}
        ph = param_hash(params)
        if ph in exclude_params:
            continue
        ans = str(c)
        d1 = str(b * b)         # computed b² but forgot 4a
        d2 = str(c + 1)
        d3 = str(b * b // (2 * a))  # divided by 2a instead of 4a
        dist = make_distractors(ans, [d1, d2, d3])
        b_sign = "+" if b >= 0 else "-"
        abs_b = abs(b)
        a_str = "" if a == 1 else f"{a}"
        exact = (f"For what value of c does the equation {a_str}x² {b_sign} {abs_b}x + c = 0 "
                 f"have exactly one real solution?")
        ctx = (f"D=0: {b}²-4*{a}*c=0 → c={b*b}/(4*{a})={c}. "
               f"Answer: {c}. CRITICAL: stem is locked. "
               f"DISTRACTOR ERRORS — "
               f"'{b*b}': computed b²={b*b} but forgot to divide by 4a={4*a}. "
               f"'{c+1}': off by one. "
               f"'{b*b//(2*a)}': divided by 2a={2*a} instead of 4a={4*a} (quadratic formula denominator confusion).")
        result = _nle_result(3, params, ph, ans, dist, "mcq", ctx, exact)
        if not validate_math_object(result):
            return result

    raise RuntimeError("discriminant_constant_find d3: could not generate unique params")


def _d3_sum_of_roots_cubic(rng_obj, exclude_params, variant=None):
    """Cubic in factored form: find sum or product of roots."""
    v = variant or rng_obj.choice(["sum_of_roots", "product_of_roots"])
    for _ in range(200):
        r1 = rng_obj.randint(-5, 5)
        r2 = rng_obj.randint(-5, 5)
        r3 = rng_obj.randint(-5, 5)
        if len({r1, r2, r3}) < 3:
            continue
        # Exclude zero-roots: makes product distractor = 0 trivially identifiable,
        # and muddles Vieta's sign conventions for the sum variant.
        if 0 in (r1, r2, r3):
            continue

        if v == "sum_of_roots":
            root_sum = r1 + r2 + r3
            if root_sum == 0:
                continue   # sum=0 collides with −root_sum distractor
            params = {"r1": r1, "r2": r2, "r3": r3,
                      "tpl": "sum_of_roots_cubic", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(root_sum)
            d1 = str(-root_sum)         # sign error
            d2 = str(r1 * r2 * r3)      # product instead of sum
            d3 = str(root_sum - r3)     # forgot to include third root
            # Guard: ensure all 3 distractors are distinct from ans and each other.
            if len({ans, d1, d2, d3}) < 4:
                continue
            dist = make_distractors(ans, [d1, d2, d3])
            s1 = "+" if r1 <= 0 else "-"
            s2 = "+" if r2 <= 0 else "-"
            s3 = "+" if r3 <= 0 else "-"
            exact = (f"f(x) = (x {s1} {abs(r1)})(x {s2} {abs(r2)})(x {s3} {abs(r3)})\n"
                     f"What is the sum of the zeros of f?")
            ctx = (f"Zeros: {r1}, {r2}, {r3}. Sum = {r1}+{r2}+{r3} = {root_sum}. "
                   f"Answer: {root_sum}. CRITICAL: stem is locked. "
                   f"DISTRACTOR ERRORS — "
                   f"'{-root_sum}': sign error (Vieta: sum = −(−b)/a = −(−(r1+r2+r3)) = r1+r2+r3). "
                   f"'{r1*r2*r3}': computed product of roots instead of sum. "
                   f"'{root_sum-r3}': forgot to add the third root {r3}.")
            result = _nle_result(3, params, ph, ans, dist, "mcq", ctx, exact)
            if not validate_math_object(result):
                return result

        else:  # product_of_roots
            root_prod = r1 * r2 * r3
            # zero-root already excluded above, so product ≠ 0
            params = {"r1": r1, "r2": r2, "r3": r3,
                      "tpl": "sum_of_roots_cubic", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(root_prod)
            d1 = str(-root_prod)       # sign error
            d2 = str(r1 + r2 + r3)    # sum instead of product
            d3 = str(r1 * r2)          # forgot third factor (and r3 ≠ 1 guard below)
            if len({ans, d1, d2, d3}) < 4:
                continue
            dist = make_distractors(ans, [d1, d2, d3])
            s1 = "+" if r1 <= 0 else "-"
            s2 = "+" if r2 <= 0 else "-"
            s3 = "+" if r3 <= 0 else "-"
            exact = (f"f(x) = (x {s1} {abs(r1)})(x {s2} {abs(r2)})(x {s3} {abs(r3)})\n"
                     f"What is the product of the zeros of f?")
            ctx = (f"Zeros: {r1}, {r2}, {r3}. Product = {r1}*{r2}*{r3} = {root_prod}. "
                   f"Answer: {root_prod}. CRITICAL: stem is locked. "
                   f"DISTRACTOR ERRORS — "
                   f"'{-root_prod}': sign error on product. "
                   f"'{r1+r2+r3}': computed sum {r1+r2+r3} instead of product. "
                   f"'{r1*r2}': only multiplied two roots, forgot the third.")
            result = _nle_result(3, params, ph, ans, dist, "mcq", ctx, exact)
            if not validate_math_object(result):
                return result

    raise RuntimeError("sum_of_roots_cubic d3: could not generate unique params")


def _d3_greatest_intersection_x(rng_obj, exclude_params, variant=None):
    """System y=ax²+bx+c, y=mx+n → find greater x or y at greater x."""
    v = variant or rng_obj.choice(["greatest_x", "find_y"])
    for _ in range(200):
        # Integer intersections at x=r1 and x=r2, r2 > r1
        r1 = rng_obj.randint(-4, 2)
        r2 = rng_obj.randint(r1 + 2, r1 + 6)
        m = rng_obj.randint(-3, 3)
        if m == 0:
            continue
        n = rng_obj.randint(-8, 8)
        if n == 0:
            continue   # n=0 makes d2 = m*r2 equal to ans y_at_r2 in find_y variant
        # y = x² + (−(r1+r2) + m)x + (r1*r2 + n) after subtracting line
        p = -(r1 + r2) + m
        q = r1 * r2 + n
        y_at_r2 = m * r2 + n
        y_at_r1 = m * r1 + n

        if abs(p) > 15 or abs(q) > 25:
            continue
        # Guards for ambiguity / collisions across both variants.
        # greatest_x: stem uses "greatest" qualifier. Ensure r2 is strictly greater than
        # both other numeric distractors in value (r1+r2 can exceed r2 when r1>0, but
        # then "greatest x-value" cue becomes a trap — this is fine so long as r1+r2 is
        # NOT itself an intersection root; which it isn't since only r1 and r2 are).
        # But y_at_r2 can coincidentally equal r1, r2, or r1+r2 — that makes a distractor
        # visually equal a choice letter's worth of info. Reject those cases.
        if y_at_r2 in (r1, r2, r1 + r2):
            continue
        # find_y: ans = y_at_r2. Distractors {y_at_r1, m*r2, r2²}. Require distinctness.
        if len({y_at_r2, y_at_r1, m * r2, r2 * r2}) < 4:
            continue

        params = {"r1": r1, "r2": r2, "m": m, "n": n, "p": p, "q": q,
                  "tpl": "greatest_intersection_x", "variant": v}
        ph = param_hash(params)
        if ph in exclude_params:
            continue

        p_sign = "+" if p >= 0 else "-"
        abs_p = abs(p)
        q_sign = "+" if q >= 0 else "-"
        abs_q = abs(q)
        n_sign = "+" if n >= 0 else "-"
        abs_n = abs(n)

        if v == "greatest_x":
            ans = str(r2)
            d1 = str(r1)
            d2 = str(r1 + r2)    # sum of x coords
            d3 = str(y_at_r2)    # y-value at r2 instead of x-value
            dist = make_distractors(ans, [d1, d2, d3])
            exact = (f"y = x² {p_sign} {abs_p}x {q_sign} {abs_q}\n"
                     f"y = {m}x {n_sign} {abs_n}\n"
                     f"What is the greatest x-value at which the graphs of the two equations intersect?")
            ctx = (f"Full derivation (use verbatim; do not re-derive): "
                   f"Set the two expressions for y equal: x²{p:+d}x{q:+d} = {m}x{n:+d}. "
                   f"Move the line to the left: x²{p-m:+d}x{q-n:+d} = 0. "
                   f"Factor: (x-{r1})(x-{r2}) = 0 → x = {r1} or x = {r2}. "
                   f"The greater x-value is {r2}. "
                   f"Answer: {r2}. CRITICAL: stem is locked. "
                   f"DISTRACTOR ERRORS — "
                   f"'{r1}': chose the smaller x-value {r1}. "
                   f"'{r1+r2}': reported sum {r1+r2} instead of the larger root. "
                   f"'{y_at_r2}': reported the y-value at x={r2} instead of x itself.")
            result = _nle_result(3, params, ph, ans, dist, "mcq", ctx, exact)
            if not validate_math_object(result):
                return result

        else:  # find_y at greater x
            ans = str(y_at_r2)
            d1 = str(y_at_r1)
            d2 = str(m * r2)         # forgot n
            d3 = str(r2 ** 2)        # used x² instead of y=mx+n
            dist = make_distractors(ans, [d1, d2, d3])
            exact = (f"y = x² {p_sign} {abs_p}x {q_sign} {abs_q}\n"
                     f"y = {m}x {n_sign} {abs_n}\n"
                     f"At the intersection point with the greatest x-value, what is the value of y?")
            ctx = (f"Full derivation (use verbatim; do not re-derive): "
                   f"Set the two expressions for y equal: x²{p:+d}x{q:+d} = {m}x{n:+d}. "
                   f"Move the line to the left: x²{p-m:+d}x{q-n:+d} = 0. "
                   f"Factor: (x-{r1})(x-{r2}) = 0 → x = {r1} or x = {r2}. "
                   f"The greater x-value is {r2}. "
                   f"Substitute x={r2} into the line y={m}x{n:+d}: y = {m}·{r2}{n:+d} = {y_at_r2}. "
                   f"Answer: {y_at_r2}. CRITICAL: stem is locked. "
                   f"DISTRACTOR ERRORS — "
                   f"'{y_at_r1}': computed y at the smaller x={r1} instead of x={r2}. "
                   f"'{m*r2}': forgot the y-intercept {n} in y={m}x{n:+d}. "
                   f"'{r2**2}': plugged x={r2} into x² instead of into y={m}x{n:+d}.")
            result = _nle_result(3, params, ph, ans, dist, "mcq", ctx, exact)
            if not validate_math_object(result):
                return result

    raise RuntimeError("greatest_intersection_x d3: could not generate unique params")


# ── Routing dicts ─────────────────────────────────────────────────────────────

_D1 = {
    "perfect_square_solve":    {"fn": _d1_perfect_square_solve,    "variants": ["spr_root", "mcq_with_coeff"]},
    "factored_form_solve":     {"fn": _d1_factored_form_solve,     "variants": ["two_factors", "three_factors"]},
    "absolute_value_easy":     {"fn": _d1_absolute_value_easy,     "variants": ["find_positive", "sum_of_solutions"]},
    "system_from_graph":       {"fn": _d1_system_from_graph,       "variants": ["read_coordinates", "count_intersections"]},
    "literal_equation":        {"fn": _d1_literal_equation,        "variants": ["two_var_linear", "three_var_linear"]},
}

_D2 = {
    "solve_by_factoring":               {"fn": _d2_solve_by_factoring,               "variants": ["find_root", "find_sum"]},
    "solve_from_context_area":          {"fn": _d2_solve_from_context_area,          "variants": ["rectangle_area", "projectile_context"]},
    "rational_equation_solve":          {"fn": _d2_rational_equation_solve,          "variants": ["simple_rational", "rational_with_quadratic"]},
    "literal_equation_rational":        {"fn": _d2_literal_equation_rational,        "variants": ["rational_form", "square_root_form"]},
    "absolute_value_medium":            {"fn": _d2_absolute_value_medium,            "variants": ["find_sum", "no_solution"]},
    "count_solutions_discriminant":     {"fn": _d2_count_solutions_discriminant,     "variants": ["count_roots", "find_k"]},
    "system_linear_quadratic_solve":    {"fn": _d2_system_linear_quadratic_solve,    "variants": ["find_coordinates", "find_y"]},
}

_D3 = {
    "system_one_intersection":      {"fn": _d3_system_one_intersection,      "variants": ["find_k_in_quadratic", "find_x"]},
    "vieta_sum_of_roots":           {"fn": _d3_vieta_sum_of_roots,           "variants": ["sum_of_roots", "product_of_roots"]},
    "discriminant_no_solution":     {"fn": _d3_discriminant_no_solution,     "variants": ["least_integer_k", "greatest_integer_b"]},
    "tangent_condition":            {"fn": _d3_tangent_condition,            "variants": ["find_c", "find_slope"]},
    "radical_equation_solve":       {"fn": _d3_radical_equation_solve,       "variants": ["simple_radical", "square_both_sides"]},
    "literal_rearrangement_hard":   {"fn": _d3_literal_rearrangement_hard,   "variants": ["solve_for_var"]},
    "count_distinct_zeros":         {"fn": _d3_count_distinct_zeros,         "variants": ["factored_form", "identify_factor"]},
    "discriminant_constant_find":   {"fn": _d3_discriminant_constant_find,   "variants": ["find_constant"]},
    "sum_of_roots_cubic":           {"fn": _d3_sum_of_roots_cubic,           "variants": ["sum_of_roots", "product_of_roots"]},
    "greatest_intersection_x":      {"fn": _d3_greatest_intersection_x,      "variants": ["greatest_x", "find_y"]},
}

_ROUTING = {1: _D1, 2: _D2, 3: _D3}


# ── Public metadata API ───────────────────────────────────────────────────────

def nle_variants(difficulty: int, template: str = None) -> dict:
    """
    Return variant metadata for nonlinear_equations.

    If template is None: returns {template: [variants]} for all templates at the given difficulty.
    If template is given: returns {"variants": [...]} for that template.
    """
    routing = _ROUTING.get(difficulty, {})
    if template is None:
        return {tpl: entry["variants"] for tpl, entry in routing.items()}
    if template not in routing:
        raise ValueError(f"Unknown template '{template}' for nonlinear_equations d{difficulty}")
    return {"variants": routing[template]["variants"]}


# ── Main generator ────────────────────────────────────────────────────────────

def gen_nonlinear_equations(difficulty: int, rng_obj: random.Random,
                             exclude_params: set,
                             force_template: str = None,
                             force_variant: str = None,
                             **_kwargs) -> dict:
    """
    Nonlinear equations generator (NLE).

    All templates set exactStem — the problem statement is reproduced verbatim.
    Dispatches to per-template functions via _D1/_D2/_D3 routing dicts.
    """
    clamped = min(max(difficulty, 1), 3)
    routing = _ROUTING.get(clamped, _D3)

    if force_template is not None:
        if force_template not in routing:
            valid = sorted(routing.keys())
            raise ValueError(
                f"--template '{force_template}' is not valid for "
                f"nonlinear_equations d{clamped}. Valid: {valid}"
            )
        tpl = force_template
    else:
        tpl = rng_obj.choice(list(routing.keys()))

    entry = routing[tpl]
    fn    = entry["fn"]

    if force_variant is not None:
        if force_variant not in entry["variants"]:
            raise ValueError(
                f"--variant '{force_variant}' is not valid for template '{tpl}'. "
                f"Valid: {entry['variants']}"
            )
        return fn(rng_obj, exclude_params, variant=force_variant)

    return fn(rng_obj, exclude_params)
