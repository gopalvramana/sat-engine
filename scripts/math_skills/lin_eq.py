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

def _leq_result(d, params, ph, ans, spr, distractors, qt="mcq", ctx=""):
    sm, sx = spr if spr else (None, None)
    return {"skill": "linear_eq_one_var", "difficulty": d, "questionType": qt,
            "params": params, "paramHash": ph, "verifiedAnswer": ans,
            "distractors": distractors, "sprMin": sm, "sprMax": sx,
            "scenarioTag": None, "diagramSpec": None,
            "questionContext": ctx or f"Solve the linear equation for the unknown variable. The answer is {ans}."}


# ── d1 template functions ─────────────────────────────────────────────────────

def _d1_direct_solve_one_step(rng_obj, exclude_params, variant=None):
    """ax = c; solve for x."""
    x = symbols("x")
    for _ in range(200):
        a = rng_obj.randint(2, 9)
        if variant == "small_coeff" and a > 5:
            continue
        if variant == "large_coeff" and a <= 5:
            continue
        answer = rng_obj.randint(1, 9)
        c = a * answer
        params = {"a": a, "c": c, "tpl": "direct_solve_one_step",
                  "variant": variant or ("large_coeff" if a > 5 else "small_coeff")}
        ph = param_hash(params)
        if ph in exclude_params:
            continue
        sol = solve(a * x - c, x)
        assert sol and sol[0] == answer
        ans = fmt_num(answer)
        dist = make_distractors(ans, [
            fmt_num(c - a),
            fmt_num(c + a),
            str(c),
            str(a),
        ])
        ctx = (f"Solve: {a}x = {c}. Divide both sides by {a}: x = {c}/{a} = {answer}. "
               f"The question must ask: What is the value of x in the equation {a}x = {c}?")
        return _leq_result(1, params, ph, ans, None, dist, "mcq", ctx)
    raise RuntimeError("direct_solve_one_step d1: could not generate unique params")


def _d1_direct_solve_two_step(rng_obj, exclude_params, variant=None):
    """ax + b = c; solve for x."""
    x = symbols("x")
    for _ in range(200):
        a = rng_obj.randint(2, 7)
        answer = rng_obj.randint(1, 8)
        b = rng_obj.choice([-1, 1]) * rng_obj.randint(1, 10)
        if variant == "pos_const" and b < 0:
            continue
        if variant == "neg_const" and b > 0:
            continue
        c = a * answer + b
        if c <= 0:
            continue
        params = {"a": a, "b": b, "c": c, "tpl": "direct_solve_two_step",
                  "variant": variant or ("neg_const" if b < 0 else "pos_const")}
        ph = param_hash(params)
        if ph in exclude_params:
            continue
        sol = solve(a * x + b - c, x)
        assert sol and sol[0] == answer
        ans = fmt_num(answer)
        dist = make_distractors(ans, [
            fmt_num(Rational(c, a)),
            fmt_num(c - b),
            fmt_num(c - a),
            fmt_num(c - b + a),
        ])
        ctx = (f"Solve: {a}x + {b} = {c}. "
               f"Subtract {b} from both sides: {a}x = {c - b}. "
               f"Divide by {a}: x = {answer}. "
               f"The question must ask: What is the value of x?")
        return _leq_result(1, params, ph, ans, None, dist, "mcq", ctx)
    raise RuntimeError("direct_solve_two_step d1: could not generate unique params")


def _d1_direct_solve_distribute(rng_obj, exclude_params, variant=None):
    """outer_a(inner_b·x + inner_c) = rhs; solve for x."""
    x = symbols("x")
    for _ in range(200):
        inner_b = rng_obj.randint(2, 4)
        inner_c = rng_obj.choice([-1, 1]) * rng_obj.randint(1, 5)
        if variant == "small_outer":
            outer_a = 2
        elif variant == "large_outer":
            outer_a = rng_obj.choice([3, 4])
        else:
            outer_a = rng_obj.randint(2, 4)
        answer = rng_obj.randint(1, 5)
        rhs = outer_a * (inner_b * answer + inner_c)
        if rhs <= 0:
            continue
        params = {"outer_a": outer_a, "inner_b": inner_b,
                  "inner_c": inner_c, "rhs": rhs, "tpl": "direct_solve_distribute",
                  "variant": variant or ("small_outer" if outer_a == 2 else "large_outer")}
        ph = param_hash(params)
        if ph in exclude_params:
            continue
        check = solve(outer_a * (inner_b * x + inner_c) - rhs, x)
        assert check and check[0] == answer
        ans = fmt_num(answer)
        expanded_lhs = outer_a * inner_b
        expanded_const = outer_a * inner_c
        dist = make_distractors(ans, [
            fmt_num(Rational(rhs, outer_a)),
            fmt_num(Rational(rhs, inner_b)),
            fmt_num(Rational(rhs, outer_a * inner_b)),
            fmt_num(inner_b * answer),
        ])
        ctx = (f"Distribute: {outer_a}({inner_b}x + ({inner_c})) = {rhs}. "
               f"Expanding: {expanded_lhs}x + ({expanded_const}) = {rhs}. "
               f"Isolate x: x = ({rhs} − ({expanded_const})) ÷ {expanded_lhs} = {answer}. "
               f"The question must ask: What is the value of x?")
        return _leq_result(1, params, ph, ans, None, dist, "mcq", ctx)
    raise RuntimeError("direct_solve_distribute d1: could not generate unique params")


def _d1_find_expression_given_x(rng_obj, exclude_params, variant=None):
    """x = n; find x + k."""
    for _ in range(200):
        n = rng_obj.randint(1, 12)
        if variant == "small_n" and n > 6:
            continue
        if variant == "large_n" and n <= 6:
            continue
        k = rng_obj.randint(2, 18)
        answer = n + k
        params = {"n": n, "k": k, "tpl": "find_expression_given_x",
                  "variant": variant or ("large_n" if n > 6 else "small_n")}
        ph = param_hash(params)
        if ph in exclude_params:
            continue
        x = symbols("x")
        sol = solve(x - n, x)
        assert sol and int(sol[0]) + k == answer
        ans = fmt_num(answer)
        dist = make_distractors(ans, [
            str(n),
            str(k),
            str(n * k),
            str(n - k),
        ])
        ctx = (f"x = {n}. Substitute: x + {k} = {n} + {k} = {answer}. "
               f"The question must ask: If x = {n}, what is the value of x + {k}?")
        return _leq_result(1, params, ph, ans, None, dist, "mcq", ctx)
    raise RuntimeError("find_expression_given_x d1: could not generate unique params")


def _d1_find_expression_shift(rng_obj, exclude_params, variant=None):
    """ax − b = c; find ax + b."""
    x = symbols("x")
    for _ in range(200):
        a = rng_obj.randint(2, 6)
        b = rng_obj.randint(1, 10)
        if variant == "small_b" and b > 5:
            continue
        if variant == "large_b" and b <= 5:
            continue
        answer_x = rng_obj.randint(2, 8)
        c = a * answer_x - b
        if c <= 0:
            continue
        ax_val = a * answer_x
        expr_val = ax_val + b
        params = {"a": a, "b": b, "c": c, "tpl": "find_expression_shift",
                  "variant": variant or ("large_b" if b > 5 else "small_b")}
        ph = param_hash(params)
        if ph in exclude_params:
            continue
        sol = solve(a * x - b - c, x)
        assert sol and sol[0] == answer_x
        assert a * answer_x + b == expr_val
        ans = fmt_num(expr_val)
        dist = make_distractors(ans, [str(b), str(ax_val), str(c), str(answer_x)])
        ctx = (f"Equation: {a}x − {b} = {c}. "
               f"Add {b} to both sides: {a}x = {c + b} = {ax_val}. "
               f"Expression {a}x + {b} = {ax_val} + {b} = {expr_val}. "
               f"The question must ask: If {a}x − {b} = {c}, "
               f"what is the value of {a}x + {b}?")
        return _leq_result(1, params, ph, ans, None, dist, "mcq", ctx)
    raise RuntimeError("find_expression_shift d1: could not generate unique params")


def _d1_find_expression_divide(rng_obj, exclude_params, variant=None):
    """ax = c; find kx."""
    x = symbols("x")
    for _ in range(200):
        a = rng_obj.randint(2, 7)
        x_val = rng_obj.randint(2, 9)
        c = a * x_val
        k = rng_obj.choice([j for j in range(2, 25) if j != a])
        if variant == "small_k" and k >= 10:
            continue
        if variant == "large_k" and k < 10:
            continue
        expr_val = k * x_val
        if expr_val > 200:
            continue
        params = {"a": a, "c": c, "k": k, "tpl": "find_expression_divide",
                  "variant": variant or ("large_k" if k >= 10 else "small_k")}
        ph = param_hash(params)
        if ph in exclude_params:
            continue
        sol = solve(a * x - c, x)
        assert sol and sol[0] == x_val
        assert k * x_val == expr_val
        ans = fmt_num(expr_val)
        dist = make_distractors(ans, [
            str(x_val),
            str(c),
            str(k * a),
            str(c + k),
        ])
        ctx = (f"Equation: {a}x = {c}. Solve: x = {c}/{a} = {x_val}. "
               f"Then {k}x = {k} × {x_val} = {expr_val}. "
               f"The question must ask: If {a}x = {c}, what is the value of {k}x?")
        return _leq_result(1, params, ph, ans, None, dist, "mcq", ctx)
    raise RuntimeError("find_expression_divide d1: could not generate unique params")


def _d1_equivalent_equation(rng_obj, exclude_params, variant=None):
    """ax + b = c; find ax."""
    x = symbols("x")
    for _ in range(200):
        a = rng_obj.randint(2, 7)
        answer = rng_obj.randint(2, 9)
        b = rng_obj.randint(1, 10)
        c = a * answer + b
        correct_rhs = c - b
        if variant == "small_rhs" and correct_rhs > 10:
            continue
        if variant == "large_rhs" and correct_rhs <= 10:
            continue
        params = {"a": a, "b": b, "c": c, "tpl": "equivalent_equation",
                  "variant": variant or ("large_rhs" if correct_rhs > 10 else "small_rhs")}
        ph = param_hash(params)
        if ph in exclude_params:
            continue
        sol = solve(a * x + b - c, x)
        assert sol and sol[0] == answer
        assert correct_rhs == a * answer
        wrong = [c, c + b, b, c - a]
        wrong = list(dict.fromkeys([r for r in wrong if r != correct_rhs]))
        pad = 1
        while len(wrong) < 3:
            v = correct_rhs + pad * 2
            if v not in wrong and v != correct_rhs:
                wrong.append(v)
            pad += 1
        ans = fmt_num(correct_rhs)
        dist = [str(wrong[0]), str(wrong[1]), str(wrong[2])]
        ctx = (f"Equation: {a}x + {b} = {c}. Subtract {b} from both sides: {a}x = {correct_rhs}. "
               f"The question must ask: In the equation {a}x + {b} = {c}, "
               f"what is the value of {a}x? "
               f"Write ONLY the question stem. Do NOT list or reference the answer choices.")
        return _leq_result(1, params, ph, ans, None, dist, "mcq", ctx)
    raise RuntimeError("equivalent_equation d1: could not generate unique params")


def _d1_infinite_solutions_simple(rng_obj, exclude_params, variant=None):
    """ax + k = a(x + c); find k for infinite solutions."""
    x = symbols("x")
    for _ in range(200):
        a = rng_obj.randint(2, 7)
        c = rng_obj.randint(2, 12)
        k_ans = a * c
        if variant == "small_product" and k_ans > 12:
            continue
        if variant == "large_product" and k_ans <= 12:
            continue
        params = {"a": a, "c": c, "tpl": "infinite_solutions_simple",
                  "variant": variant or ("large_product" if k_ans > 12 else "small_product")}
        ph = param_hash(params)
        if ph in exclude_params:
            continue
        lhs_chk = a * x + k_ans
        rhs_chk = a * (x + c)
        assert sp.expand(lhs_chk - rhs_chk) == 0
        ans = fmt_num(k_ans)
        dist = make_distractors(ans, [
            str(a + c),
            str(c),
            str(a),
            str(0),
        ])
        ctx = (f"Equation: {a}x + k = {a}(x + {c}). "
               f"Expand RHS: {a}x + {k_ans}. "
               f"For an identity, constants must match: k = {k_ans}. "
               f"The question must ask: For what value of k does the equation "
               f"{a}x + k = {a}(x + {c}) have infinitely many solutions?")
        return _leq_result(1, params, ph, ans, None, dist, "mcq", ctx)
    raise RuntimeError("infinite_solutions_simple d1: could not generate unique params")


def _d1_reciprocal_expression(rng_obj, exclude_params, variant=None):
    """(1/a)x = b; find (1/b)x."""
    x = symbols("x")
    for _ in range(200):
        a = rng_obj.randint(2, 8)
        b = rng_obj.randint(2, 8)
        while b == a:
            b = rng_obj.randint(2, 8)
        if variant == "small_vals" and (a > 5 or b > 5):
            continue
        if variant == "large_vals" and (a <= 5 and b <= 5):
            continue
        x_val = a * b
        answer = a
        params = {"a": a, "b": b, "tpl": "reciprocal_expression",
                  "variant": variant or ("large_vals" if (a > 5 or b > 5) else "small_vals")}
        ph = param_hash(params)
        if ph in exclude_params:
            continue
        check = solve(Rational(1, a) * x - b, x)
        assert check and int(check[0]) == x_val
        assert Rational(x_val, b) == a
        ans = fmt_num(answer)
        dist = make_distractors(ans, [
            str(b),
            str(x_val),
            str(a * a),
            str(b * b),
        ])
        ctx = (f"Solve: (1/{a})x = {b} → x = {b} × {a} = {x_val}. "
               f"Then (1/{b})x = (1/{b}) × {x_val} = {answer}. "
               f"The question must ask: If \\(\\frac{{1}}{{{a}}}\\)x = {b}, "
               f"what is the value of \\(\\frac{{1}}{{{b}}}\\)x?")
        return _leq_result(1, params, ph, ans, None, dist, "mcq", ctx)
    raise RuntimeError("reciprocal_expression d1: could not generate unique params")


# ── d2 template functions ─────────────────────────────────────────────────────

def _d2_scale_simple(rng_obj, exclude_params, variant=None):
    """ax = b; find cx."""
    x = symbols("x")
    for _ in range(200):
        a = rng_obj.randint(2, 6)
        x_val = rng_obj.randint(2, 10)
        b = a * x_val
        c = rng_obj.choice([j for j in range(2, 20) if j != a])
        if variant == "small_c" and c >= 10:
            continue
        if variant == "large_c" and c < 10:
            continue
        expr_val = c * x_val
        if expr_val > 200:
            continue
        params = {"a": a, "b": b, "c": c, "tpl": "scale_simple",
                  "variant": variant or ("large_c" if c >= 10 else "small_c")}
        ph = param_hash(params)
        if ph in exclude_params:
            continue
        sol = solve(a * x - b, x)
        assert sol and sol[0] == x_val
        ans = fmt_num(expr_val)
        dist = make_distractors(ans, [
            str(x_val),
            str(b),
            str(b + c),
            str(x_val + c),
        ])
        ctx = (f"Equation: {a}x = {b}. Solve: x = {x_val}. "
               f"Then {c}x = {c} × {x_val} = {expr_val}. "
               f"The question must ask: If {a}x = {b}, what is the value of {c}x?")
        return _leq_result(2, params, ph, ans, None, dist, "mcq", ctx)
    raise RuntimeError("scale_simple d2: could not generate unique params")


def _d2_scale_compound(rng_obj, exclude_params, variant=None):
    """ax + b = c; find d*(ax+b)."""
    x = symbols("x")
    for _ in range(200):
        a = rng_obj.randint(2, 5)
        b = rng_obj.choice([-1, 1]) * rng_obj.randint(1, 10)
        if variant == "pos_b" and b < 0:
            continue
        if variant == "neg_b" and b > 0:
            continue
        x_val = rng_obj.randint(1, 8)
        c = a * x_val + b
        d = rng_obj.randint(2, 5)
        da = d * a
        db = d * b
        expr_val = d * c
        params = {"a": a, "b": b, "c": c, "d": d, "tpl": "scale_compound",
                  "variant": variant or ("neg_b" if b < 0 else "pos_b")}
        ph = param_hash(params)
        if ph in exclude_params:
            continue
        sol = solve(a * x + b - c, x)
        assert sol and sol[0] == x_val
        assert da * x_val + db == expr_val
        ans = fmt_num(expr_val)
        dist = make_distractors(ans, [
            str(da * x_val),
            str(a * x_val + db),
            str(c),
            str(c + d),
        ])
        ctx = (f"Equation: {a}x + {b} = {c}. Multiply both sides by {d}: "
               f"{da}x + {db} = {expr_val}. "
               f"The question must ask: If {a}x + {b} = {c}, what is the value of {da}x + {db}?")
        return _leq_result(2, params, ph, ans, None, dist, "mcq", ctx)
    raise RuntimeError("scale_compound d2: could not generate unique params")


def _d2_isolate_expression(rng_obj, exclude_params, variant=None):
    """k + a*(x − b) = c; find a*(x − b)."""
    x = symbols("x")
    for _ in range(200):
        a = rng_obj.randint(2, 6)
        b = rng_obj.randint(1, 8)
        k = rng_obj.choice([-1, 1]) * rng_obj.randint(1, 15)
        if variant == "pos_k" and k < 0:
            continue
        if variant == "neg_k" and k > 0:
            continue
        x_val = rng_obj.randint(b + 1, b + 12)
        inner = a * (x_val - b)
        c = k + inner
        expr_val = inner
        params = {"a": a, "b": b, "k": k, "c": c, "tpl": "isolate_expression",
                  "variant": variant or ("neg_k" if k < 0 else "pos_k")}
        ph = param_hash(params)
        if ph in exclude_params:
            continue
        sol = solve(k + a * (x - b) - c, x)
        assert sol and sol[0] == x_val
        ans = fmt_num(expr_val)
        dist = make_distractors(ans, [
            str(c),
            str(c + k),
            str(x_val),
            str(abs(k)),
        ])
        ctx = (f"Equation: {k} + {a}(x − {b}) = {c}. "
               f"Subtract {k} from both sides: {a}(x − {b}) = {c} − {k} = {expr_val}. "
               f"The question must ask: In the equation {k} + {a}(x − {b}) = {c}, "
               f"what is the value of {a}(x − {b})?")
        return _leq_result(2, params, ph, ans, None, dist, "mcq", ctx)
    raise RuntimeError("isolate_expression d2: could not generate unique params")


def _d2_fractional_common_factor(rng_obj, exclude_params, variant=None):
    """(1/a)(x+k) − (1/b)(x+k) = c; solve for x. MCQ or SPR."""
    x = symbols("x")
    for _ in range(200):
        a = rng_obj.randint(2, 5)
        b = rng_obj.randint(a + 1, a + 4)
        diff = b - a
        ab = a * b
        k = rng_obj.randint(1, 8)
        step = ab // _math.gcd(ab, diff)
        xk_mult = rng_obj.randint(1, 4)
        xk_val = step * xk_mult
        c_rat = Rational(xk_val * diff, ab)
        if c_rat.denominator != 1:
            continue
        c_int = int(c_rat)
        if c_int <= 0:
            continue
        x_val = xk_val - k
        if x_val <= 0:
            continue
        sub = variant or rng_obj.choice(["mcq_type", "spr_type"])
        qt = "mcq" if sub == "mcq_type" else "spr"
        params = {"a": a, "b": b, "k": k, "xk": xk_val, "c": c_int,
                  "tpl": "fractional_common_factor", "variant": sub}
        ph = param_hash(params)
        if ph in exclude_params:
            continue
        expr = Rational(1, a) * (x + k) - Rational(1, b) * (x + k) - c_int
        sol = solve(expr, x)
        assert sol and sol[0] == x_val
        ans = fmt_num(x_val)

        sm, sx = spr_bounds(ans) if qt == "spr" else (None, None)
        dist = make_distractors(ans, [
            str(xk_val),
            str(x_val + a),
            str(x_val + b),
            str(c_int * a),
        ]) if qt == "mcq" else []
        ctx = (f"Equation: (1/{a})(x + {k}) − (1/{b})(x + {k}) = {c_int}. "
               f"Factor out (x + {k}): (x + {k})(1/{a} − 1/{b}) = {c_int}. "
               f"Compute 1/{a} − 1/{b} = {diff}/{ab}. "
               f"So x + {k} = {c_int} × {ab}/{diff} = {xk_val}. "
               f"x = {xk_val} − {k} = {x_val}. "
               f"The question must ask: What is the value of x in the equation "
               f"\\(\\frac{{1}}{{{a}}}\\)(x + {k}) − \\(\\frac{{1}}{{{b}}}\\)(x + {k}) = {c_int}?")
        return _leq_result(2, params, ph, ans, (sm, sx), dist, qt, ctx)
    raise RuntimeError("fractional_common_factor d2: could not generate unique params")


# ── d3 template functions ─────────────────────────────────────────────────────

def _d3_expression_as_unit(rng_obj, exclude_params, variant=None):
    """p*(Ax−B) + q = r*(Ax−B) + s; find Ax−B. MCQ or SPR."""
    x = symbols("x")
    for _ in range(200):
        p = rng_obj.randint(3, 7)
        r = rng_obj.randint(1, p - 1)
        q = rng_obj.choice([-1, 1]) * rng_obj.randint(1, 15)
        s = rng_obj.choice([-1, 1]) * rng_obj.randint(1, 15)
        while s == q:
            s = rng_obj.choice([-1, 1]) * rng_obj.randint(1, 15)
        u_rat = Rational(s - q, p - r)
        if u_rat.denominator != 1:
            continue
        u_int = int(u_rat)
        A = rng_obj.randint(2, 5)
        B = rng_obj.choice([-1, 1]) * rng_obj.randint(1, 8)
        if (u_int + B) % A != 0:
            continue
        x_val = (u_int + B) // A
        sub = variant or rng_obj.choice(["mcq_type", "spr_type"])
        qt = "mcq" if sub == "mcq_type" else "spr"
        params = {"p": p, "q": q, "r": r, "s": s, "A": A, "B": B,
                  "tpl": "expression_as_unit", "variant": sub}
        ph = param_hash(params)
        if ph in exclude_params:
            continue
        expr_chk = p * (A * x - B) + q - (r * (A * x - B) + s)
        sol = solve(expr_chk, x)
        assert sol and sol[0] == x_val
        assert A * x_val - B == u_int
        ans = fmt_num(u_int)

        sm, sx = spr_bounds(ans) if qt == "spr" else (None, None)
        B_disp = f"+ {abs(B)}" if B < 0 else (f"− {B}" if B > 0 else "")
        dist = make_distractors(ans, [
            str(u_int + (p - r)),
            str(s - q),
            str(x_val),
            str(-u_int),
        ]) if qt == "mcq" else []
        ctx = (f"Let u = {A}x {B_disp}. Substituting: {p}u + {q} = {r}u + {s}. "
               f"Collect u: ({p}−{r})u = {s}−{q} → {p - r}u = {s - q} → u = {u_int}. "
               f"The question asks for the value of {A}x {B_disp} (= u), not x itself. "
               f"The question must ask: What is the value of {A}x {B_disp}? "
               f"Present the equation as: {p}({A}x {B_disp}) + {q} = {r}({A}x {B_disp}) + {s}.")
        return _leq_result(3, params, ph, ans, (sm, sx), dist, qt, ctx)
    raise RuntimeError("expression_as_unit d3: could not generate unique params")


def _d3_infinite_solutions_complex(rng_obj, exclude_params, variant=None):
    """(Ax+B)/C − s/D = r(x−E); find s for infinite solutions."""
    x = symbols("x")
    for _ in range(200):
        C = rng_obj.randint(2, 4)
        D = rng_obj.randint(2, 5)
        r = rng_obj.randint(1, 4)
        if variant == "small_r" and r > 2:
            continue
        if variant == "large_r" and r <= 2:
            continue
        E = rng_obj.randint(1, 8)
        B_num = rng_obj.randint(1, 6)
        B = B_num * C
        A = r * C
        s_val = D * (B_num + r * E)
        if s_val <= 0:
            continue
        params = {"A": A, "B": B, "C": C, "s": s_val, "D": D, "r": r, "E": E,
                  "tpl": "infinite_solutions_complex",
                  "variant": variant or ("large_r" if r > 2 else "small_r")}
        ph = param_hash(params)
        if ph in exclude_params:
            continue
        lhs_expr = Rational(A, C) * x + Rational(B, C) - Rational(s_val, D)
        rhs_expr = r * (x - E)
        diff_expr = sp.expand(lhs_expr - rhs_expr)
        assert diff_expr == 0, f"Not identity: {diff_expr}"
        ans = fmt_num(s_val)
        alt_wrong = D * (B_num - r * E)
        dist = make_distractors(ans, [
            str(s_val + D),
            str(s_val - D),
            str(alt_wrong) if alt_wrong != s_val else str(s_val + 2 * D),
            str(r * E),
        ])
        ctx = (f"Equation: ({A}x + {B})/{C} − s/{D} = {r}(x − {E}). "
               f"Simplify LHS: {r}x + {B_num} − s/{D}. RHS: {r}x − {r * E}. "
               f"Match x-coeff: {r} = {r} ✓. Match constants: "
               f"{B_num} − s/{D} = −{r * E} → s/{D} = {B_num + r * E} → s = {s_val}. "
               f"The question must ask: For what value of s does the equation "
               f"({A}x + {B})/{C} − s/{D} = {r}(x − {E}) have infinitely many solutions?")
        return _leq_result(3, params, ph, ans, None, dist, "mcq", ctx)
    raise RuntimeError("infinite_solutions_complex d3: could not generate unique params")


def _d3_no_solution(rng_obj, exclude_params, variant=None):
    """n(ax + b) = cx + d; find n for no solution."""
    x = symbols("x")
    for _ in range(200):
        a = rng_obj.randint(2, 4)
        b = rng_obj.randint(1, 10)
        n_val = rng_obj.randint(2, 5)
        if variant == "small_n" and n_val > 3:
            continue
        if variant == "large_n" and n_val <= 3:
            continue
        c = n_val * a
        nb = n_val * b
        d = nb + rng_obj.choice([1, 2, 3, -1, -2])
        while d == nb or d <= 0:
            d = nb + rng_obj.choice([1, 2, 3, -1, -2, 4, -3])
        params = {"a": a, "b": b, "c": c, "d": d, "tpl": "no_solution",
                  "variant": variant or ("large_n" if n_val > 3 else "small_n")}
        ph = param_hash(params)
        if ph in exclude_params:
            continue
        eqn = n_val * a * x + n_val * b - (c * x + d)
        sol = solve(eqn, x)
        assert len(sol) == 0, f"Expected no solution, got {sol}"
        ans = fmt_num(n_val)
        dist = make_distractors(ans, [
            fmt_num(Rational(d, b)),
            fmt_num(Rational(d, a)),
            str(a),
            str(c),
        ])
        ctx = (f"For n({a}x + {b}) = {c}x + {d} to have no solution: "
               f"expand LHS = {a}n·x + {b}n. Need x-terms to cancel: "
               f"{a}n = {c} → n = {n_val}. Check constants: {b}×{n_val} = {nb} ≠ {d} ✓. "
               f"The question must ask: For what value of n does the equation "
               f"n({a}x + {b}) = {c}x + {d} have no solution?")
        return _leq_result(3, params, ph, ans, None, dist, "mcq", ctx)
    raise RuntimeError("no_solution d3: could not generate unique params")


# ── Routing dicts ─────────────────────────────────────────────────────────────

_D1 = {
    "direct_solve_one_step":      {"fn": _d1_direct_solve_one_step,      "variants": ["small_coeff",   "large_coeff"]},
    "direct_solve_two_step":      {"fn": _d1_direct_solve_two_step,      "variants": ["pos_const",     "neg_const"]},
    "direct_solve_distribute":    {"fn": _d1_direct_solve_distribute,    "variants": ["small_outer",   "large_outer"]},
    "find_expression_given_x":    {"fn": _d1_find_expression_given_x,    "variants": ["small_n",       "large_n"]},
    "find_expression_shift":      {"fn": _d1_find_expression_shift,      "variants": ["small_b",       "large_b"]},
    "find_expression_divide":     {"fn": _d1_find_expression_divide,     "variants": ["small_k",       "large_k"]},
    "equivalent_equation":        {"fn": _d1_equivalent_equation,        "variants": ["small_rhs",     "large_rhs"]},
    "infinite_solutions_simple":  {"fn": _d1_infinite_solutions_simple,  "variants": ["small_product", "large_product"]},
    "reciprocal_expression":      {"fn": _d1_reciprocal_expression,      "variants": ["small_vals",    "large_vals"]},
}

_D2 = {
    "scale_simple":               {"fn": _d2_scale_simple,               "variants": ["small_c",   "large_c"]},
    "scale_compound":             {"fn": _d2_scale_compound,             "variants": ["pos_b",     "neg_b"]},
    "isolate_expression":         {"fn": _d2_isolate_expression,         "variants": ["pos_k",     "neg_k"]},
    "fractional_common_factor":   {"fn": _d2_fractional_common_factor,   "variants": ["mcq_type",  "spr_type"]},
}

_D3 = {
    "expression_as_unit":         {"fn": _d3_expression_as_unit,         "variants": ["mcq_type",  "spr_type"]},
    "infinite_solutions_complex": {"fn": _d3_infinite_solutions_complex, "variants": ["small_r",   "large_r"]},
    "no_solution":                {"fn": _d3_no_solution,                "variants": ["small_n",   "large_n"]},
}

_ROUTING = {1: _D1, 2: _D2, 3: _D3}

# _L1V_TEMPLATES auto-derived — single source of truth
_LEQ_TEMPLATES = {d: set(tpls.keys()) for d, tpls in _ROUTING.items()}


# ── Public metadata API ───────────────────────────────────────────────────────

def leq_variants(difficulty: int, template: str = None) -> dict:
    """
    Return variant metadata for linear_eq_one_var.

    If template is None: returns {template: [variants]} for all templates
    at the given difficulty level.

    If template is given: returns {"variants": [...]} for that template.
    """
    routing = _ROUTING.get(difficulty, {})
    if template is None:
        return {tpl: entry["variants"] for tpl, entry in routing.items()}
    if template not in routing:
        raise ValueError(
            f"Unknown template '{template}' for linear_eq_one_var d{difficulty}"
        )
    return {"variants": routing[template]["variants"]}


# ── Main generator ────────────────────────────────────────────────────────────

def gen_linear_eq_one_var(difficulty: int, rng_obj: random.Random, exclude_params: set,
                           force_template: str = None,
                           force_variant: str = None,
                           **_kwargs) -> dict:
    """
    Linear equations in one variable (L1V).

    Dispatches to a standalone per-template function via _D1/_D2/_D3 routing dicts.

    Args:
        force_template: pin to a specific template (e.g. "direct_solve_two_step").
                        If None, picks randomly from the difficulty level's pool.
        force_variant:  pin to a specific variant within the template
                        (e.g. "neg_const"). If None, no variant filter is applied.
    """
    clamped = min(max(difficulty, 1), 3)
    routing = _ROUTING.get(clamped, _D3)

    if force_template is not None:
        if force_template not in routing:
            valid = sorted(routing.keys())
            raise ValueError(
                f"--template '{force_template}' is not valid for "
                f"linear_eq_one_var d{clamped}. Valid: {valid}"
            )
        tpl = force_template
    else:
        tpl = rng_obj.choice(list(routing.keys()))

    entry = routing[tpl]
    return entry["fn"](rng_obj, exclude_params, variant=force_variant)
