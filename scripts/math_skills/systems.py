import random
from sympy import symbols, solve
from .core import (
    param_hash, spr_bounds, make_distractors,
)

# ── Scenario pools ────────────────────────────────────────────────────────────

_SLE_WP_EASY_SCENARIOS = [
    ("p", "h", "paperback books", "hardcover books", "a bookcase"),
    ("a", "g", "apples", "oranges", "a fruit bowl"),
    ("c", "t", "compact cars", "trucks", "a parking lot"),
    ("d", "s", "dogs", "cats", "an animal shelter"),
    ("r", "b", "red marbles", "blue marbles", "a jar"),
    ("f", "v", "fiction books", "nonfiction books", "a library cart"),
]
_SLE_PRICING_SCENARIOS = [
    ("sandwiches", "drinks"),
    ("loaves of bread", "packages of rolls"),
    ("adult tickets", "child tickets"),
    ("cups of coffee", "muffins"),
    ("kg of apples", "kg of oranges"),
]
_SLE_SPEED_SCENARIOS = [
    (60, 25, "highway", "local roads"),
    (70, 30, "expressway", "city streets"),
    (55, 20, "freeway", "neighborhood roads"),
    (65, 35, "main road", "side streets"),
]
_SLE_HARD_SCENARIOS = [
    ("jackets", "sweaters"),
    ("roses", "carnations"),
    ("cookies", "brownies"),
    ("novels", "textbooks"),
    ("scarves", "hats"),
]
_SLE_LENGTH_SCENARIOS = [
    ("centimeters", "wire"),
    ("inches", "rope"),
    ("feet", "cable"),
    ("meters", "string"),
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _si(m, b):
    """Format y = mx + b cleanly."""
    if m == 1:
        ms = ""
    elif m == -1:
        ms = "-"
    else:
        ms = str(m)
    if b > 0:
        return f"y = {ms}x + {b}"
    if b < 0:
        return f"y = {ms}x - {abs(b)}"
    return f"y = {ms}x"


def _eq(a, b, c):
    """Format ax + by = c, suppressing coefficient 1."""
    ax = "x" if a == 1 else f"{a}x"
    by = "y" if b == 1 else f"{b}y"
    return f"{ax} + {by} = {c}"


def _sle(d, params, ph, ans, distractors, ctx="", qt="mcq",
         spr_min=None, spr_max=None, diag=None):
    return {
        "skill": "systems_linear_eq",
        "difficulty": d,
        "questionType": qt,
        "params": params,
        "paramHash": ph,
        "verifiedAnswer": ans,
        "distractors": distractors,
        "sprMin": spr_min,
        "sprMax": spr_max,
        "scenarioTag": None,
        "diagramSpec": diag,
        "questionContext": (ctx or
            f"Solve the system of equations and find the stated quantity. The answer is {ans}."),
    }


# ── d1 template functions ─────────────────────────────────────────────────────

def _d1_direct_substitution(rng_obj, exclude_params, variant=None):
    """Direct substitution: x_given / y_expr / ratio_sub."""
    x, y = symbols("x y")
    sub = variant or rng_obj.choice(["x_given", "y_expr", "ratio_sub"])
    for _ in range(200):
        if sub == "x_given":
            xv = rng_obj.randint(1, 8)
            yv = rng_obj.randint(1, 8)
            S = xv + yv
            params = {"xv": xv, "S": S, "tpl": "direct_substitution", "variant": sub}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(yv)
            ctx = (f"The system is: x = {xv} and x + y = {S}. "
                   f"Substitute x = {xv}: {xv} + y = {S}, so y = {yv}. "
                   f"The question asks for the value of y. Answer: {yv}. "
                   f"Write the stem as one complete sentence: "
                   f"'If \\(x = {xv}\\) and \\(x + y = {S}\\), what is the value of \\(y\\)?'")
            return _sle(1, params, ph, ans,
                        make_distractors(ans, [str(xv), str(S), str(yv + 1), str(yv - 1)]),
                        ctx=ctx)

        elif sub == "y_expr":
            m = rng_obj.choice([2, 3])
            b = rng_obj.randint(1, 5)
            xv = rng_obj.randint(1, 6)
            yv = m * xv + b
            S = xv + yv
            params = {"m": m, "b": b, "S": S, "tpl": "direct_substitution", "variant": sub}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(xv)
            ctx = (f"The system is: y = {m}x + {b} and x + y = {S}. "
                   f"Substitute: x + ({m}x + {b}) = {S} → {m+1}x = {S - b} → x = {xv}. "
                   f"The question asks for the value of x. Answer: {xv}. "
                   f"Write the stem as one complete sentence: "
                   f"'If \\(y = {m}x + {b}\\) and \\(x + y = {S}\\), what is the value of \\(x\\)?'")
            return _sle(1, params, ph, ans,
                        make_distractors(ans, [str(yv), str(xv + 1), str(xv - 1), str(S - xv)]),
                        ctx=ctx)

        else:  # ratio_sub
            k = rng_obj.randint(2, 4)
            xv = rng_obj.randint(2, 6)
            yv = k * xv
            S = xv + yv
            params = {"k": k, "S": S, "tpl": "direct_substitution", "variant": sub}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(xv)
            ctx = (f"The system is: y = {k}x and x + y = {S}. "
                   f"Substitute: x + {k}x = {S} → {k+1}x = {S} → x = {xv}. "
                   f"The question asks for the value of x. Answer: {xv}. "
                   f"Write the stem as one complete sentence: "
                   f"'If \\(y = {k}x\\) and \\(x + y = {S}\\), what is the value of \\(x\\)?'")
            return _sle(1, params, ph, ans,
                        make_distractors(ans, [str(yv), str(S), str(xv + 1), str(k)]),
                        ctx=ctx)
    raise RuntimeError("direct_substitution d1: could not generate unique params")


def _d1_sum_difference(rng_obj, exclude_params, variant=None):
    """Sum/difference: given ax+by=c and either x-y or x+y, find the other."""
    sub = variant or rng_obj.choice(["sum_seq", "diff_direct"])
    for _ in range(200):
        xv = rng_obj.randint(2, 8)
        yv = rng_obj.randint(2, 8)
        S = xv + yv
        D = xv - yv
        a = rng_obj.randint(1, 3)
        b = rng_obj.randint(1, 3)
        c = a * xv + b * yv
        eq1 = _eq(a, b, c)

        if sub == "sum_seq":
            params = {"a": a, "b": b, "c": c, "D": D, "tpl": "sum_difference", "variant": sub}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(S)
            ctx = (f"The system is: {eq1} and x - y = {D}. "
                   f"Solve: x = {xv}, y = {yv}. Then x + y = {S}. "
                   f"The question MUST ask: what is the value of x + y? Answer: {S}. "
                   f"STEM FORMAT: Present the two equations as a system — each on its own line. "
                   f"Do NOT write them inline or join them with 'and'.")
            return _sle(1, params, ph, ans,
                        make_distractors(ans, [str(xv), str(yv), str(D), str(S + 1)]),
                        ctx=ctx)
        else:  # diff_direct
            if a == b:
                continue
            params = {"a": a, "b": b, "c": c, "S": S, "tpl": "sum_difference", "variant": sub}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(D)
            ctx = (f"The system is: {eq1} and x + y = {S}. "
                   f"Solve: x = {xv}, y = {yv}. Then x - y = {D}. "
                   f"The question MUST ask: what is the value of x - y? Answer: {D}. "
                   f"STEM FORMAT: Present the two equations as a system — each on its own line. "
                   f"Do NOT write them inline or join them with 'and'.")
            return _sle(1, params, ph, ans,
                        make_distractors(ans, [str(xv), str(yv), str(S), str(D + 1)]),
                        ctx=ctx)
    raise RuntimeError("sum_difference d1: could not generate unique params")


def _d1_graph_reading(rng_obj, exclude_params, variant=None):
    """Graph-reading: find the intersection point or just x-coordinate."""
    sub = variant or rng_obj.choice(["find_pair", "find_x"])
    for _ in range(200):
        m1 = rng_obj.choice([-2, -1, 1, 2])
        m2 = rng_obj.choice([-2, -1, 1, 2, 3])
        if m1 == m2:
            continue
        xv = rng_obj.randint(-3, 3) or 1
        yv = rng_obj.randint(-3, 3) or 2
        b1 = yv - m1 * xv
        b2 = yv - m2 * xv
        params = {"m1": m1, "b1": b1, "m2": m2, "b2": b2,
                  "xv": xv, "yv": yv, "tpl": "graph_reading", "variant": sub}
        ph = param_hash(params)
        if ph in exclude_params:
            continue
        fn1 = _si(m1, b1)
        fn2 = _si(m2, b2)
        diag = {
            "type": "coordinate_plane",
            "lines": [
                {"function": fn1, "label": fn1},
                {"function": fn2, "label": fn2},
            ],
            "highlight_point": [xv, yv],
        }
        if sub == "find_pair":
            ans = f"({xv}, {yv})"
            wrong = [
                f"({xv + 1}, {yv})",
                f"({xv}, {yv + 1})",
                f"({xv - 1}, {yv - 1})",
            ]
            ctx = (f"The graph shows two lines: {_si(m1, b1)} and {_si(m2, b2)}. "
                   f"They intersect at ({xv}, {yv}). "
                   f"The question asks: what is the solution (x, y)? Answer: ({xv}, {yv}).")
            return _sle(1, params, ph, ans, wrong, ctx=ctx, diag=diag)
        else:  # find_x
            ans = str(xv)
            ctx = (f"The graph shows two lines: {_si(m1, b1)} and {_si(m2, b2)}. "
                   f"They intersect at ({xv}, {yv}). "
                   f"The question asks: what is the value of x? Answer: {xv}.")
            return _sle(1, params, ph, ans,
                        make_distractors(ans, [str(yv), str(xv + 1), str(xv - 1), str(xv + 2)]),
                        ctx=ctx, diag=diag)
    raise RuntimeError("graph_reading d1: could not generate unique params")


def _d1_word_problem_easy(rng_obj, exclude_params, variant=None):
    """Word problem: which system of equations models the scenario?"""
    sub = variant or rng_obj.choice(["ratio_total", "additive_total"])
    for _ in range(200):
        sc = rng_obj.choice(_SLE_WP_EASY_SCENARIOS)
        vx, vy, item1, item2, container = sc

        if sub == "ratio_total":
            k = rng_obj.randint(2, 4)
            xv = rng_obj.randint(3, 8)
            yv = k * xv
            T = xv + yv
            params = {"k": k, "T": T, "item1": item1, "tpl": "word_problem_easy", "variant": sub}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            correct = f"{vx} + {vy} = {T}; {vy} = {k}{vx}"
            w1 = f"{vx} + {vy} = {T}; {vy} = {k+1}{vx}"
            w2 = f"{vx} - {vy} = {T}; {vy} = {k}{vx}"
            w3 = f"{vx} + {vy} = {T+1}; {vy} = {k}{vx}"
            if len({correct, w1, w2, w3}) < 4:
                continue
            ctx = (f"There are {item1} and {item2} in {container}. "
                   f"The total is {T}. There are {k} times as many {item2} as {item1}. "
                   f"Let {vx} = number of {item1}, {vy} = number of {item2}. "
                   f"The question asks which system of equations models this situation. "
                   f"The correct answer is: {correct}. "
                   f"The answer choices are provided separately — do NOT list them in the question stem.")
            return _sle(1, params, ph, correct, [w1, w2, w3], ctx=ctx)

        else:  # additive_total
            a = rng_obj.randint(2, 5)
            b = rng_obj.randint(2, 5)
            if a == b:
                continue
            xv = rng_obj.randint(2, 6)
            yv = rng_obj.randint(2, 6)
            T1 = a * xv + b * yv
            T2 = xv + yv
            params = {"a": a, "b": b, "T1": T1, "T2": T2, "item1": item1, "tpl": "word_problem_easy", "variant": sub}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            correct = f"{vx} + {vy} = {T2}; {a}{vx} + {b}{vy} = {T1}"
            w1 = f"{vx} + {vy} = {T2}; {a}{vx} + {b}{vy} = {T1 + a}"
            w2 = f"{vx} - {vy} = {T2}; {a}{vx} + {b}{vy} = {T1}"
            w3 = f"{vx} + {vy} = {T2 + 1}; {a}{vx} + {b}{vy} = {T1}"
            if len({correct, w1, w2, w3}) < 4:
                continue
            ctx = (f"There are {item1} and {item2} in {container}. "
                   f"Count equation: {vx} + {vy} = {T2}. Value equation: {a}{vx} + {b}{vy} = {T1}. "
                   f"The question asks which system of equations models this situation. "
                   f"The correct answer is: {correct}. "
                   f"The answer choices are provided separately — do NOT list them in the question stem.")
            return _sle(1, params, ph, correct, [w1, w2, w3], ctx=ctx)
    raise RuntimeError("word_problem_easy d1: could not generate unique params")


# ── d2 template functions ─────────────────────────────────────────────────────

def _d2_substitution_solve(rng_obj, exclude_params, variant=None):
    """Solve 2×2 system; ask for value of x or y."""
    x, y = symbols("x y")
    for _ in range(200):
        xv = rng_obj.randint(1, 8)
        yv = rng_obj.randint(1, 8)
        a = rng_obj.randint(2, 4)
        b = rng_obj.randint(2, 4)
        c1 = a * xv + yv
        c2 = xv + b * yv
        ask = rng_obj.choice(["x", "y"])
        if variant == "ask_x" and ask != "x":
            continue
        if variant == "ask_y" and ask != "y":
            continue
        sub = variant or f"ask_{ask}"
        params = {"a": a, "b": b, "c1": c1, "c2": c2, "ask": ask,
                  "tpl": "substitution_solve", "variant": sub}
        ph = param_hash(params)
        if ph in exclude_params:
            continue
        sol = solve([a * x + y - c1, x + b * y - c2], [x, y])
        if not isinstance(sol, dict):
            continue
        assert sol[x] == xv and sol[y] == yv
        ans = str(xv) if ask == "x" else str(yv)
        use_spr = rng_obj.random() < 0.30
        qt = "spr" if use_spr else "mcq"
        smin, smax = spr_bounds(ans) if use_spr else (None, None)
        other = str(yv if ask == "x" else xv)
        ctx = (f"The system is {a}x + y = {c1} and x + {b}y = {c2}. "
               f"Solve: x = {xv}, y = {yv}. "
               f"The question asks for the value of {ask}. Answer: {ans}. "
               f"STEM FORMAT: Present the two equations as a system — each on its own line. "
               f"Do NOT write them inline or join them with 'and'.")
        return _sle(2, params, ph, ans,
                    make_distractors(ans, [other, str(int(ans) + 1),
                                           str(int(ans) - 1), str(c1)]),
                    ctx=ctx, qt=qt, spr_min=smin, spr_max=smax)
    raise RuntimeError("substitution_solve d2: could not generate unique params")


def _d2_solve_find_expression(rng_obj, exclude_params, variant=None):
    """Solve system; evaluate px + qy. Variant: both_pos_vars or mixed_sign_vars."""
    x, y = symbols("x y")
    for _ in range(200):
        xv = rng_obj.choice([-1, 1]) * rng_obj.randint(1, 5)
        yv = rng_obj.choice([-1, 1]) * rng_obj.randint(1, 5)
        if variant == "both_pos_vars" and not (xv > 0 and yv > 0):
            continue
        if variant == "mixed_sign_vars" and xv > 0 and yv > 0:
            continue
        sub = variant or ("both_pos_vars" if xv > 0 and yv > 0 else "mixed_sign_vars")
        a1 = rng_obj.randint(1, 4)
        b1 = rng_obj.randint(1, 4)
        a2 = rng_obj.randint(1, 4)
        b2 = rng_obj.randint(1, 4)
        if a1 * b2 - a2 * b1 == 0:
            continue
        c1 = a1 * xv + b1 * yv
        c2 = a2 * xv + b2 * yv
        p = rng_obj.randint(2, 4)
        q = rng_obj.randint(2, 4)
        if (p == a1 and q == b1) or (p == a2 and q == b2):
            continue
        combo = p * xv + q * yv
        params = {"a1": a1, "b1": b1, "c1": c1, "a2": a2, "b2": b2, "c2": c2,
                  "p": p, "q": q, "tpl": "solve_find_expression", "variant": sub}
        ph = param_hash(params)
        if ph in exclude_params:
            continue
        sol = solve([a1 * x + b1 * y - c1, a2 * x + b2 * y - c2], [x, y])
        if not isinstance(sol, dict):
            continue
        assert sol[x] == xv and sol[y] == yv
        ans = str(combo)
        ctx = (f"Solve the system: {_eq(a1, b1, c1)} and {_eq(a2, b2, c2)}. "
               f"x = {xv}, y = {yv}. Compute {p}x + {q}y = {p}×{xv} + {q}×{yv} = {combo}. "
               f"The question MUST ask: what is the value of {p}x + {q}y? Answer: {combo}. "
               f"STEM FORMAT: Present the two equations as a system — each on its own line. "
               f"Do NOT write them inline or join them with 'and'.")
        return _sle(2, params, ph, ans,
                    make_distractors(ans, [str(combo + p), str(combo - q),
                                           str(p * xv), str(q * yv)]),
                    ctx=ctx)
    raise RuntimeError("solve_find_expression d2: could not generate unique params")


def _d2_no_solution_identify(rng_obj, exclude_params, variant=None):
    """Which of these four systems has no solution (parallel lines)?"""
    x, y = symbols("x y")
    for _ in range(200):
        a1 = rng_obj.randint(1, 4)
        b1 = rng_obj.randint(1, 4)
        c1 = rng_obj.randint(3, 15)
        k = rng_obj.randint(2, 4)
        if variant == "small_k" and k > 3:
            continue
        if variant == "large_k" and k <= 3:
            continue
        sub = variant or ("small_k" if k <= 3 else "large_k")
        shift = rng_obj.choice([-2, -1, 1, 2, 3])
        c2_par = k * c1 + shift
        correct = f"{_eq(a1, b1, c1)}; {_eq(k*a1, k*b1, c2_par)}"
        w1 = f"{_eq(a1, b1, c1)}; {_eq(k*a1, k*b1, k*c1)}"
        a3 = a1 + rng_obj.randint(1, 2)
        b3 = b1 + rng_obj.randint(1, 2)
        c3 = rng_obj.randint(3, 15)
        w2 = f"{_eq(a1, b1, c1)}; {_eq(a3, b3, c3)}"
        a4 = a1 + rng_obj.randint(1, 3)
        b4 = b1 - 1 if b1 > 1 else b1 + 2
        c4 = rng_obj.randint(3, 15)
        w3 = f"{_eq(a1, b1, c1)}; {_eq(a4, b4, c4)}"
        if len({correct, w1, w2, w3}) < 4:
            continue
        params = {"a1": a1, "b1": b1, "c1": c1, "k": k, "shift": shift,
                  "tpl": "no_solution_identify", "variant": sub}
        ph = param_hash(params)
        if ph in exclude_params:
            continue
        check = solve([a1 * x + b1 * y - c1, k * a1 * x + k * b1 * y - c2_par], [x, y])
        if check:
            continue
        ctx = (f"The question asks: which of the following systems of equations has no solution? "
               f"The correct answer is the system with parallel lines "
               f"(equal coefficient ratios, different constant ratio): {correct}. "
               f"Wrong choices: {w1} (same line — infinitely many solutions), "
               f"{w2} and {w3} (different slopes — one solution). "
               f"The answer choices are provided separately — do NOT list them in the question stem.")
        return _sle(2, params, ph, correct, [w1, w2, w3], ctx=ctx)
    raise RuntimeError("no_solution_identify d2: could not generate unique params")


def _d2_infinite_find_constant(rng_obj, exclude_params, variant=None):
    """Find constant k so system has infinitely many solutions."""
    x, y = symbols("x y")
    for _ in range(200):
        a1 = rng_obj.randint(1, 4)
        b1 = rng_obj.randint(1, 4)
        c1 = rng_obj.choice([-1, 1]) * rng_obj.randint(4, 20)
        if variant == "pos_constant" and c1 <= 0:
            continue
        if variant == "neg_constant" and c1 >= 0:
            continue
        sub = variant or ("pos_constant" if c1 > 0 else "neg_constant")
        k = rng_obj.randint(2, 5)
        a2, b2, c2 = k * a1, k * b1, k * c1
        params = {"a1": a1, "b1": b1, "c1": c1, "k_ans": k, "a2": a2, "c2": c2,
                  "tpl": "infinite_find_constant", "variant": sub}
        ph = param_hash(params)
        if ph in exclude_params:
            continue
        check_sol = solve([a1 * x + b1 * y - c1, a2 * x + b2 * y - c2], [x, y])
        is_infinite = bool(check_sol) and y not in check_sol
        if not is_infinite:
            continue
        ans = str(b2)
        ctx = (f"The system {_eq(a1, b1, c1)} and {a2}x + ky = {c2} has "
               f"infinitely many solutions because both equations define the same line "
               f"(multiply eq1 by {k}). "
               f"The question: '{_eq(a1, b1, c1)} and {a2}x + ky = {c2} has "
               f"infinitely many solutions. What is k?' Answer: k = {b2}. "
               f"STEM FORMAT: Present the two equations as a system — each on its own line. "
               f"Do NOT write them inline or join them with 'and'.")
        return _sle(2, params, ph, ans,
                    make_distractors(ans, [str(b2 + b1), str(b2 - b1),
                                           str(a2), str(b1)]),
                    ctx=ctx)
    raise RuntimeError("infinite_find_constant d2: could not generate unique params")


def _d2_word_problem_medium(rng_obj, exclude_params, variant=None):
    """Medium word problem: pricing / speed_time / vote_count."""
    x, y = symbols("x y")
    sub = variant or rng_obj.choice(["pricing", "speed_time", "vote_count"])
    for _ in range(200):
        if sub == "pricing":
            sc = rng_obj.choice(_SLE_PRICING_SCENARIOS)
            item1, item2 = sc
            p1 = rng_obj.randint(2, 8)
            p2 = rng_obj.randint(2, 8)
            n1a = rng_obj.randint(2, 5)
            n2a = rng_obj.randint(2, 5)
            n1b = rng_obj.randint(2, 5)
            n2b = rng_obj.randint(2, 5)
            if n1a * n2b - n1b * n2a == 0:
                continue
            T1 = n1a * p1 + n2a * p2
            T2 = n1b * p1 + n2b * p2
            params = {"n1a": n1a, "n2a": n2a, "T1": T1,
                      "n1b": n1b, "n2b": n2b, "T2": T2,
                      "item1": item1, "tpl": "word_problem_medium", "variant": sub}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            sol = solve([n1a * x + n2a * y - T1, n1b * x + n2b * y - T2], [x, y])
            if not isinstance(sol, dict):
                continue
            if sol[x] != p1 or sol[y] != p2:
                continue
            ans = str(p1)
            use_spr = rng_obj.random() < 0.30
            qt = "spr" if use_spr else "mcq"
            smin, smax = spr_bounds(ans) if use_spr else (None, None)
            ctx = (f"{n1a} {item1} and {n2a} {item2} cost {T1} dollars. "
                   f"{n1b} {item1} and {n2b} {item2} cost {T2} dollars. "
                   f"Solve: price of {item1} = {p1} dollars, price of {item2} = {p2} dollars. "
                   f"The question asks for the price, in dollars, of one {item1}. Answer: {p1}. "
                   f"IMPORTANT: write all monetary amounts as 'N dollars', never use the $ symbol.")
            return _sle(2, params, ph, ans,
                        make_distractors(ans, [str(p2), str(p1 + 1), str(p1 - 1), str(p1 + 2)]),
                        ctx=ctx, qt=qt, spr_min=smin, spr_max=smax)

        elif sub == "speed_time":
            sc = rng_obj.choice(_SLE_SPEED_SCENARIOS)
            spd1, spd2, rd1, rd2 = sc
            t1 = rng_obj.randint(1, 4)
            t2 = rng_obj.randint(1, 4)
            T = t1 + t2
            D = spd1 * t1 + spd2 * t2
            params = {"spd1": spd1, "spd2": spd2, "T": T, "D": D,
                      "rd1": rd1, "tpl": "word_problem_medium", "variant": sub}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            sol = solve([x + y - T, spd1 * x + spd2 * y - D], [x, y])
            if not isinstance(sol, dict):
                continue
            assert sol[x] == t1 and sol[y] == t2
            ans = str(t1)
            ctx = (f"A driver travels {D} miles in {T} hours. "
                   f"She drives {spd1} mph on the {rd1} and {spd2} mph on {rd2}. "
                   f"Let x = hours on {rd1}, y = hours on {rd2}. "
                   f"x + y = {T}; {spd1}x + {spd2}y = {D}. "
                   f"Solve: x = {t1}. "
                   f"The question asks for hours on the {rd1}. Answer: {t1}.")
            return _sle(2, params, ph, ans,
                        make_distractors(ans, [str(t2), str(t1 + 1), str(t1 - 1), str(T)]),
                        ctx=ctx)

        else:  # vote_count
            found = False
            for _v in range(50):
                N = rng_obj.randint(100, 500)
                M = rng_obj.randint(10, N // 2)
                if (N + M) % 2 == 0:
                    found = True
                    break
            if not found:
                continue
            winner = (N + M) // 2
            loser = N - winner
            params = {"N": N, "M": M, "tpl": "word_problem_medium", "variant": sub}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(winner)
            ctx = (f"Two candidates received {N} total votes. "
                   f"The winner received {M} more votes than the loser. "
                   f"x + y = {N}; x - y = {M}. "
                   f"Solve: winner = {winner}, loser = {loser}. "
                   f"The question asks for the winner's vote count. Answer: {winner}.")
            return _sle(2, params, ph, ans,
                        make_distractors(ans, [str(loser), str(winner + M),
                                               str(winner - 1), str(N)]),
                        ctx=ctx)
    raise RuntimeError("word_problem_medium d2: could not generate unique params")


# ── d3 template functions ─────────────────────────────────────────────────────

def _d3_no_solution_find_param(rng_obj, exclude_params, variant=None):
    """Find k so Ax + ky = C has no solution with the other equation."""
    x, y = symbols("x y")
    for _ in range(200):
        a1 = rng_obj.randint(1, 4)
        b1 = rng_obj.randint(1, 4)
        c1 = rng_obj.choice([-1, 1]) * rng_obj.randint(3, 20)
        scale = rng_obj.randint(2, 5)
        shift = rng_obj.choice([-3, -2, -1, 1, 2, 3])
        c2 = scale * c1 + shift
        a2 = scale * a1
        b2_ans = scale * b1
        sub = variant or rng_obj.choice(["mcq_type", "spr_type"])
        params = {"a1": a1, "b1": b1, "c1": c1, "a2": a2, "c2": c2,
                  "scale": scale, "b2_ans": b2_ans,
                  "tpl": "no_solution_find_param", "variant": sub}
        ph = param_hash(params)
        if ph in exclude_params:
            continue
        check = solve([a1 * x + b1 * y - c1, a2 * x + b2_ans * y - c2], [x, y])
        if check:
            continue
        ans = str(b2_ans)
        if sub == "mcq_type":
            qt = "mcq"
            smin, smax = None, None
        else:
            qt = "spr"
            smin, smax = spr_bounds(ans)
        ctx = (f"The system {_eq(a1, b1, c1)} and {a2}x + ky = {c2} has no solution "
               f"because the lines are parallel: a2/a1 = {a2}/{a1} = {scale}, and "
               f"for no solution k/b1 must also equal {scale}, so k = {scale}×{b1} = {b2_ans}. "
               f"But c2/c1 = {c2}/{c1} ≠ {scale}, confirming no solution. "
               f"The question: '{_eq(a1, b1, c1)} and {a2}x + ky = {c2} has no solution. "
               f"What is k?' Answer: k = {b2_ans}. "
               f"STEM FORMAT: Present the two equations as a system — each on its own line. "
               f"Do NOT write them inline or join them with 'and'.")
        return _sle(3, params, ph, ans,
                    make_distractors(ans, [str(b2_ans + b1), str(b2_ans - b1),
                                           str(a2), str(b1)]),
                    ctx=ctx, qt=qt, spr_min=smin, spr_max=smax)
    raise RuntimeError("no_solution_find_param d3: could not generate unique params")


def _d3_word_problem_hard(rng_obj, exclude_params, variant=None):
    """Hard word problem: total_and_multiple / two_prices / length_split."""
    x, y = symbols("x y")
    sub = variant or rng_obj.choice(["total_and_multiple", "two_prices", "length_split"])
    for _ in range(200):
        if sub == "total_and_multiple":
            sc = rng_obj.choice(_SLE_HARD_SCENARIOS)
            item1, item2 = sc
            k = rng_obj.randint(2, 4)
            r = rng_obj.randint(1, 5)
            yv = rng_obj.randint(4, 12)
            xv = k * yv + r
            T = xv + yv
            params = {"k": k, "r": r, "T": T, "item1": item1,
                      "tpl": "word_problem_hard", "variant": sub}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(xv)
            smin, smax = spr_bounds(ans)
            ctx = (f"A store has {item1} and {item2}. Total = {T}. "
                   f"There are {k} times as many {item1} as {item2}, plus {r} more. "
                   f"x = {item1}, y = {item2}: x + y = {T}; x = {k}y + {r}. "
                   f"Solve: y = {yv}, x = {xv}. "
                   f"The question asks for the number of {item1}. Answer: {xv}.")
            return _sle(3, params, ph, ans, [],
                        ctx=ctx, qt="spr", spr_min=smin, spr_max=smax)

        elif sub == "two_prices":
            sc = rng_obj.choice(_SLE_PRICING_SCENARIOS)
            item1, item2 = sc
            p1 = rng_obj.randint(3, 12)
            p2 = rng_obj.randint(3, 12)
            if p1 == p2:
                continue
            n1a = rng_obj.randint(2, 6)
            n2a = rng_obj.randint(2, 6)
            n1b = rng_obj.randint(2, 6)
            n2b = rng_obj.randint(2, 6)
            if n1a * n2b - n1b * n2a == 0:
                continue
            T1 = n1a * p1 + n2a * p2
            T2 = n1b * p1 + n2b * p2
            cc1 = rng_obj.randint(1, 3)
            cc2 = rng_obj.randint(1, 3)
            combo_val = cc1 * p1 + cc2 * p2
            params = {"n1a": n1a, "n2a": n2a, "T1": T1,
                      "n1b": n1b, "n2b": n2b, "T2": T2,
                      "cc1": cc1, "cc2": cc2,
                      "item1": item1, "tpl": "word_problem_hard", "variant": sub}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            sol = solve([n1a * x + n2a * y - T1, n1b * x + n2b * y - T2], [x, y])
            if not isinstance(sol, dict):
                continue
            if sol[x] != p1 or sol[y] != p2:
                continue
            ans = str(combo_val)
            ctx = (f"{n1a} {item1} and {n2a} {item2} cost {T1} dollars. "
                   f"{n1b} {item1} and {n2b} {item2} cost {T2} dollars. "
                   f"Solve: {item1} costs {p1} dollars, {item2} costs {p2} dollars. "
                   f"Find cost of {cc1} {item1} and {cc2} {item2}: "
                   f"{cc1}×{p1} + {cc2}×{p2} = {combo_val}. "
                   f"The question asks for the cost, in dollars, of {cc1} {item1} and {cc2} {item2}. "
                   f"Answer: {combo_val}. "
                   f"IMPORTANT: write all monetary amounts as 'N dollars', never use the $ symbol.")
            return _sle(3, params, ph, ans,
                        make_distractors(ans, [str(combo_val + cc1), str(combo_val - cc2),
                                               str(cc1 * p1), str(cc2 * p2)]),
                        ctx=ctx)

        else:  # length_split
            sc = rng_obj.choice(_SLE_LENGTH_SCENARIOS)
            unit, material = sc
            total = rng_obj.randint(20, 60)
            diff = rng_obj.choice(list(range(2, total // 3, 2)))
            if (total + diff) % 2 != 0:
                continue
            longer = (total + diff) // 2
            shorter = total - longer
            params = {"total": total, "diff": diff,
                      "unit": unit, "material": material,
                      "tpl": "word_problem_hard", "variant": sub}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(longer)
            smin, smax = spr_bounds(ans)
            ctx = (f"A piece of {material} {total} {unit} long is cut into two pieces. "
                   f"The longer piece is {diff} {unit} longer than the shorter piece. "
                   f"x + y = {total}; x - y = {diff}. "
                   f"Solve: x = {longer}, y = {shorter}. "
                   f"The question asks for the length of the longer piece. Answer: {longer}.")
            return _sle(3, params, ph, ans, [],
                        ctx=ctx, qt="spr", spr_min=smin, spr_max=smax)
    raise RuntimeError("word_problem_hard d3: could not generate unique params")


def _d3_linear_combination_trick(rng_obj, exclude_params, variant=None):
    """Find px+qy directly by combining equations; no need to solve individually."""
    x, y = symbols("x y")
    _R_TO_VARIANT = {(1, 1): "add_both", (1, -1): "subtract_eq2", (2, 1): "scale_add"}
    if variant == "add_both":
        r_choices = [(1, 1)]
    elif variant == "subtract_eq2":
        r_choices = [(1, -1)]
    elif variant == "scale_add":
        r_choices = [(2, 1)]
    else:
        r_choices = [(1, 1), (1, -1), (2, 1)]
    for _ in range(200):
        r1, r2 = rng_obj.choice(r_choices)
        xv = rng_obj.choice([-1, 1]) * rng_obj.randint(1, 8)
        yv = rng_obj.choice([-1, 1]) * rng_obj.randint(1, 8)
        a1 = rng_obj.randint(1, 4)
        b1 = rng_obj.randint(1, 4)
        a2 = rng_obj.randint(1, 4)
        b2 = rng_obj.randint(1, 4)
        if a1 * b2 - a2 * b1 == 0:
            continue
        c1 = a1 * xv + b1 * yv
        c2 = a2 * xv + b2 * yv
        px = r1 * a1 + r2 * a2
        qy = r1 * b1 + r2 * b2
        if px <= 0 or qy <= 0:
            continue
        if (px == a1 and qy == b1) or (px == a2 and qy == b2):
            continue
        target = r1 * c1 + r2 * c2
        params = {"a1": a1, "b1": b1, "c1": c1, "a2": a2, "b2": b2, "c2": c2,
                  "r1": r1, "r2": r2, "px": px, "qy": qy,
                  "tpl": "linear_combination_trick",
                  "variant": variant or _R_TO_VARIANT[(r1, r2)]}
        ph = param_hash(params)
        if ph in exclude_params:
            continue
        sol = solve([a1 * x + b1 * y - c1, a2 * x + b2 * y - c2], [x, y])
        if not isinstance(sol, dict):
            continue
        assert sol[x] == xv and sol[y] == yv
        ans = str(target)
        op = "+" if r2 > 0 else "-"
        ctx = (f"The system is: {_eq(a1, b1, c1)} and {_eq(a2, b2, c2)}. "
               f"Add {r1}×eq1 {op} {abs(r2)}×eq2 to get {px}x + {qy}y = {target}. "
               f"The question MUST ask: what is the value of {px}x + {qy}y? "
               f"Answer: {target}. "
               f"(Alternatively: x = {xv}, y = {yv}, then {px}×{xv} + {qy}×{yv} = {target}.) "
               f"STEM FORMAT: Present the two equations as a system — each on its own line. "
               f"Do NOT write them inline or join them with 'and'.")
        return _sle(3, params, ph, ans,
                    make_distractors(ans, [str(target + px), str(target - qy),
                                           str(r1 * c1), str(r2 * c2)]),
                    ctx=ctx)
    raise RuntimeError("linear_combination_trick d3: could not generate unique params")


def _d3_solve_find_xy_product(rng_obj, exclude_params, variant=None):
    """Solve system; find xy. Variant: pos_product or neg_product."""
    x, y = symbols("x y")
    for _ in range(200):
        xv = rng_obj.choice([-1, 1]) * rng_obj.randint(1, 8)
        yv = rng_obj.choice([-1, 1]) * rng_obj.randint(1, 8)
        if variant == "pos_product" and xv * yv <= 0:
            continue
        if variant == "neg_product" and xv * yv >= 0:
            continue
        sub = variant or ("pos_product" if xv * yv > 0 else "neg_product")
        a1 = rng_obj.randint(2, 5)
        b1 = rng_obj.randint(2, 5)
        a2 = rng_obj.randint(2, 5)
        b2 = rng_obj.randint(2, 5)
        if a1 * b2 - a2 * b1 == 0:
            continue
        c1 = a1 * xv + b1 * yv
        c2 = a2 * xv + b2 * yv
        product = xv * yv
        params = {"a1": a1, "b1": b1, "c1": c1, "a2": a2, "b2": b2, "c2": c2,
                  "tpl": "solve_find_xy_product", "variant": sub}
        ph = param_hash(params)
        if ph in exclude_params:
            continue
        sol = solve([a1 * x + b1 * y - c1, a2 * x + b2 * y - c2], [x, y])
        if not isinstance(sol, dict):
            continue
        assert sol[x] == xv and sol[y] == yv
        ans = str(product)
        ctx = (f"Solve the system: {_eq(a1, b1, c1)} and {_eq(a2, b2, c2)}. "
               f"x = {xv}, y = {yv}. Compute xy = {xv}×{yv} = {product}. "
               f"The question MUST ask: what is the value of xy? Answer: {product}. "
               f"STEM FORMAT: Present the two equations as a system — each on its own line. "
               f"Do NOT write them inline or join them with 'and'.")
        return _sle(3, params, ph, ans,
                    make_distractors(ans, [str(product + xv), str(product - yv),
                                           str(xv + yv), str(xv - yv)]),
                    ctx=ctx)
    raise RuntimeError("solve_find_xy_product d3: could not generate unique params")


# ── Routing dicts ─────────────────────────────────────────────────────────────

_D1 = {
    "direct_substitution": {"fn": _d1_direct_substitution, "variants": ["x_given", "y_expr", "ratio_sub"]},
    "sum_difference":       {"fn": _d1_sum_difference,      "variants": ["sum_seq", "diff_direct"]},
    "graph_reading":        {"fn": _d1_graph_reading,        "variants": ["find_pair", "find_x"]},
    "word_problem_easy":    {"fn": _d1_word_problem_easy,    "variants": ["ratio_total", "additive_total"]},
}

_D2 = {
    "substitution_solve":     {"fn": _d2_substitution_solve,     "variants": ["ask_x", "ask_y"]},
    "solve_find_expression":  {"fn": _d2_solve_find_expression,  "variants": ["both_pos_vars", "mixed_sign_vars"]},
    "no_solution_identify":   {"fn": _d2_no_solution_identify,   "variants": ["small_k", "large_k"]},
    "infinite_find_constant": {"fn": _d2_infinite_find_constant, "variants": ["pos_constant", "neg_constant"]},
    "word_problem_medium":    {"fn": _d2_word_problem_medium,    "variants": ["pricing", "speed_time", "vote_count"]},
}

_D3 = {
    "no_solution_find_param":    {"fn": _d3_no_solution_find_param,    "variants": ["mcq_type", "spr_type"]},
    "word_problem_hard":         {"fn": _d3_word_problem_hard,         "variants": ["total_and_multiple", "two_prices", "length_split"]},
    "linear_combination_trick":  {"fn": _d3_linear_combination_trick,  "variants": ["add_both", "subtract_eq2", "scale_add"]},
    "solve_find_xy_product":     {"fn": _d3_solve_find_xy_product,     "variants": ["pos_product", "neg_product"]},
}

_ROUTING = {1: _D1, 2: _D2, 3: _D3}

# _SLE_TEMPLATES auto-derived — single source of truth
_SLE_TEMPLATES = {d: set(tpls.keys()) for d, tpls in _ROUTING.items()}


# ── Public metadata API ───────────────────────────────────────────────────────

def sle_variants(difficulty: int, template: str = None) -> dict:
    """
    Return variant metadata for systems_linear_eq.

    If template is None: returns {template: [variants]} for all templates
    at the given difficulty level.

    If template is given: returns {"variants": [...]} for that template.
    """
    routing = _ROUTING.get(difficulty, {})
    if template is None:
        return {tpl: entry["variants"] for tpl, entry in routing.items()}
    if template not in routing:
        raise ValueError(
            f"Unknown template '{template}' for systems_linear_eq d{difficulty}"
        )
    return {"variants": routing[template]["variants"]}


# ── Main generator ────────────────────────────────────────────────────────────

def gen_systems_linear_eq(difficulty: int, rng_obj: random.Random,
                          exclude_params: set,
                          force_template: str = None,
                          force_variant: str = None,
                          **_kwargs) -> dict:
    """
    Systems of linear equations generator (SLE).

    Dispatches to a standalone per-template function via _D1/_D2/_D3 routing dicts.

    Args:
        force_template: pin to a specific template (e.g. "graph_reading").
                        If None, picks randomly from the difficulty level's pool.
        force_variant:  pin to a specific variant within the template
                        (e.g. "find_x", "pricing"). If None, no variant filter applied.
    """
    clamped = min(max(difficulty, 1), 3)
    routing = _ROUTING.get(clamped, _D3)

    if force_template is not None:
        if force_template not in routing:
            valid = sorted(routing.keys())
            raise ValueError(
                f"--template '{force_template}' is not valid for "
                f"systems_linear_eq d{clamped}. Valid: {valid}"
            )
        tpl = force_template
    else:
        tpl = rng_obj.choice(list(routing.keys()))

    entry = routing[tpl]
    return entry["fn"](rng_obj, exclude_params, variant=force_variant)
