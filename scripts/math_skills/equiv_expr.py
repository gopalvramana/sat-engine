import math as _math
import random
from sympy import symbols, expand, Rational
from .core import param_hash, spr_bounds, make_distractors, validate_math_object

_x = symbols("x")


# ── Format helpers ────────────────────────────────────────────────────────────

def _xp(n: int) -> str:
    """Format x^n — returns 'x' for n=1, 'x^n' otherwise."""
    return "x" if n == 1 else f"x^{n}"


def _lp(s: str) -> str:
    """Wrap a plain-text polynomial string in LaTeX delimiters for KaTeX rendering."""
    return f"\\({s}\\)"


def _ab(a, b, var="x"):
    """Format ax + b cleanly."""
    xp = var if a == 1 else (f"-{var}" if a == -1 else f"{a}{var}")
    if b == 0:
        return xp
    return f"{xp} + {b}" if b > 0 else f"{xp} - {abs(b)}"


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
        parts.append((f"+ {bt}" if b > 0 else f"- {bt}") if parts else (_ab(b, 0, var)))
    if c != 0:
        parts.append((f"+ {abs(c)}" if c > 0 else f"- {abs(c)}") if parts else str(c))
    return " ".join(parts) if parts else "0"


def _abcd(a, b, c, d, var="x"):
    """Format ax^3 + bx^2 + cx + d cleanly."""
    parts = []
    if a == 1:
        parts.append(f"{var}^3")
    elif a != 0:
        parts.append(f"{a}{var}^3")
    if b != 0:
        bt = f"{abs(b)}{var}^2" if abs(b) != 1 else f"{var}^2"
        parts.append((f"+ {bt}" if b > 0 else f"- {bt}") if parts else (_abc(b, 0, 0, var).split()[0]))
    if c != 0:
        ct = var if abs(c) == 1 else f"{abs(c)}{var}"
        parts.append((f"+ {ct}" if c > 0 else f"- {ct}") if parts else (_ab(c, 0, var)))
    if d != 0:
        parts.append((f"+ {abs(d)}" if d > 0 else f"- {abs(d)}") if parts else str(d))
    return " ".join(parts) if parts else "0"


def _binomial(p, q):
    """Format (px + q) as a string without the outer parens."""
    xp = "x" if p == 1 else ("-x" if p == -1 else f"{p}x")
    if q == 0:
        return xp
    return f"{xp} + {q}" if q > 0 else f"{xp} - {abs(q)}"


def _factors(p, q, r, s):
    """Format (px+q)(rx+s)."""
    return f"({_binomial(p, q)})({_binomial(r, s)})"


def _lat_rat_exp(m, n):
    """LaTeX \\(x^{m/n}\\)."""
    return f"\\(x^{{\\frac{{{m}}}{{{n}}}}}\\)"


def _lat_radical(m, n):
    """LaTeX for nth root of x^m."""
    if n == 2:
        return f"\\(\\sqrt{{x^{{{m}}}}}\\)"
    return f"\\(\\sqrt[{n}]{{x^{{{m}}}}}\\)"


def _lat_xpow(p):
    """LaTeX \\(x^p\\)."""
    return f"\\(x^{{{p}}}\\)"


def _lat_expr(s):
    """Wrap a plain LaTeX expression in \\( \\)."""
    return f"\\({s}\\)"


# ── Result helper ─────────────────────────────────────────────────────────────

def _exp_result(d, params, ph, ans, distractors, qt="mcq", ctx="", exact_stem=""):
    sm, sx = (None, None)
    if qt == "spr":
        try:
            sm, sx = spr_bounds(str(ans))
        except Exception:
            pass
    return {
        "skill": "equivalent_expressions",
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
        "questionContext": ctx or f"Equivalent expressions. Correct: {ans}. CRITICAL: stem is locked.",
        "exactStem": exact_stem if exact_stem else None,
    }


# ── D1 template functions ─────────────────────────────────────────────────────

def _d1_combine_like_terms(rng_obj, exclude_params, variant=None):
    v = variant or rng_obj.choice(["distribute_first", "pure_collect"])
    for _ in range(200):
        if v == "distribute_first":
            outer = rng_obj.randint(2, 5)
            b = rng_obj.randint(2, 5)
            c = rng_obj.choice([-1, 1]) * rng_obj.randint(1, 6)
            d = rng_obj.randint(2, 6)
            e = rng_obj.choice([-1, 1]) * rng_obj.randint(1, 8)
            cx = outer * b + d
            cc = outer * c + e
            if cx <= 0:
                continue
            params = {"outer": outer, "b": b, "c": c, "d": d, "e": e,
                      "tpl": "combine_like_terms", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = _ab(cx, cc)
            c_sign = "+" if c >= 0 else "-"
            inner = f"{b}x {c_sign} {abs(c)}"
            e_sign = "+" if e >= 0 else "-"
            expr_str = f"{outer}({inner}) + {d}x {e_sign} {abs(e)}"
            # 3 common errors
            d_sign_c = _ab(cx, -outer * c + e)   # sign error distributing c
            d_no_dx  = _ab(outer * b, cc)         # forgot to combine d*x
            d_sub_dx = _ab(outer * b - d, cc)     # subtracted d instead of adding
            dist = make_distractors(ans, [d_sign_c, d_no_dx, d_sub_dx])
            ctx = (f"Distribute {outer}: {outer}*{b}x = {outer*b}x, {outer}*{c:+d} = {outer*c:+d}. "
                   f"Combine x-terms: {outer*b}x + {d}x = {cx}x. "
                   f"Combine constants: {outer*c} + {e} = {cc}. "
                   f"Answer: {ans}. CRITICAL: stem is locked. "
                   f"DISTRACTOR ERRORS — "
                   f"'{d_sign_c}': sign error distributing {outer}*({c:+d}): treated as {outer}*({-c:+d}) = {-outer*c}, giving constant {-outer*c+e} instead of {cc}. "
                   f"'{d_no_dx}': forgot to combine the +{d}x term, kept only {outer*b}x from the distribution. "
                   f"'{d_sub_dx}': subtracted {d}x instead of adding: {outer*b}x - {d}x = {outer*b-d}x.")
            exact = f"Which of the following is equivalent to {expr_str}?"
            result = _exp_result(1, params, ph, ans, dist, "mcq", ctx, exact)
            if not validate_math_object(result):
                return result

        else:  # pure_collect: ax^2 + bx - sub_c*x^2 + dx + e
            a     = rng_obj.randint(4, 9)
            sub_c = rng_obj.randint(1, a - 1)
            b     = rng_obj.randint(1, 7)
            d     = rng_obj.choice([-1, 1]) * rng_obj.randint(1, 6)
            e     = rng_obj.choice([-1, 1]) * rng_obj.randint(1, 8)
            coeff2 = a - sub_c
            coeff1 = b + d
            if coeff2 <= 0 or abs(b) == abs(d) or coeff1 == 0:
                continue
            params = {"a": a, "sub_c": sub_c, "b": b, "d": d, "e": e,
                      "tpl": "combine_like_terms", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            d_sign = "+" if d >= 0 else "-"
            e_sign = "+" if e >= 0 else "-"
            expr_str = (f"{a}x^2 + {b}x - {sub_c}x^2 {d_sign} {abs(d)}x {e_sign} {abs(e)}")
            ans = _lp(_abc(coeff2, coeff1, e))
            d_add_c  = _lp(_abc(a + sub_c, coeff1, e))
            d_sub_d  = _lp(_abc(coeff2, b - d, e))
            d_neg_e  = _lp(_abc(coeff2, coeff1, -e))
            dist = make_distractors(ans, [d_add_c, d_sub_d, d_neg_e])
            ctx = (f"Combine x^2: {a} - {sub_c} = {coeff2}. "
                   f"Combine x: {b} {d_sign} {abs(d)} = {coeff1}. "
                   f"Constant: {e}. Answer: {_abc(coeff2, coeff1, e)}. CRITICAL: stem is locked. "
                   f"DISTRACTOR ERRORS — "
                   f"'{d_add_c}': added x^2 coefficients instead of subtracting: {a}+{sub_c}={a+sub_c} instead of {coeff2}. "
                   f"'{d_sub_d}': applied wrong sign to x-coefficient: computed {b-d} instead of {coeff1}. "
                   f"'{d_neg_e}': negated the constant term {e} → {-e}.")
            exact = f"Which of the following is equivalent to \\({expr_str}\\)?"
            result = _exp_result(1, params, ph, ans, dist, "mcq", ctx, exact)
            if not validate_math_object(result):
                return result

    raise RuntimeError("combine_like_terms d1: could not generate unique params")


def _d1_factor_gcf(rng_obj, exclude_params, variant=None):
    v = variant or rng_obj.choice(["monomial_gcf", "binomial_gcf"])
    for _ in range(200):
        if v == "monomial_gcf":
            gcf_coeff = rng_obj.randint(2, 6)
            gcf_pow   = rng_obj.randint(1, 3)   # power of x in GCF
            a1        = rng_obj.randint(2, 6)    # first term inner coeff
            a2        = rng_obj.randint(1, 5)    # second term inner coeff
            extra_pow = rng_obj.randint(1, 3)    # extra power in first term
            if a1 == a2:
                continue
            # Expression: gcf_coeff*x^(gcf_pow+extra_pow)*a1 + gcf_coeff*x^gcf_pow*a2
            # = gcf_coeff * x^gcf_pow * (a1*x^extra_pow + a2)
            p1 = gcf_pow + extra_pow
            p2 = gcf_pow
            t1 = gcf_coeff * a1
            t2 = gcf_coeff * a2
            params = {"gcf_coeff": gcf_coeff, "gcf_pow": gcf_pow,
                      "a1": a1, "a2": a2, "extra_pow": extra_pow,
                      "tpl": "factor_gcf", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            expr_str = f"{t1}{_xp(p1)} + {t2}{_xp(p2)}"
            ans_inner = f"{a1}{_xp(extra_pow)} + {a2}" if a2 > 0 else f"{a1}{_xp(extra_pow)} - {abs(a2)}"
            gcf_str = f"{gcf_coeff}{_xp(gcf_pow)}"
            ans = _lp(f"{gcf_str}({ans_inner})")
            d_wrong_a1  = _lp(f"{gcf_str}({a1 + 1}{_xp(extra_pow)} + {a2})")
            d_wrong_a2  = _lp(f"{gcf_str}({a1}{_xp(extra_pow)} + {a2 + 1})")
            d_sign_a2   = _lp(f"{gcf_str}({a1}{_xp(extra_pow)} - {a2})")
            dist = make_distractors(ans, [d_wrong_a1, d_wrong_a2, d_sign_a2])
            ctx = (f"GCF of {t1}{_xp(p1)} and {t2}{_xp(p2)}: coefficient GCF = {gcf_coeff}, "
                   f"variable GCF = {_xp(gcf_pow)}. Factor: {gcf_str}({ans_inner}). "
                   f"CRITICAL: stem is locked. "
                   f"DISTRACTOR ERRORS — "
                   f"'{d_wrong_a1}': first inner coefficient computed as {a1+1} instead of {a1} (arithmetic error dividing {t1} by {gcf_coeff}). "
                   f"'{d_wrong_a2}': second inner coefficient computed as {a2+1} instead of {a2} (arithmetic error dividing {t2} by {gcf_coeff}). "
                   f"'{d_sign_a2}': sign error on second inner coefficient: wrote -{a2} instead of +{a2}.")
            exact = f"Which of the following is equivalent to \\({expr_str}\\)?"
            result = _exp_result(1, params, ph, ans, dist, "mcq", ctx, exact)
            if not validate_math_object(result):
                return result

        else:  # binomial_gcf: p*x*(ax+b) + q*(ax+b) = (p*x+q)(ax+b)
            a = rng_obj.randint(2, 5)
            b = rng_obj.choice([-1, 1]) * rng_obj.randint(1, 6)
            p = rng_obj.randint(2, 6)
            q = rng_obj.choice([-1, 1]) * rng_obj.randint(2, 7)
            params = {"a": a, "b": b, "p": p, "q": q,
                      "tpl": "factor_gcf", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            b_sign = "+" if b >= 0 else "-"
            q_sign = "+" if q >= 0 else "-"
            binomial_str = f"{a}x {b_sign} {abs(b)}"
            expr_str = f"{p}x({binomial_str}) {q_sign} {abs(q)}({binomial_str})"
            ans = f"({_binomial(p, q)})({binomial_str})"
            d_sign_q     = f"({_binomial(p, -q)})({binomial_str})"      # sign error on q
            d_sign_b     = f"({_binomial(p, q)})({_binomial(a, -b)})"   # sign error on b
            d_sign_expand = _abc(p * a, -p * b + q * a, -q * b)         # expanded with b sign flipped
            dist = make_distractors(ans, [d_sign_q, d_sign_b, d_sign_expand])
            ctx = (f"Common factor is ({binomial_str}). Factor: ({_binomial(p, q)})({binomial_str}). "
                   f"CRITICAL: stem is locked. "
                   f"DISTRACTOR ERRORS — "
                   f"'{d_sign_q}': sign error on outer factor — wrote q as {-q} instead of {q}. "
                   f"'{d_sign_b}': sign error on the common binomial factor — wrote ({_binomial(a, -b)}) instead of ({binomial_str}). "
                   f"'{d_sign_expand}': expanded the product but with a sign error on b, giving an incorrect quadratic instead of the factored form.")
            exact = f"Which of the following is equivalent to {expr_str}?"
            result = _exp_result(1, params, ph, ans, dist, "mcq", ctx, exact)
            if not validate_math_object(result):
                return result

    raise RuntimeError("factor_gcf d1: could not generate unique params")


def _d1_rational_exponent_radical(rng_obj, exclude_params, variant=None):
    v = variant or rng_obj.choice(["radical_to_exp", "exp_to_radical"])
    for _ in range(200):
        # Pick root index n and inner power m (keep small for clarity)
        n = rng_obj.choice([2, 3, 4, 5])
        m = rng_obj.randint(2, 6)
        if m == n:  # trivial: nth root of x^n = x
            continue
        # Ensure fraction m/n is not reducible to integer
        from math import gcd as _gcd
        if _gcd(m, n) == n:  # m/n would be integer
            continue
        params = {"m": m, "n": n, "tpl": "rational_exponent_radical", "variant": v}
        ph = param_hash(params)
        if ph in exclude_params:
            continue

        if v == "radical_to_exp":
            # Stem: nth root of x^m; Answer: x^(m/n)
            exact = f"Which of the following is equivalent to {_lat_radical(m, n)}?"
            ans   = _lat_rat_exp(m, n)
            d_flip  = _lat_rat_exp(n, m)             # flipped fraction
            d_coeff = _lat_expr(f"{m}x^{{\\frac{{1}}{{{n}}}}}")  # moved m as coefficient
            d_mult  = _lat_xpow(m * n)               # multiplied indices
        else:  # exp_to_radical
            # Stem: x^(m/n); Answer: nth root of x^m
            exact = f"Which of the following is equivalent to {_lat_rat_exp(m, n)}?"
            ans   = _lat_radical(m, n)
            # Flip: x^(n/m) = mth root of x^n
            d_flip   = _lat_radical(n, m)
            # Wrong root index (use 2 if n != 2, else 3)
            wrong_n = 2 if n != 2 else 3
            d_wrongn = _lat_radical(m, wrong_n)
            d_frac   = _lat_expr(f"\\frac{{x^{{{m}}}}}{{{n}}}")  # misread as algebraic frac

        if v == "radical_to_exp":
            dist = make_distractors(ans, [d_flip, d_coeff, d_mult])
            ctx = (f"Recall: the nth root of x^m = x^(m/n). "
                   f"Here m={m}, n={n}. Answer: {ans}. CRITICAL: stem is locked. "
                   f"DISTRACTOR ERRORS — "
                   f"'{d_flip}': flipped the fraction — used exponent {n}/{m} instead of {m}/{n}. "
                   f"'{d_coeff}': moved inner exponent {m} to be a coefficient instead of keeping it in the exponent position. "
                   f"'{d_mult}': multiplied indices {m}*{n}={m*n} instead of dividing to form rational exponent {m}/{n}.")
        else:
            dist = make_distractors(ans, [d_flip, d_wrongn, d_frac])
            ctx = (f"Recall: x^(m/n) = the nth root of x^m. "
                   f"Here m={m}, n={n}. Answer: {ans}. CRITICAL: stem is locked. "
                   f"DISTRACTOR ERRORS — "
                   f"'{d_flip}': swapped root index and power — used {m}th root of x^{n} instead of {n}th root of x^{m}. "
                   f"'{d_wrongn}': used wrong root index {wrong_n} instead of {n}. "
                   f"'{d_frac}': misread rational exponent as algebraic fraction x^{m}/{n}.")
        result = _exp_result(1, params, ph, ans, dist, "mcq", ctx, exact)
        if not validate_math_object(result):
            return result

    raise RuntimeError("rational_exponent_radical d1: could not generate unique params")


def _d1_factor_trinomial(rng_obj, exclude_params, variant=None):
    v = variant or rng_obj.choice(["monic", "non_monic"])
    for _ in range(200):
        if v == "monic":
            # x^2 + bx + c = (x+r)(x+s); r*s=c, r+s=b
            r = rng_obj.choice([-1, 1]) * rng_obj.randint(1, 7)
            s = rng_obj.choice([-1, 1]) * rng_obj.randint(1, 7)
            if r == s or r == 0 or s == 0:
                continue
            b = r + s
            c = r * s
            if abs(b) < 2 or abs(c) < 2:
                continue
            params = {"r": r, "s": s, "tpl": "factor_trinomial", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            # verify
            assert expand((_x + r) * (_x + s)) == _x**2 + b * _x + c
            ans = _factors(1, r, 1, s)
            expr_str = _abc(1, b, c)
            # distractors: wrong factor pairs
            r2 = r + rng_obj.choice([-1, 1])
            if r2 == 0:
                r2 = r + 2
            s2 = c // r2 if r2 != 0 and c % r2 == 0 else s + rng_obj.choice([-1, 1])
            d_wrong_pair = _factors(1, r2, 1, s2)
            d_sign_r     = _factors(1, -r, 1, -s)  # negate both roots
            d_sign_one   = _factors(1, r, 1, -s)   # negate one root
            dist = make_distractors(ans, [d_wrong_pair, d_sign_r, d_sign_one])
            ctx = (f"Factor x^2 + {b}x + {c}: find r,s with r*s={c} and r+s={b}. "
                   f"r={r}, s={s}. Answer: {ans}. CRITICAL: stem is locked. "
                   f"DISTRACTOR ERRORS — "
                   f"'{d_wrong_pair}': used wrong factor pair ({r2},{s2}) — these do not satisfy r*s={c} and r+s={b}. "
                   f"'{d_sign_r}': negated both roots: used ({-r},{-s}) instead of ({r},{s}). "
                   f"'{d_sign_one}': negated one root: used ({r},{-s}) — gives product {r*(-s)} ≠ {c}.")
            exact = f"Which of the following is equivalent to \\({expr_str}\\)?"
            result = _exp_result(1, params, ph, ans, dist, "mcq", ctx, exact)
            if not validate_math_object(result):
                return result

        else:  # non_monic: (px+r)(x+s) = px^2+(ps+r)x+rs
            p = rng_obj.randint(2, 4)
            r = rng_obj.choice([-1, 1]) * rng_obj.randint(1, 5)
            s = rng_obj.choice([-1, 1]) * rng_obj.randint(1, 6)
            if r == 0 or s == 0:
                continue
            b = p * s + r    # x-coefficient
            c = r * s        # constant
            if b == 0 or c == 0:
                continue
            params = {"p": p, "r": r, "s": s, "tpl": "factor_trinomial", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            assert expand((p * _x + r) * (_x + s)) == p * _x**2 + b * _x + c
            ans = _factors(p, r, 1, s)
            expr_str = _abc(p, b, c)
            d_sign_r   = _factors(p, -r, 1, -s)  # both signs flipped
            d_drop_p   = _factors(1, r, 1, s)    # dropped leading coeff
            d_wrong_s  = _factors(p, r, 1, s + rng_obj.choice([-1, 1]) * rng_obj.randint(1, 2))
            dist = make_distractors(ans, [d_sign_r, d_drop_p, d_wrong_s])
            ctx = (f"Factor {p}x^2 + {b}x + {c} = ({_binomial(p, r)})({_binomial(1, s)}). "
                   f"Answer: {ans}. CRITICAL: stem is locked. "
                   f"DISTRACTOR ERRORS — "
                   f"'{d_sign_r}': flipped signs on both inner constants — used ({-r},{-s}) instead of ({r},{s}). "
                   f"'{d_drop_p}': dropped leading coefficient {p}, treated as monic (1,r,1,s) instead of ({p},r,1,s). "
                   f"'{d_wrong_s}': used incorrect value for the second root — product would not equal {c}.")
            exact = f"Which of the following is equivalent to \\({expr_str}\\)?"
            result = _exp_result(1, params, ph, ans, dist, "mcq", ctx, exact)
            if not validate_math_object(result):
                return result

    raise RuntimeError("factor_trinomial d1: could not generate unique params")


# ── D2 template functions ─────────────────────────────────────────────────────

def _d2_polynomial_multiply(rng_obj, exclude_params, variant=None):
    v = variant or rng_obj.choice(["linear_linear", "linear_quadratic"])
    for _ in range(200):
        if v == "linear_linear":
            a = rng_obj.randint(1, 4)
            b = rng_obj.choice([-1, 1]) * rng_obj.randint(1, 6)
            c = rng_obj.randint(1, 4)
            d = rng_obj.choice([-1, 1]) * rng_obj.randint(1, 6)
            if a == c and b == d:
                continue
            A = a * c
            B = a * d + b * c
            C = b * d
            params = {"a": a, "b": b, "c": c, "d": d, "tpl": "polynomial_multiply", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            assert expand((a * _x + b) * (c * _x + d)) == A * _x**2 + B * _x + C
            expr_str = f"({_binomial(a, b)})({_binomial(c, d)})"
            ans = _lp(_abc(A, B, C))
            d_sign_B  = _lp(_abc(A, -B, C))
            d_sign_C  = _lp(_abc(A, B, -C))
            d_no_mid  = _lp(_abc(A, 0, C))
            dist = make_distractors(ans, [d_sign_B, d_sign_C, d_no_mid])
            ctx = (f"FOIL: {a*c}x^2, ({a}*{d}+{b}*{c})x={B}x, {b}*{d}={C}. "
                   f"Answer: {_abc(A, B, C)}. CRITICAL: stem is locked. "
                   f"DISTRACTOR ERRORS — "
                   f"'{d_sign_B}': sign error on middle (x) term: got {-B}x instead of {B}x from cross-products. "
                   f"'{d_sign_C}': sign error on constant: got {-C} instead of {C} from {b}*{d}. "
                   f"'{d_no_mid}': omitted middle term entirely — only multiplied first*first and last*last, skipped outer/inner cross-terms.")
            exact = f"Which of the following is equivalent to \\({expr_str}\\)?"
            result = _exp_result(2, params, ph, ans, dist, "mcq", ctx, exact)
            if not validate_math_object(result):
                return result

        else:  # linear_quadratic: (ax+b)(cx^2+dx+e) = acx^3+(ad+bc)x^2+(ae+bd)x+be
            a = rng_obj.randint(1, 3)
            b = rng_obj.choice([-1, 1]) * rng_obj.randint(1, 4)
            c = rng_obj.randint(1, 3)
            d = rng_obj.choice([-1, 1]) * rng_obj.randint(1, 4)
            e = rng_obj.choice([-1, 1]) * rng_obj.randint(1, 5)
            A = a * c
            B = a * d + b * c
            C = a * e + b * d
            D = b * e
            if A == 0:
                continue
            params = {"a": a, "b": b, "c": c, "d": d, "e": e,
                      "tpl": "polynomial_multiply", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            assert expand((a * _x + b) * (c * _x**2 + d * _x + e)) == A * _x**3 + B * _x**2 + C * _x + D
            quad_str = _abc(c, d, e)
            expr_str = f"({_binomial(a, b)})({quad_str})"
            ans = _lp(_abcd(A, B, C, D))
            d_sign_B = _lp(_abcd(A, -B, C, D))
            d_sign_C = _lp(_abcd(A, B, -C, D))
            d_sign_D = _lp(_abcd(A, B, C, -D))
            dist = make_distractors(ans, [d_sign_B, d_sign_C, d_sign_D])
            ctx = (f"Distribute {_binomial(a, b)} over each term of {quad_str}. "
                   f"x^3 coeff={A}, x^2 coeff={B}, x coeff={C}, constant={D}. "
                   f"Answer: {_abcd(A, B, C, D)}. CRITICAL: stem is locked. "
                   f"DISTRACTOR ERRORS — "
                   f"'{d_sign_B}': sign error on x^2 coefficient: got {-B} instead of {B} (error in {a}*{d}+{b}*{c}). "
                   f"'{d_sign_C}': sign error on x coefficient: got {-C} instead of {C} (error in {a}*{e}+{b}*{d}). "
                   f"'{d_sign_D}': sign error on constant: got {-D} instead of {D} (error in {b}*{e}).")
            exact = f"Which of the following is equivalent to \\({expr_str}\\)?"
            result = _exp_result(2, params, ph, ans, dist, "mcq", ctx, exact)
            if not validate_math_object(result):
                return result

    raise RuntimeError("polynomial_multiply d2: could not generate unique params")


def _d2_add_subtract_polynomials(rng_obj, exclude_params, variant=None):
    v = variant or rng_obj.choice(["add_type", "subtract_type"])
    for _ in range(200):
        if v == "add_type":
            a1 = rng_obj.randint(2, 6); a2 = rng_obj.randint(1, 5)
            b1 = rng_obj.choice([-1,1]) * rng_obj.randint(1, 6)
            b2 = rng_obj.choice([-1,1]) * rng_obj.randint(1, 6)
            c1 = rng_obj.choice([-1,1]) * rng_obj.randint(1, 8)
            c2 = rng_obj.choice([-1,1]) * rng_obj.randint(1, 8)
            A = a1 + a2; B = b1 + b2; C = c1 + c2
            params = {"a1": a1, "a2": a2, "b1": b1, "b2": b2, "c1": c1, "c2": c2,
                      "tpl": "add_subtract_polynomials", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            p1 = _abc(a1, b1, c1); p2 = _abc(a2, b2, c2)
            expr_str = f"({p1}) + ({p2})"
            ans = _lp(_abc(A, B, C))
            d_sub_a   = _lp(_abc(a1 - a2, B, C))
            d_sign_b2 = _lp(_abc(A, b1 - b2, C))
            d_sign_c2 = _lp(_abc(A, B, c1 - c2))
            dist = make_distractors(ans, [d_sub_a, d_sign_b2, d_sign_c2])
            ctx = (f"Combine: {a1}+{a2}={A} for x^2; {b1}+{b2}={B} for x; {c1}+{c2}={C} constant. "
                   f"Answer: {_abc(A, B, C)}. CRITICAL: stem is locked. "
                   f"DISTRACTOR ERRORS — "
                   f"'{d_sub_a}': subtracted x^2 coefficients instead of adding: {a1}-{a2}={a1-a2} instead of {A}. "
                   f"'{d_sign_b2}': sign error on x-term of second polynomial: used {b1}-({b2})={b1-b2} instead of {B}. "
                   f"'{d_sign_c2}': sign error on constant of second polynomial: used {c1}-({c2})={c1-c2} instead of {C}.")
            exact = f"Which of the following is equivalent to \\({expr_str}\\)?"
            result = _exp_result(2, params, ph, ans, dist, "mcq", ctx, exact)
            if not validate_math_object(result):
                return result

        else:  # subtract_type: (p1) - (p2), distribute minus
            a1 = rng_obj.randint(3, 8); a2 = rng_obj.randint(1, a1 - 1)
            b1 = rng_obj.choice([-1,1]) * rng_obj.randint(1, 6)
            b2 = rng_obj.choice([-1,1]) * rng_obj.randint(1, 6)
            c1 = rng_obj.choice([-1,1]) * rng_obj.randint(1, 8)
            c2 = rng_obj.choice([-1,1]) * rng_obj.randint(1, 8)
            A = a1 - a2; B = b1 - b2; C = c1 - c2
            if A <= 0:
                continue
            params = {"a1": a1, "a2": a2, "b1": b1, "b2": b2, "c1": c1, "c2": c2,
                      "tpl": "add_subtract_polynomials", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            p1 = _abc(a1, b1, c1); p2 = _abc(a2, b2, c2)
            expr_str = f"({p1}) - ({p2})"
            ans = _lp(_abc(A, B, C))
            d_b2_sign = _lp(_abc(A, b1 + b2, C))
            d_c2_sign = _lp(_abc(A, B, c1 + c2))
            d_add_a   = _lp(_abc(a1 + a2, B, C))
            dist = make_distractors(ans, [d_b2_sign, d_c2_sign, d_add_a])
            ctx = (f"Distribute minus: -({_abc(a2, b2, c2)}) = {_abc(-a2, -b2, -c2)}. "
                   f"Add: {A}x^2 + {B}x + ({C}). "
                   f"Answer: {_abc(A, B, C)}. CRITICAL: stem is locked. "
                   f"DISTRACTOR ERRORS — "
                   f"'{d_b2_sign}': forgot to negate x-term of second polynomial: used {b1}+({b2})={b1+b2} instead of {B}={b1}-({b2}). "
                   f"'{d_c2_sign}': forgot to negate constant of second polynomial: used {c1}+({c2})={c1+c2} instead of {C}={c1}-({c2}). "
                   f"'{d_add_a}': added x^2 coefficients instead of subtracting: {a1}+{a2}={a1+a2} instead of {A}.")
            exact = f"Which of the following is equivalent to \\({expr_str}\\)?"
            result = _exp_result(2, params, ph, ans, dist, "mcq", ctx, exact)
            if not validate_math_object(result):
                return result

    raise RuntimeError("add_subtract_polynomials d2: could not generate unique params")


def _d2_exponent_rules(rng_obj, exclude_params, variant=None):
    v = variant or rng_obj.choice(["product_rule", "power_rule", "negative_exp"])
    for _ in range(200):
        if v == "product_rule":
            a = rng_obj.randint(2, 7); b = rng_obj.randint(2, 7)
            if a == b:
                continue
            params = {"a": a, "b": b, "tpl": "exponent_rules", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans   = _lat_xpow(a + b)
            d_mul = _lat_xpow(a * b)
            d_sub = _lat_xpow(a - b)
            d_two = _lat_expr(f"2x^{{{a+b}}}")
            dist  = make_distractors(ans, [d_mul, d_sub, d_two])
            exact = f"Which of the following is equivalent to \\(x^{{{a}}} \\cdot x^{{{b}}}\\)?"
            ctx   = (f"Product rule: x^{a} * x^{b} = x^({a}+{b}) = x^{a+b}. "
                     f"Answer: {ans}. CRITICAL: stem is locked. "
                     f"DISTRACTOR ERRORS — "
                     f"'{d_mul}': multiplied exponents {a}*{b}={a*b} instead of adding {a}+{b}={a+b}. "
                     f"'{d_sub}': subtracted exponents {a}-{b}={a-b} instead of adding. "
                     f"'{d_two}': added spurious coefficient 2 while still computing the exponent sum.")
            result = _exp_result(2, params, ph, ans, dist, "mcq", ctx, exact)
            if not validate_math_object(result):
                return result

        elif v == "power_rule":
            a = rng_obj.randint(2, 6); b = rng_obj.randint(2, 5)
            params = {"a": a, "b": b, "tpl": "exponent_rules", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans    = _lat_xpow(a * b)
            d_add  = _lat_xpow(a + b)
            d_pow  = _lat_xpow(a ** b)
            d_coef = _lat_expr(f"{b}x^{{{a}}}")
            dist   = make_distractors(ans, [d_add, d_pow, d_coef])
            exact  = f"Which of the following is equivalent to \\((x^{{{a}}})^{{{b}}}\\)?"
            ctx    = (f"Power rule: (x^{a})^{b} = x^({a}*{b}) = x^{a*b}. "
                      f"Answer: {ans}. CRITICAL: stem is locked. "
                      f"DISTRACTOR ERRORS — "
                      f"'{d_add}': added exponents {a}+{b}={a+b} instead of multiplying. "
                      f"'{d_pow}': raised inner exponent to outer power: x^({a}^{b}) = x^{a**b} (iterated exponentiation). "
                      f"'{d_coef}': moved outer exponent {b} to be a coefficient instead of multiplying: {b}x^{a}.")
            result = _exp_result(2, params, ph, ans, dist, "mcq", ctx, exact)
            if not validate_math_object(result):
                return result

        else:  # negative_exp: n * x^(-k) = n / x^k
            n = rng_obj.randint(2, 8); k = rng_obj.randint(2, 5)
            params = {"n": n, "k": k, "tpl": "exponent_rules", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans      = _lat_expr(f"\\frac{{{n}}}{{x^{{{k}}}}}")
            d_neg    = _lat_expr(f"-{n}x^{{{k}}}")  # thought x^-k = -x^k
            d_pos    = _lat_expr(f"{n}x^{{{k}}}")   # dropped negative sign
            d_negfrac = _lat_expr(f"\\frac{{-{n}}}{{x^{{{k}}}}}")
            dist     = make_distractors(ans, [d_neg, d_pos, d_negfrac])
            exact    = f"Which of the following is equivalent to \\({n}x^{{-{k}}}\\)?"
            ctx      = (f"Negative exponent rule: x^(-{k}) = 1/x^{k}. "
                        f"{n}x^(-{k}) = {n}/x^{k}. "
                        f"Answer: {ans}. CRITICAL: stem is locked. "
                        f"DISTRACTOR ERRORS — "
                        f"'{d_neg}': confused negative exponent with negative coefficient — wrote -{n}x^{k} instead of {n}/x^{k}. "
                        f"'{d_pos}': ignored the negative sign in the exponent entirely — wrote {n}x^{k}. "
                        f"'{d_negfrac}': applied the negative to the numerator of the fraction — wrote -{n}/x^{k}.")
            result   = _exp_result(2, params, ph, ans, dist, "mcq", ctx, exact)
            if not validate_math_object(result):
                return result

    raise RuntimeError("exponent_rules d2: could not generate unique params")


def _d2_factor_polynomial_medium(rng_obj, exclude_params, variant=None):
    v = variant or rng_obj.choice(["grouping", "complex_gcf"])
    for _ in range(200):
        if v == "grouping":
            # x^3 + p*x^2 + q*x + p*q = (x^2+q)(x+p) via grouping
            p = rng_obj.choice([-1, 1]) * rng_obj.randint(2, 6)
            q = rng_obj.choice([-1, 1]) * rng_obj.randint(2, 6)
            if p == q or p == 0 or q == 0:
                continue
            d_const = p * q
            params = {"p": p, "q": q, "tpl": "factor_polynomial_medium", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            assert expand((_x**2 + q) * (_x + p)) == _x**3 + p * _x**2 + q * _x + d_const
            expr_str = _abcd(1, p, q, d_const)
            ans = _lp(f"({_abc(1, 0, q)})({_binomial(1, p)})")
            d_sign_q = _lp(f"({_abc(1, 0, -q)})({_binomial(1, p)})")
            d_sign_p = _lp(f"({_abc(1, 0, q)})({_binomial(1, -p)})")
            d_wrong  = _lp(f"({_binomial(1, p)})({_binomial(1, q)})")
            dist = make_distractors(ans, [d_sign_q, d_sign_p, d_wrong])
            ctx = (f"Group: (x^3 + {p}x^2) + ({q}x + {d_const}) = x^2(x+{p}) + {q}(x+{p}). "
                   f"Factor: ({_abc(1, 0, q)})({_binomial(1, p)}). CRITICAL: stem is locked. "
                   f"DISTRACTOR ERRORS — "
                   f"'{d_sign_q}': sign error on q in first factor — wrote (x^2 - {abs(q)}) instead of (x^2 + {q}). "
                   f"'{d_sign_p}': sign error on p in second factor after grouping — wrote (x - {abs(p)}) instead of (x + {p}). "
                   f"'{d_wrong}': incorrect grouping strategy — factored as two linear binomials ({_binomial(1, p)})({_binomial(1, q)}) instead of (quadratic)(linear).")
            exact = f"Which of the following is equivalent to \\({expr_str}\\)?"
            result = _exp_result(2, params, ph, ans, dist, "mcq", ctx, exact)
            if not validate_math_object(result):
                return result

        else:  # complex_gcf: a*x^2*y + b*x*y^2 = xy(ax+by)
            a = rng_obj.randint(2, 7); b = rng_obj.randint(2, 7)
            if a == b:
                continue
            params = {"a": a, "b": b, "tpl": "factor_polynomial_medium", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            expr_str = f"{a}x^2y + {b}xy^2"
            ans = _lp(f"xy({a}x + {b}y)")
            d_xpow    = _lp(f"xy({a}x^2 + {b}y)")
            d_swap    = _lp(f"xy({a}y + {b}x)")
            d_wrongin = _lp(f"xy({a}x + {b}y^2)")
            dist = make_distractors(ans, [d_xpow, d_swap, d_wrongin])
            ctx = (f"GCF of {a}x^2*y and {b}*x*y^2 is xy. Factor: xy({a}x + {b}y). "
                   f"CRITICAL: stem is locked. "
                   f"DISTRACTOR ERRORS — "
                   f"'{d_xpow}': only factored out y from first term instead of xy, leaving extra x^2 inside. "
                   f"'{d_swap}': swapped the x and y terms inside the inner factor. "
                   f"'{d_wrongin}': only factored out x from second term instead of xy, leaving extra y^2 inside.")
            exact = f"Which of the following is equivalent to \\({expr_str}\\)?"
            result = _exp_result(2, params, ph, ans, dist, "mcq", ctx, exact)
            if not validate_math_object(result):
                return result

    raise RuntimeError("factor_polynomial_medium d2: could not generate unique params")


# ── D3 template functions ─────────────────────────────────────────────────────

def _d3_factor_to_reveal_property(rng_obj, exclude_params, variant=None):
    # Only variant: complete_square
    # x^2 + bx + c = (x + h)^2 + k  where h = b/2, k = c - h^2
    for _ in range(200):
        # Use even b for clean h value
        b = rng_obj.choice([-1, 1]) * rng_obj.randint(1, 6) * 2
        c = rng_obj.choice([-1, 1]) * rng_obj.randint(1, 12)
        h = b // 2
        k = c - h * h
        params = {"b": b, "c": c, "tpl": "factor_to_reveal_property", "variant": "complete_square"}
        ph = param_hash(params)
        if ph in exclude_params:
            continue
        assert expand((_x + h)**2 + k) == _x**2 + b * _x + c
        expr_str = _abc(1, b, c)
        h_str = f"x + {h}" if h >= 0 else f"x - {abs(h)}"
        if k == 0:
            ans_plain = f"({h_str})^2"
        elif k > 0:
            ans_plain = f"({h_str})^2 + {k}"
        else:
            ans_plain = f"({h_str})^2 - {abs(k)}"
        ans = _lp(ans_plain)
        d_no_adj_plain = f"({h_str})^2 + {c}"
        d_use_h2_plain = f"({h_str})^2 - {h*h}"
        wrong_hstr = f"x + {b}" if b >= 0 else f"x - {abs(b)}"
        wrong_k = c - b * b
        d_wrong_h_plain = f"({wrong_hstr})^2 - {abs(wrong_k)}" if wrong_k < 0 else f"({wrong_hstr})^2 + {wrong_k}"
        dist = make_distractors(ans, [_lp(d_no_adj_plain), _lp(d_use_h2_plain), _lp(d_wrong_h_plain)])
        ctx = (f"Complete the square: half of {b} is {h}, {h}^2 = {h*h}. "
               f"x^2 + {b}x + {c} = (x^2 + {b}x + {h*h}) - {h*h} + {c} = ({h_str})^2 + {k}. "
               f"Answer: {ans_plain}. CRITICAL: stem is locked. "
               f"DISTRACTOR ERRORS — "
               f"'{d_no_adj_plain}': added original constant {c} without adjusting — forgot to subtract h^2={h*h}. "
               f"'{d_use_h2_plain}': subtracted h^2={h*h} but dropped the original constant {c} entirely. "
               f"'{d_wrong_h_plain}': used h={b} (the full coefficient) instead of h={h} (half the coefficient).")
        exact = f"Which of the following is equivalent to \\({expr_str}\\)?"
        result = _exp_result(3, params, ph, ans, dist, "mcq", ctx, exact)
        if not validate_math_object(result):
            return result

    raise RuntimeError("factor_to_reveal_property d3: could not generate unique params")


def _d3_rational_expression_add(rng_obj, exclude_params, variant=None):
    # poly_denom: p/(x+a) + q/(x+b)
    for _ in range(200):
        a = rng_obj.choice([-1, 1]) * rng_obj.randint(1, 6)
        b = rng_obj.choice([-1, 1]) * rng_obj.randint(1, 6)
        p = rng_obj.randint(1, 5)
        q = rng_obj.randint(1, 5)
        if a == b or a == -b:
            continue
        # Numerator: p(x+b) + q(x+a) = (p+q)x + (pb + qa)
        num_x  = p + q
        num_c  = p * b + q * a
        denom_a_str = f"x + {a}" if a >= 0 else f"x - {abs(a)}"
        denom_b_str = f"x + {b}" if b >= 0 else f"x - {abs(b)}"
        params = {"a": a, "b": b, "p": p, "q": q,
                  "tpl": "rational_expression_add", "variant": "poly_denom"}
        ph = param_hash(params)
        if ph in exclude_params:
            continue
        num_str = _ab(num_x, num_c)
        denom_str = f"({denom_a_str})({denom_b_str})"
        ans = f"({num_str}) / {denom_str}"
        # Distractors
        d_add_num   = f"{p + q} / {denom_str}"             # added numerators without LCD
        d_add_denom = f"({num_str}) / ({denom_a_str} + {denom_b_str})"  # added denominators
        # Sign error: qp*a instead of q*a in numerator
        wrong_c = p * b - q * a
        d_sign  = f"({_ab(num_x, wrong_c)}) / {denom_str}"
        dist = make_distractors(ans, [d_add_num, d_add_denom, d_sign])
        ctx = (f"LCD = {denom_str}. "
               f"Numerator: {p}({denom_b_str}) + {q}({denom_a_str}) "
               f"= {p}x + {p*b} + {q}x + {q*a} = {num_str}. "
               f"Answer: {ans}. CRITICAL: stem is locked. "
               f"DISTRACTOR ERRORS — "
               f"'{d_add_num}': student added numerators ({p}+{q}={p+q}) without finding LCD, ignoring x terms. "
               f"'{d_add_denom}': student added denominators instead of multiplying them for the LCD. "
               f"'{d_sign}': student computed {q}({denom_a_str}) as {q}x+{q*abs(a)} instead of {q}x+{q*a} "
               f"(sign error on the constant of {denom_a_str}), giving numerator {_ab(num_x, wrong_c)} instead of {num_str}.")
        exact = f"Which of the following is equivalent to {p}/({denom_a_str}) + {q}/({denom_b_str})?"
        result = _exp_result(3, params, ph, ans, dist, "mcq", ctx, exact)
        if not validate_math_object(result):
            return result

    raise RuntimeError("rational_expression_add d3: could not generate unique params")


def _d3_polynomial_factor_with_constant(rng_obj, exclude_params, variant=None):
    v = variant or rng_obj.choice(["find_k", "identify_factor"])
    for _ in range(200):
        # x^2 + kx + c = (x - r1)(x + r2) where r1, r2 > 0
        r1 = rng_obj.randint(1, 7)
        r2 = rng_obj.randint(1, 7)
        if r1 == r2:
            continue
        k = r2 - r1     # coefficient of x: -(r1) + r2
        c = -r1 * r2    # constant: (−r1)(r2) = −r1*r2
        if k == 0 or c == 0:
            continue
        params = {"r1": r1, "r2": r2, "tpl": "polynomial_factor_with_constant", "variant": v}
        ph = param_hash(params)
        if ph in exclude_params:
            continue

        poly_str = _abc(1, k, c)
        assert expand((_x - r1) * (_x + r2)) == _x**2 + k * _x + c

        if v == "find_k":
            c_show = c
            c_sign = "+" if c_show >= 0 else "-"
            poly_shown = f"x^2 + kx {c_sign} {abs(c_show)}"
            exact = f"If \\(x - {r1}\\) is a factor of \\({poly_shown}\\), what is the value of k?"
            ans   = str(k)
            d_neg_k  = str(-k)             # sign error
            d_r2     = str(r2)             # gave other root instead of k
            d_r1     = str(r1)             # gave known root instead of k
            dist = make_distractors(ans, [d_neg_k, d_r2, d_r1])
            ctx = (f"Since (x - {r1}) is a factor, x={r1} is a root. "
                   f"Substitute: {r1}^2 + k*{r1} + ({c}) = 0 → {r1**2 + c} + {r1}k = 0 → k = {k}. "
                   f"Answer: {k}. CRITICAL: stem is locked. "
                   f"DISTRACTOR ERRORS — "
                   f"'{d_neg_k}': sign error — solved {r1}k = {-(r1**2 + c)} and wrote k = {-k} (negated). "
                   f"'{d_r2}': found the other root x={r2} instead of solving for the coefficient k. "
                   f"'{d_r1}': gave the root {r1} from the given factor (x - {r1}) as the answer instead of computing k.")
        else:  # identify_factor: which is a factor of x^2 + kx + c?
            exact = f"Which of the following is a factor of \\({poly_str}\\)?"
            ans   = f"x - {r1}"
            d_sign_r1 = f"x + {r1}"       # wrong sign on r1
            d_sign_r2 = f"x - {r2}"       # the other root with sign flipped
            d_const   = f"x - {r1*r2}"   # used constant directly
            dist = make_distractors(ans, [d_sign_r1, d_sign_r2, d_const])
            ctx = (f"Factor: {poly_str} = (x - {r1})(x + {r2}). "
                   f"Factors are (x - {r1}) and (x + {r2}). "
                   f"Answer: x - {r1}. CRITICAL: stem is locked. "
                   f"DISTRACTOR ERRORS — "
                   f"'{d_sign_r1}': wrong sign — (x + {r1}) has root x = -{r1}, which is not a root of this polynomial. "
                   f"'{d_sign_r2}': the actual factor is (x + {r2}), not (x - {r2}); (x - {r2}) would give root x = {r2} which is not a root here. "
                   f"'{d_const}': used product {r1}*{r2}={r1*r2} as a single root instead of finding individual factors.")

        result = _exp_result(3, params, ph, ans, dist, "mcq", ctx, exact)
        if not validate_math_object(result):
            return result

    raise RuntimeError("polynomial_factor_with_constant d3: could not generate unique params")


def _d3_polynomial_coefficient_find(rng_obj, exclude_params, variant=None):
    v = variant or rng_obj.choice(["specific_term", "compare_forms"])
    for _ in range(200):
        if v == "specific_term":
            # (ax+b)(cx^2+dx+e): find coefficient of x^2
            a = rng_obj.randint(1, 4)
            b = rng_obj.choice([-1, 1]) * rng_obj.randint(1, 5)
            c = rng_obj.randint(1, 4)
            d = rng_obj.choice([-1, 1]) * rng_obj.randint(1, 5)
            e = rng_obj.choice([-1, 1]) * rng_obj.randint(1, 5)
            # x^2 coefficient in (ax+b)(cx^2+dx+e): a*d + b*c
            coeff_x2 = a * d + b * c
            if coeff_x2 == 0:
                continue
            params = {"a": a, "b": b, "c": c, "d": d, "e": e,
                      "tpl": "polynomial_coefficient_find", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            quad_str = _abc(c, d, e)
            expr_str = f"({_binomial(a, b)})({quad_str})"
            ans  = str(coeff_x2)
            d_only_ad = str(a * d)    # forgot b*c contribution
            d_only_bc = str(b * c)    # forgot a*d contribution
            d_abs_val = str(abs(coeff_x2)) if coeff_x2 < 0 else str(-coeff_x2)
            dist = make_distractors(ans, [d_only_ad, d_only_bc, d_abs_val])
            ctx = (f"x^2 terms come from: a*d*x^2 = {a}*{d}*x^2 = {a*d}x^2 AND b*c*x^2 = {b}*{c}x^2 = {b*c}x^2. "
                   f"Sum: {coeff_x2}. Answer: {coeff_x2}. CRITICAL: stem is locked. "
                   f"DISTRACTOR ERRORS — "
                   f"'{d_only_ad}': only counted the a*d cross-term ({a}*{d}={a*d}), forgot the b*c cross-term ({b}*{c}={b*c}). "
                   f"'{d_only_bc}': only counted the b*c cross-term ({b}*{c}={b*c}), forgot the a*d cross-term ({a}*{d}={a*d}). "
                   f"'{d_abs_val}': sign error — negated the result, wrote {d_abs_val} instead of {coeff_x2}.")
            exact = (f"The expression \\({expr_str}\\) is expanded and written in standard form. "
                     f"What is the coefficient of \\(x^2\\)?")
            result = _exp_result(3, params, ph, ans, dist, "mcq", ctx, exact)
            if not validate_math_object(result):
                return result

        else:  # compare_forms (SPR)
            # (x + p)(x + q) = x^2 + (p+q)x + pq; given p+q=S and p-q=D, find pq
            S = rng_obj.randint(6, 14)   # sum p+q
            D = rng_obj.choice([2, 4, 6]) # difference p-q (even for clean integers)
            if D >= S or (S + D) % 2 != 0:  # need S even so p,q are integers
                continue
            p = (S + D) // 2
            q = (S - D) // 2
            if p == q or p <= 0 or q <= 0:
                continue
            pq = p * q
            params = {"S": S, "D": D, "p": p, "q": q, "pq": pq,
                      "tpl": "polynomial_coefficient_find", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans  = str(pq)
            sm, sx = spr_bounds(ans)
            d_wrong1 = str(((S - D) // 2) * (S + D))  # used wrong pair
            d_sum    = str(S)                           # gave sum instead of product
            ctx = (f"p + q = {S} and p - q = {D}. Add: 2p = {S+D}, p = {p}; q = {q}. "
                   f"c = pq = {p}*{q} = {pq}. CRITICAL: stem is locked.")
            exact = (f"The expression (x + p)(x + q) is equivalent to x^2 + {S}x + c, "
                     f"where p and q are positive integers and p - q = {D}. "
                     f"What is the value of c?")
            result = _exp_result(3, params, ph, ans, [], "spr", ctx, exact)
            result["sprMin"] = sm
            result["sprMax"] = sx
            if not validate_math_object(result):
                return result

    raise RuntimeError("polynomial_coefficient_find d3: could not generate unique params")


def _d3_exponent_equation_solve(rng_obj, exclude_params, variant=None):
    v = variant or rng_obj.choice(["rational_exp", "solve_for_var"])
    for _ in range(200):
        if v == "rational_exp":
            # x^(p/q) = c; solution x = c^(q/p)
            p = rng_obj.choice([2, 3])   # numerator of exponent
            q = rng_obj.choice([2, 3, 4])  # denominator
            if p >= q:
                continue
            if _math.gcd(p, q) != 1:  # skip reducible fractions (e.g. 2/4 = 1/2)
                continue
            # Pick c so that c^(q/p) is a clean integer
            base = rng_obj.randint(2, 5)
            c = base ** p          # c = base^p, so x = c^(q/p) = base^q
            x_ans = base ** q
            params = {"p": p, "q": q, "base": base, "c": c,
                      "tpl": "exponent_equation_solve", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            assert round(c ** (q / p)) == x_ans
            exact = f"Which value of x satisfies {_lat_rat_exp(p, q)} = {c}?"
            ans   = str(x_ans)
            d_mult  = str(c * q // p)   # multiplied: c * (q/p)
            d_root  = str(round(c ** (1 / p)))  # only took pth root
            d_cubic = str(c ** q)       # raised to q instead of q/p
            dist = make_distractors(ans, [d_mult, d_root, d_cubic])
            ctx = (f"Raise both sides to reciprocal power {q}/{p}: x = {c}^({q}/{p}) = "
                   f"({c}^(1/{p}))^{q} = {round(c**(1/p))}^{q} = {x_ans}. "
                   f"Answer: {x_ans}. CRITICAL: stem is locked. "
                   f"DISTRACTOR ERRORS — "
                   f"'{d_mult}': multiplied {c}*(q/p) = {c}*({q}/{p}) = {c*q//p} instead of raising to power {q}/{p}. "
                   f"'{d_root}': only took the {p}th root of {c} = {round(c**(1/p))}, forgot to then raise to the {q}th power. "
                   f"'{d_cubic}': raised {c} to the full power {q} = {c**q} instead of the reciprocal power {q}/{p}.")
            result = _exp_result(3, params, ph, ans, dist, "mcq", ctx, exact)
            if not validate_math_object(result):
                return result

        else:  # solve_for_var: base^(kx) = base^n → x = n/k
            base = rng_obj.choice([2, 3, 5])
            n    = rng_obj.choice([4, 6, 8, 9, 10, 12])
            k    = rng_obj.choice([2, 3, 4])
            if n % k != 0:
                continue
            x_ans = n // k
            if x_ans <= 1:
                continue
            rhs_val = base ** n
            params = {"base": base, "n": n, "k": k, "rhs": rhs_val,
                      "tpl": "exponent_equation_solve", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            assert base ** (k * x_ans) == rhs_val
            lhs_str = _lat_expr(f"{base}^{{{k}x}}")
            exact = f"If {lhs_str} = {rhs_val}, what is the value of x?"
            ans   = str(x_ans)
            d_exp  = str(n)             # found exponent but forgot to divide by k
            d_mul  = str(n * k)         # multiplied instead of dividing
            d_half = str(x_ans - 1)     # off-by-one
            dist = make_distractors(ans, [d_exp, d_mul, d_half])
            ctx = (f"{base}^({k}x) = {rhs_val} = {base}^{n}. So {k}x = {n}, x = {x_ans}. "
                   f"CRITICAL: stem is locked. "
                   f"DISTRACTOR ERRORS — "
                   f"'{d_exp}': found the equated exponent {n} but forgot to divide by k={k} — gave x = {n} instead of {x_ans}. "
                   f"'{d_mul}': multiplied {n}*{k}={n*k} instead of dividing to find x. "
                   f"'{d_half}': off-by-one arithmetic error — got x = {x_ans-1} instead of {x_ans}.")
            result = _exp_result(3, params, ph, ans, dist, "mcq", ctx, exact)
            if not validate_math_object(result):
                return result

    raise RuntimeError("exponent_equation_solve d3: could not generate unique params")


# ── Routing dicts ─────────────────────────────────────────────────────────────

_D1 = {
    "combine_like_terms":       {"fn": _d1_combine_like_terms,       "variants": ["distribute_first", "pure_collect"]},
    "factor_gcf":               {"fn": _d1_factor_gcf,               "variants": ["monomial_gcf", "binomial_gcf"]},
    "rational_exponent_radical": {"fn": _d1_rational_exponent_radical, "variants": ["radical_to_exp", "exp_to_radical"]},
    "factor_trinomial":         {"fn": _d1_factor_trinomial,         "variants": ["monic", "non_monic"]},
}

_D2 = {
    "polynomial_multiply":         {"fn": _d2_polynomial_multiply,         "variants": ["linear_linear", "linear_quadratic"]},
    "add_subtract_polynomials":    {"fn": _d2_add_subtract_polynomials,    "variants": ["add_type", "subtract_type"]},
    "exponent_rules":              {"fn": _d2_exponent_rules,              "variants": ["product_rule", "power_rule", "negative_exp"]},
    "factor_polynomial_medium":    {"fn": _d2_factor_polynomial_medium,    "variants": ["grouping", "complex_gcf"]},
}

_D3 = {
    "factor_to_reveal_property":      {"fn": _d3_factor_to_reveal_property,      "variants": ["complete_square"]},
    "rational_expression_add":        {"fn": _d3_rational_expression_add,        "variants": ["poly_denom"]},
    "polynomial_factor_with_constant": {"fn": _d3_polynomial_factor_with_constant, "variants": ["find_k", "identify_factor"]},
    "polynomial_coefficient_find":    {"fn": _d3_polynomial_coefficient_find,    "variants": ["specific_term", "compare_forms"]},
    "exponent_equation_solve":        {"fn": _d3_exponent_equation_solve,        "variants": ["rational_exp", "solve_for_var"]},
}

_ROUTING = {1: _D1, 2: _D2, 3: _D3}


# ── Public metadata API ───────────────────────────────────────────────────────

def exp_variants(difficulty: int, template: str = None) -> dict:
    """
    Return variant metadata for equivalent_expressions.

    If template is None: returns {template: [variants]} for all templates at the given difficulty.
    If template is given: returns {"variants": [...]} for that template.
    """
    routing = _ROUTING.get(difficulty, {})
    if template is None:
        return {tpl: entry["variants"] for tpl, entry in routing.items()}
    if template not in routing:
        raise ValueError(f"Unknown template '{template}' for equivalent_expressions d{difficulty}")
    return {"variants": routing[template]["variants"]}


# ── Main generator ────────────────────────────────────────────────────────────

def gen_equivalent_expressions(difficulty: int, rng_obj: random.Random,
                                exclude_params: set,
                                force_template: str = None,
                                force_variant: str = None,
                                **_kwargs) -> dict:
    """
    Equivalent expressions generator (EXP).

    All templates set exactStem — the math expression must be reproduced verbatim.
    Dispatches to per-template functions via _D1/_D2/_D3 routing dicts.
    """
    clamped = min(max(difficulty, 1), 3)
    routing = _ROUTING.get(clamped, _D3)

    if force_template is not None:
        if force_template not in routing:
            valid = sorted(routing.keys())
            raise ValueError(
                f"--template '{force_template}' is not valid for "
                f"equivalent_expressions d{clamped}. Valid: {valid}"
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
