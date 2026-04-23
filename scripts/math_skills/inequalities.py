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

def _lin_result(d, params, ph, ans, spr, distractors, qt="mcq", ctx=""):
    sm, sx = spr if spr else (None, None)
    return {"skill": "linear_inequalities", "difficulty": d, "questionType": qt,
            "params": params, "paramHash": ph, "verifiedAnswer": ans,
            "distractors": distractors, "sprMin": sm, "sprMax": sx,
            "scenarioTag": None, "diagramSpec": None,
            "questionContext": ctx or f"Solve the linear inequality. The answer is {ans}."}


# ── d1 template functions ─────────────────────────────────────────────────────

def _d1_one_var_word_bound(rng_obj, exclude_params, variant=None):
    """One-variable word-bound: min/max additional or packs SPR."""
    v = variant or rng_obj.choice(["min_additional", "max_additional", "packs_spr"])
    for _ in range(200):
        if v == "packs_spr":
            need = rng_obj.randint(30, 200)
            pack_size = rng_obj.randint(4, 14)
            if need % pack_size == 0:
                need += rng_obj.randint(1, pack_size - 1)
            answer = _math.ceil(need / pack_size)
            assert answer * pack_size >= need and (answer - 1) * pack_size < need
            item, container = rng_obj.choice([
                ("pens", "box"), ("sandwiches", "tray"),
                ("tennis balls", "can"), ("test tubes", "rack"),
                ("flyers", "bundle"), ("screws", "pack"),
            ])
            params = {"need": need, "pack": pack_size, "scenario": container,
                      "tpl": "one_var_word_bound", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = fmt_num(answer)
            ctx = (f"Need at least {need} {item}s; they are sold in {container}s of {pack_size}. "
                   f"{need} / {pack_size} = {need/pack_size:.3f}; must round UP because "
                   f"partial {container}s cannot be ordered → minimum {answer} {container}s. "
                   f"The question must ask the minimum number of {container}s that must be ordered. "
                   f"Verified answer: {answer}.")
            return _lin_result(1, params, ph, ans, spr_bounds(ans), [], "spr", ctx)
        else:
            goal = rng_obj.randint(30, 250)
            current = rng_obj.randint(5, goal - 5)
            answer = goal - current
            if v == "min_additional":
                domain, quantity = rng_obj.choice([
                    ("charity fundraiser", "dollars raised"),
                    ("community garden", "volunteer hours logged"),
                    ("school reading program", "pages read"),
                    ("athletic training plan", "miles logged"),
                    ("science fair project", "data points collected"),
                ])
                threshold_word = "fundraising goal" if "fundraiser" in domain else "target"
            else:
                domain, quantity = rng_obj.choice([
                    ("storage facility", "boxes stored"),
                    ("event venue", "guests registered"),
                    ("parking lot", "vehicles parked"),
                    ("school cafeteria", "students seated"),
                    ("supply room", "items on shelves"),
                ])
                threshold_word = "capacity"
            params = {"goal": goal, "current": current, "scenario": domain,
                      "tpl": "one_var_word_bound", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = fmt_num(answer)
            dist = make_distractors(ans, [
                str(current), str(goal), str(goal + current),
            ])
            dir_word = "minimum additional" if v == "min_additional" else "maximum additional"
            ctx = (f"Context: {domain}. Current {quantity} = {current}; {threshold_word} = {goal}. "
                   f"{dir_word} = {goal} − {current} = {answer}. "
                   f"The question must ask for the {dir_word} {quantity} "
                   f"{'needed to reach the' if v == 'min_additional' else 'allowed under the'} "
                   f"{threshold_word}. Verified answer: {answer}.")
            return _lin_result(1, params, ph, ans, None, dist, "mcq", ctx)
    raise RuntimeError("one_var_word_bound d1: could not generate unique params")


def _d1_compound_range(rng_obj, exclude_params, variant=None):
    """Compound range: direct or scaled."""
    v = variant or rng_obj.choice(["direct", "scaled"])
    for _ in range(200):
        low = rng_obj.randint(5, 30)
        high = rng_obj.randint(low + 5, low + 30)
        var_letter = rng_obj.choice(["v", "h", "t", "s", "n", "w", "p"])
        if v == "direct":
            ans_str = f"{low} ≤ {var_letter} ≤ {high}"
            dist_pool = [
                f"{var_letter} ≥ {low + high}",
                f"{var_letter} ≤ {low}",
                f"{var_letter} ≥ {high}",
                f"0 ≤ {var_letter} ≤ {low}",
            ]
            params = {"low": low, "high": high, "var": var_letter, "tpl": "compound_range",
                      "variant": v}
        else:
            rate = rng_obj.choice([2, 3, 4, 5, 6, 8, 10, 12])
            ans_str = f"{low} ≤ {rate}{var_letter} ≤ {high}"
            dist_pool = [
                f"({low})({rate}) ≤ {var_letter} ≤ ({high})({rate})",
                f"{low} + {rate} ≤ {var_letter} ≤ {high} + {rate}",
                f"{low}/{rate} ≤ {var_letter} ≤ {high}/{rate}",
            ]
            params = {"low": low, "high": high, "rate": rate, "var": var_letter,
                      "tpl": "compound_range", "variant": v}
        ph = param_hash(params)
        if ph in exclude_params:
            continue
        dist = make_distractors(ans_str, dist_pool)
        if v == "scaled":
            ctx = (f"A quantity is measured to be between {low} and {high}. "
                   f"Variable {var_letter} is defined by the relationship: quantity = {rate}{var_letter}. "
                   f"Correct inequality: {ans_str}. "
                   f"The question stem MUST define {var_letter} using the phrase "
                   f"'the quantity equals {rate} times {var_letter}' or equivalent — "
                   f"NOT 'w equals {rate} times the quantity' (that would be the inverse). "
                   f"The question must ask: Which inequality represents the possible values of {var_letter}?")
        else:
            ctx = (f"Compound range direct. Variable {var_letter} between {low} and {high}. "
                   f"Correct inequality: {ans_str}. "
                   f"The question must ask: Which inequality represents the possible values of {var_letter}?")
        return _lin_result(1, params, ph, ans_str, None, dist, "mcq", ctx)
    raise RuntimeError("compound_range d1: could not generate unique params")


def _d1_write_inequality_easy(rng_obj, exclude_params, variant=None):
    """Write-inequality easy: total_cap / rate_constraint / budget / fee_plus_hourly."""
    v = variant or rng_obj.choice(["total_cap", "rate_constraint", "budget", "fee_plus_hourly"])
    for _ in range(200):
        if v == "total_cap":
            N = rng_obj.randint(15, 80)
            v1 = rng_obj.choice(["r", "a", "c"])
            v2 = rng_obj.choice([vv for vv in ["l", "b", "d", "m"] if vv != v1])
            ans_str = f"{v1} + {v2} ≤ {N}"
            dist_pool = [
                f"{v1} + {v2} ≥ {N}",
                f"{v1} − {v2} ≤ {N}",
                f"{v1} − {v2} ≥ {N}",
                f"{v1} + {v2} = {N}",
            ]
            params = {"N": N, "v1": v1, "v2": v2, "tpl": "write_inequality_easy", "variant": v}
        elif v == "rate_constraint":
            r1 = rng_obj.randint(2, 6)
            r2 = rng_obj.randint(r1 + 1, r1 + 6)
            N = rng_obj.randint(r1 * 5 + r2 * 5, 200)
            ans_str = f"{r1}a + {r2}b < {N}"
            dist_pool = [
                f"{r1}a + {r2}b > {N}",
                f"{r2}a + {r1}b < {N}",
                f"{r2}a + {r1}b > {N}",
                f"{r1}a − {r2}b < {N}",
            ]
            params = {"r1": r1, "r2": r2, "N": N, "tpl": "write_inequality_easy", "variant": v}
        elif v == "budget":
            p1 = rng_obj.randint(3, 9)
            p2 = rng_obj.randint(2, 12)
            while p2 == p1:
                p2 = rng_obj.randint(2, 12)
            B = rng_obj.choice([20, 25, 30, 40, 50, 60, 80, 100])
            ans_str = f"{p1}n + {p2}p ≤ {B}"
            dist_pool = [
                f"{p1}n + {p2}p ≥ {B}",
                f"{p2}n + {p1}p ≤ {B}",
                f"{p2}n + {p1}p ≥ {B}",
                f"{p1}n − {p2}p ≤ {B}",
            ]
            params = {"p1": p1, "p2": p2, "B": B, "tpl": "write_inequality_easy", "variant": v}
        else:  # fee_plus_hourly
            F = rng_obj.choice([5, 6, 8, 10, 12, 15])
            r = rng_obj.choice([3, 4, 5, 6, 7, 8])
            B = rng_obj.randint(F + r * 3, F + r * 10)
            ans_str = f"{F} + {r}h ≤ {B}"
            dist_pool = [
                f"{r}h ≤ {B}",
                f"{F}h ≤ {B}",
                f"{r} + {F}h ≤ {B}",
                f"{F} + {r}h ≥ {B}",
            ]
            params = {"F": F, "r": r, "B": B, "tpl": "write_inequality_easy", "variant": v}
        ph = param_hash(params)
        if ph in exclude_params:
            continue
        dist = make_distractors(ans_str, dist_pool)
        ctx = (f"Write-inequality easy ({v}). Correct: {ans_str}. "
               f"The question must ask: Which inequality represents this situation?")
        return _lin_result(1, params, ph, ans_str, None, dist, "mcq", ctx)
    raise RuntimeError("write_inequality_easy d1: could not generate unique params")


def _d1_system_quadrant(rng_obj, exclude_params, variant=None):
    """System-quadrant: which quadrant does the given point lie in?"""
    # Variants encode quadrant: q1 (x>0,y>0), q2 (x<0,y>0), q3 (x<0,y<0), q4 (x>0,y<0)
    for _ in range(200):
        x_sign = rng_obj.choice([1, -1])
        y_sign = rng_obj.choice([1, -1])
        if variant == "q1" and not (x_sign > 0 and y_sign > 0):
            continue
        if variant == "q2" and not (x_sign < 0 and y_sign > 0):
            continue
        if variant == "q3" and not (x_sign < 0 and y_sign < 0):
            continue
        if variant == "q4" and not (x_sign > 0 and y_sign < 0):
            continue
        x_val = x_sign * rng_obj.randint(2, 12)
        y_val = y_sign * rng_obj.randint(2, 12)

        def _sys(xs, ys):
            return f"x {'>' if xs > 0 else '<'} 0; y {'>' if ys > 0 else '<'} 0"

        ans_str = _sys(x_sign, y_sign)
        dist_pool = [
            _sys(x_sign, -y_sign),
            _sys(-x_sign, y_sign),
            _sys(-x_sign, -y_sign),
        ]
        sub = variant or {(1, 1): "q1", (-1, 1): "q2", (-1, -1): "q3", (1, -1): "q4"}[(x_sign, y_sign)]
        params = {"x": x_val, "y": y_val, "tpl": "system_quadrant", "variant": sub}
        ph = param_hash(params)
        if ph in exclude_params:
            continue
        dist = make_distractors(ans_str, dist_pool)
        ctx = (f"Point ({x_val}, {y_val}): x is {'positive' if x_sign > 0 else 'negative'}, "
               f"y is {'positive' if y_sign > 0 else 'negative'}. Correct system: {ans_str}. "
               f"The question must ask: The point ({x_val}, {y_val}) is a solution to which of "
               f"the following systems of inequalities?")
        return _lin_result(1, params, ph, ans_str, None, dist, "mcq", ctx)
    raise RuntimeError("system_quadrant d1: could not generate unique params")


# ── d2 template functions ─────────────────────────────────────────────────────

def _d2_compound_range_scaled(rng_obj, exclude_params, variant=None):
    """Compound range scaled: scale_units or threshold_select."""
    v = variant or rng_obj.choice(["scale_units", "threshold_select"])
    for _ in range(200):
        if v == "scale_units":
            low_per = rng_obj.randint(10, 60)
            high_per = rng_obj.randint(low_per + 10, low_per + 40)
            n = rng_obj.randint(5, 20)
            ans_str = f"({low_per})({n}) ≤ p ≤ ({high_per})({n})"
            dist_pool = [
                f"{low_per} + {n} ≤ p ≤ {high_per} + {n}",
                f"{low_per} ≤ {n} + p ≤ {high_per}",
                f"{low_per} ≤ {n}p ≤ {high_per}",
            ]
            params = {"low": low_per, "high": high_per, "n": n, "tpl": "compound_range_scaled",
                      "variant": v}
        else:
            threshold = rng_obj.randint(20, 50)
            low_c = threshold + rng_obj.randint(2, 8)
            high_c = low_c + rng_obj.randint(6, 20)
            ans_str = f"{low_c} < l < {high_c}"
            d_low = threshold - rng_obj.randint(10, 20)
            d2_low = max(2, threshold - rng_obj.randint(20, 30))
            d3_low = max(2, threshold - rng_obj.randint(15, 25))
            dist_pool = [
                f"{d_low} < l < {threshold}",
                f"{d2_low} < l < {threshold - 1}",
                f"{d3_low} < l < {threshold - 2}",
            ]
            params = {"t": threshold, "lc": low_c, "hc": high_c, "tpl": "compound_range_scaled",
                      "variant": v}
        ph = param_hash(params)
        if ph in exclude_params:
            continue
        dist = make_distractors(ans_str, dist_pool)
        ctx = (f"Compound-range medium ({v}). Correct: {ans_str}. "
               f"The question must ask which inequality represents the scenario.")
        return _lin_result(2, params, ph, ans_str, None, dist, "mcq", ctx)
    raise RuntimeError("compound_range_scaled d2: could not generate unique params")


def _d2_write_inequality_medium(rng_obj, exclude_params, variant=None):
    """Write-inequality medium: perimeter / system_two / capacity_minus."""
    v = variant or rng_obj.choice(["perimeter", "system_two", "capacity_minus"])
    for _ in range(200):
        if v == "perimeter":
            w = rng_obj.randint(5, 20)
            P_cap = rng_obj.randint(2 * w + 10, 2 * w + 80)
            ans_str = f"2x + {2 * w} ≤ {P_cap}"
            dist_pool = [
                f"2x + {2 * w} ≥ {P_cap}",
                f"2x + {w} ≤ {P_cap}",
                f"x + {2 * w} ≤ {P_cap}",
                f"2x + {2 * w} = {P_cap}",
            ]
            params = {"w": w, "P": P_cap, "tpl": "write_inequality_medium", "variant": v}
        elif v == "system_two":
            total = rng_obj.choice([30, 40, 50, 60, 75, 100])
            k = rng_obj.choice([2, 3])
            ans_str = f"a + b ≤ {total}; a ≥ {k}b"
            dist_pool = [
                f"a + b ≥ {total}; a ≤ {k}b",
                f"a + b ≥ {total}; a ≥ {k}b",
                f"a + b ≤ {total}; a ≤ {k}b",
            ]
            params = {"total": total, "k": k, "tpl": "write_inequality_medium", "variant": v}
        else:  # capacity_minus
            cap = rng_obj.choice([1000, 1500, 2000, 2500, 3000])
            fixed = rng_obj.choice([100, 200, 250, 300, 400, 500])
            w1 = rng_obj.randint(5, 25)
            w2 = rng_obj.randint(w1 + 5, w1 + 40)
            remaining = cap - fixed
            ans_str = f"{w1}x + {w2}y ≤ {remaining:,}"
            dist_pool = [
                f"{w1}x + {w2}y ≥ {remaining:,}",
                f"{w2}x + {w1}y ≤ {cap:,}",
                f"{w2}x + {w1}y ≥ {cap:,}",
                f"{w1}x + {w2}y ≤ {cap:,}",
            ]
            params = {"cap": cap, "fixed": fixed, "w1": w1, "w2": w2,
                      "tpl": "write_inequality_medium", "variant": v}
        ph = param_hash(params)
        if ph in exclude_params:
            continue
        dist = make_distractors(ans_str, dist_pool)
        ctx = (f"Write-inequality medium ({v}). Correct: {ans_str}. "
               f"The question must ask: Which inequality/system represents this situation?")
        return _lin_result(2, params, ph, ans_str, None, dist, "mcq", ctx)
    raise RuntimeError("write_inequality_medium d2: could not generate unique params")


def _d2_solve_one_var(rng_obj, exclude_params, variant=None):
    """Solve one-variable word-problem inequality; MCQ or SPR."""
    for _ in range(200):
        F = rng_obj.randint(30, 120)
        k = rng_obj.randint(6, 25)
        x_target = rng_obj.randint(15, 50)
        remainder = rng_obj.randint(0, k - 1)
        B = F + k * x_target + remainder
        answer = (B - F) // k
        if answer <= 0:
            continue
        assert F + k * answer <= B and F + k * (answer + 1) > B
        domain, fixed_name, unit_name = rng_obj.choice([
            ("event planning", "venue deposit", "guests"),
            ("international shipping", "base handling fee", "kilograms"),
            ("gym membership", "enrollment fee", "additional months"),
            ("catering service", "setup charge", "meals served"),
            ("self-storage rental", "base monthly fee", "additional cubic feet"),
            ("tutoring program", "registration fee", "one-hour sessions"),
        ])
        sub = variant or rng_obj.choice(["mcq_type", "spr_type"])
        qt = "mcq" if sub == "mcq_type" else "spr"
        params = {"F": F, "k": k, "B": B, "scenario": domain, "tpl": "solve_one_var", "variant": sub}
        ph = param_hash(params)
        if ph in exclude_params:
            continue
        ans = str(answer)
        sm, sx = spr_bounds(ans) if qt == "spr" else (None, None)
        dist = make_distractors(ans, [
            str(answer + 1),
            str(B // k),
            str(max(1, answer - 1)),
            str((B - F) // (k + 1)) if (B - F) // (k + 1) > 0 else str(answer + 2),
        ]) if qt == "mcq" else []
        ctx = (f"Scenario: {domain}. "
               f"Fixed cost: ${F} ({fixed_name}). Variable cost: ${k} per {unit_name}. Budget: ${B}. "
               f"Math: ({B} − {F}) ÷ {k} = {(B-F)/k:.3f}; floor = {answer} {unit_name}s. "
               f"The question must ask: What is the greatest number of {unit_name}s possible within a ${B} budget? "
               f"Write the stem using ONLY the specific dollar amounts ${F}, ${k}, ${B} — "
               f"DO NOT use variable names like F, k, B, or x in the question stem. "
               f"DO NOT ask for the fixed fee or the budget value. "
               f"Verified answer: {answer}.")
        return _lin_result(2, params, ph, ans, (sm, sx), dist, qt, ctx)
    raise RuntimeError("solve_one_var d2: could not generate unique params")


def _d2_point_satisfies(rng_obj, exclude_params, variant=None):
    """Which point satisfies y op mx+b?  Variant: less_than or greater_than."""
    for _ in range(200):
        m = rng_obj.choice([v for v in range(-6, 7) if v != 0])
        b = rng_obj.randint(-10, 15)
        op = rng_obj.choice(["<", ">"])
        if variant == "less_than" and op != "<":
            continue
        if variant == "greater_than" and op != ">":
            continue
        sub = variant or ("less_than" if op == "<" else "greater_than")
        x_c = rng_obj.randint(-6, 6)
        slack = rng_obj.randint(3, 12)
        y_c = (m * x_c + b) - slack if op == "<" else (m * x_c + b) + slack
        if abs(y_c) > 40:
            continue
        x_b_choices = [v for v in range(-5, 6) if v != x_c]
        x_b = rng_obj.choice(x_b_choices)
        y_b = m * x_b + b
        x_w1 = rng_obj.choice([v for v in range(-5, 6) if v not in {x_c, x_b}])
        y_w1 = (m * x_w1 + b) + 4 if op == "<" else (m * x_w1 + b) - 4
        x_w2 = rng_obj.choice([v for v in range(-5, 6) if v not in {x_c, x_b, x_w1}])
        y_w2 = (m * x_w2 + b) + 2 if op == "<" else (m * x_w2 + b) - 2

        def _ok(x, y):
            return (y < m * x + b) if op == "<" else (y > m * x + b)

        if not _ok(x_c, y_c) or _ok(x_b, y_b) or _ok(x_w1, y_w1) or _ok(x_w2, y_w2):
            continue
        ans_str = f"({x_c}, {y_c})"
        dist_pool = [f"({x_b}, {y_b})", f"({x_w1}, {y_w1})", f"({x_w2}, {y_w2})"]
        params = {"m": m, "b": b, "op": op, "xc": x_c, "yc": y_c, "tpl": "point_satisfies", "variant": sub}
        ph = param_hash(params)
        if ph in exclude_params:
            continue
        dist = make_distractors(ans_str, dist_pool)
        expr = fmt_lin_rhs(m, b)
        ctx = (f"Inequality: y {op} {expr}. Correct solution point {ans_str} "
               f"(strictly satisfies). Boundary distractor ({x_b}, {y_b}) lies exactly on "
               f"y = {expr} — equality fails the strict inequality. "
               f"The question must ask: Which point (x, y) is a solution to the given inequality?")
        return _lin_result(2, params, ph, ans_str, None, dist, "mcq", ctx)
    raise RuntimeError("point_satisfies d2: could not generate unique params")


def _d2_two_var_bound(rng_obj, exclude_params, variant=None):
    """Two-variable bound: x ≤ my − k word problem; MCQ or SPR."""
    for _ in range(200):
        m = rng_obj.randint(2, 6)
        k = rng_obj.randint(1, 10)
        y_val = rng_obj.randint(2, 10)
        answer = m * y_val - k
        if answer <= 0:
            continue
        domain, x_desc, y_desc = rng_obj.choice([
            ("agricultural output", "tons of crop harvested", "acres of farmland cultivated"),
            ("catering operation", "meals prepared per event", "kitchen staff on duty"),
            ("delivery service", "packages delivered per day", "vehicles deployed"),
            ("construction project", "bricks laid per hour", "workers on the site"),
            ("printing service", "pages printed per batch", "printers in operation"),
            ("customer support", "tickets resolved per shift", "agents logged in"),
        ])
        sub = variant or rng_obj.choice(["mcq_type", "spr_type"])
        qt = "mcq" if sub == "mcq_type" else "spr"
        params = {"m": m, "k": k, "y": y_val, "scenario": domain, "tpl": "two_var_bound", "variant": sub}
        ph = param_hash(params)
        if ph in exclude_params:
            continue
        ans = str(answer)
        sm, sx = spr_bounds(ans) if qt == "spr" else (None, None)
        dist = make_distractors(ans, [
            str(m * y_val + k),
            str(y_val - k),
            str(m * y_val),
            str(answer + 1),
        ]) if qt == "mcq" else []
        ctx = (f"THIS IS A NUMERICAL ANSWER QUESTION. The answer is the integer {answer}. "
               f"DO NOT ask 'which inequality represents' — that is the wrong question type. "
               f"DO NOT include A/B/C/D answer choices in the question stem. "
               f"Scenario: {domain}. "
               f"Rule: {x_desc} cannot exceed {m} times {y_desc} minus {k}. "
               f"Given {y_desc} = {y_val}: maximum {x_desc} = {m}×{y_val} − {k} = {answer}. "
               f"Write a word problem that states this rule naturally and asks: "
               f"What is the greatest possible value of {x_desc}? "
               f"The stem MUST state that {y_desc} = {y_val}. "
               f"DO NOT invent additional constraints or lower bounds. "
               f"DO NOT swap the roles of {x_desc} and {y_desc}. "
               f"Verified answer: {answer}.")
        return _lin_result(2, params, ph, ans, (sm, sx), dist, qt, ctx)
    raise RuntimeError("two_var_bound d2: could not generate unique params")


def _d2_system_solve_x(rng_obj, exclude_params, variant=None):
    """System: y > L and ax + y < R; find greatest integer x given y = y_given."""
    for _ in range(200):
        a = rng_obj.randint(2, 5)
        if variant == "coeff_small" and a > 3:
            continue
        if variant == "coeff_large" and a <= 3:
            continue
        sub = variant or ("coeff_small" if a <= 3 else "coeff_large")
        L = rng_obj.randint(5, 15)
        y_given = rng_obj.randint(L + 8, L + 40)
        R = rng_obj.randint(L + 3, L + 15)
        bound_num = R - y_given
        if bound_num % a == 0:
            bound_num -= rng_obj.randint(1, a - 1) if a > 1 else 0
        bound = bound_num / a
        if bound >= 0:
            continue
        correct_x = _math.floor(bound)
        assert a * correct_x + y_given < R
        assert a * (correct_x + 1) + y_given >= R
        params = {"L": L, "y": y_given, "a": a, "R": R, "tpl": "system_solve_x", "variant": sub}
        ph = param_hash(params)
        if ph in exclude_params:
            continue
        ans = str(correct_x)
        dist = make_distractors(ans, [
            str(correct_x + 1),
            str(correct_x + 2),
            str(-correct_x),
            str(correct_x - 1),
        ])
        ctx = (f"System: y > {L}; {a}x + y < {R}. Point (x, {y_given}) solves the system. "
               f"Since y = {y_given} > {L} ✓, the second constraint gives {a}x + {y_given} < {R} "
               f"→ x < {bound:.3f}. Largest integer satisfying: {correct_x}. "
               f"The question must ask: Which of the following could be the value of x? "
               f"STEM FORMAT: Present the two inequalities as a system — each on its own line. "
               f"Do NOT write them inline or join them with 'and'.")
        return _lin_result(2, params, ph, ans, None, dist, "mcq", ctx)
    raise RuntimeError("system_solve_x d2: could not generate unique params")


def _d2_table_satisfies(rng_obj, exclude_params, variant=None):
    """Table: which table has all rows satisfying y op mx+b?"""
    for _ in range(200):
        m = rng_obj.randint(3, 9)
        b = rng_obj.randint(-5, 15)
        op = rng_obj.choice([">", "<"])
        if variant == "strict_less" and op != "<":
            continue
        if variant == "strict_greater" and op != ">":
            continue
        sub = variant or ("strict_less" if op == "<" else "strict_greater")
        xs = sorted(rng_obj.sample(range(1, 8), 3))
        slack = rng_obj.randint(2, 5)
        ys_correct = [(m * x + b) + slack if op == ">" else (m * x + b) - slack for x in xs]
        ys_boundary = [m * x + b for x in xs]
        ys_wrong1 = [(m * x + b) - 2 if op == ">" else (m * x + b) + 2 for x in xs]
        ys_mixed = list(ys_correct)
        ys_mixed[1] = m * xs[1] + b

        def _tbl(ys):
            return f"x: {', '.join(map(str, xs))} | y: {', '.join(map(str, ys))}"

        ans_str = _tbl(ys_correct)
        dist_pool = [_tbl(ys_boundary), _tbl(ys_wrong1), _tbl(ys_mixed)]
        if any(d == ans_str for d in dist_pool):
            continue
        domain, x_var, y_var = rng_obj.choice([
            ("quality control", "production run number", "defect count"),
            ("environmental monitoring", "days since last rainfall", "air particulate level"),
            ("sales training", "weeks of training completed", "units sold per week"),
            ("fitness study", "workout sessions per week", "resting heart rate"),
            ("academic performance", "hours of daily practice", "weekly assessment score"),
            ("delivery routing", "stops per route", "total delivery time in minutes"),
        ])
        params = {"m": m, "b": b, "op": op, "xs": xs, "ys": ys_correct, "scenario": domain,
                  "tpl": "table_satisfies", "variant": sub}
        ph = param_hash(params)
        if ph in exclude_params:
            continue
        dist = make_distractors(ans_str, dist_pool)
        b_disp = f"+ {b}" if b >= 0 else f"− {abs(b)}"
        ctx = (f"Scenario: {domain}. x = {x_var}, y = {y_var}. "
               f"Strict inequality y {op} {m}x {b_disp}. Correct table: all y "
               f"{'above' if op == '>' else 'below'} the line by {slack}. "
               f"MANDATORY distractor: table with y = {m}x {b_disp} exactly (equality fails strict {op}). "
               f"The question must ask: For which of the following tables are all (x, y) "
               f"values solutions to the given inequality? "
               f"Write ONLY the question stem in questionStem — no table data, no A/B/C/D labels. "
               f"Each table goes as a separate entry in the choices field (A through D).")
        return _lin_result(2, params, ph, ans_str, None, dist, "mcq", ctx)
    raise RuntimeError("table_satisfies d2: could not generate unique params")


# ── d3 template functions ─────────────────────────────────────────────────────

def _d3_compound_range_algebraic(rng_obj, exclude_params, variant=None):
    """Compound range algebraic: commission or triangle inequality."""
    v = variant or rng_obj.choice(["commission", "triangle"])
    for _ in range(200):
        if v == "commission":
            r_pct = rng_obj.choice([4, 5, 6, 8, 10])
            r_str = f"0.{r_pct:02d}"
            p, q = rng_obj.choice([(2, 3), (2, 4), (3, 4), (3, 5)])
            ans_str = f"({p - 1}b/{r_str}) ≤ s ≤ ({q - 1}b/{r_str})"
            dist_pool = [
                f"{p}b ≤ s ≤ {q}b",
                f"({p}b/{r_str}) ≤ s ≤ ({q}b/{r_str})",
                f"(b/{r_str}) ≤ s ≤ ({p - 1}b/{r_str})",
                f"{p - 1}b ≤ s ≤ {q - 1}b",
            ]
            params = {"r": r_pct, "p": p, "q": q, "tpl": "compound_range_algebraic", "variant": v}
        else:  # triangle
            a = rng_obj.randint(4, 15)
            b = rng_obj.randint(a + 1, a + 15)
            low = b - a
            high = a + b
            ans_str = f"{low} < x < {high}"
            dist_pool = [
                f"x < {high}",
                f"x > {high}",
                f"x < {low} or x > {high}",
                f"{low} ≤ x ≤ {high}",
            ]
            params = {"a": a, "b": b, "tpl": "compound_range_algebraic", "variant": v}
        ph = param_hash(params)
        if ph in exclude_params:
            continue
        dist = make_distractors(ans_str, dist_pool)
        ctx = (f"Compound-range hard ({v}). Correct: {ans_str}. "
               f"The question must ask which inequality represents all possible values.")
        return _lin_result(3, params, ph, ans_str, None, dist, "mcq", ctx)
    raise RuntimeError("compound_range_algebraic d3: could not generate unique params")


def _d3_solve_one_var_tax(rng_obj, exclude_params, variant=None):
    """Maximum unit price under budget including sales tax."""
    for _ in range(200):
        n = rng_obj.randint(20, 80)
        if variant == "small_n" and n > 50:
            continue
        if variant == "large_n" and n <= 50:
            continue
        sub = variant or ("small_n" if n <= 50 else "large_n")
        t_pct = rng_obj.choice([5, 6, 7, 8])
        p_target = rng_obj.choice([40, 45, 50, 55, 60, 75, 80])
        B = round(n * (1 + t_pct / 100) * p_target)
        p_max = B / (n * (1 + t_pct / 100))
        p_max_round = round(p_max, 2)
        params = {"n": n, "t": t_pct, "B": B, "tpl": "solve_one_var_tax", "variant": sub}
        ph = param_hash(params)
        if ph in exclude_params:
            continue
        ans = f"${p_max_round:.2f}"
        d1 = B / n
        d2 = B / (n * (1 + (t_pct + 10) / 100))
        d3 = B / (n * (1 - t_pct / 100))
        dist = make_distractors(ans, [f"${d1:.2f}", f"${d2:.2f}", f"${d3:.2f}"])
        ctx = (f"This is a SAT word problem about finding the maximum unit price under a total budget "
               f"that includes sales tax. "
               f"Facts: {n} identical units, total budget = ${B}, sales tax rate = {t_pct}%. "
               f"Inequality: {n} × (1 + {t_pct}/100) × p ≤ {B} → p ≤ {p_max:.3f}. "
               f"Verified answer (rounded to nearest cent): {ans}. "
               f"The question stem MUST describe a real-world purchase scenario where someone buys "
               f"{n} identical items within a total budget of ${B} that includes {t_pct}% sales tax, "
               f"and asks: what is the maximum possible price per item before sales tax? "
               f"Do NOT write a linear equation question. Do NOT ask for x+y or any algebraic sum. "
               f"Write a word problem about buying {n} items with a budget and sales tax only.")
        return _lin_result(3, params, ph, ans, None, dist, "mcq", ctx)
    raise RuntimeError("solve_one_var_tax d3: could not generate unique params")


def _d3_two_var_bound_neg(rng_obj, exclude_params, variant=None):
    """Two-variable bound with negative y value; MCQ or SPR."""
    for _ in range(200):
        m = rng_obj.randint(2, 5)
        k = rng_obj.randint(1, 8)
        y_val = -rng_obj.randint(2, 8)
        answer = m * y_val - k
        sub = variant or rng_obj.choice(["mcq_type", "spr_type"])
        qt = "mcq" if sub == "mcq_type" else "spr"
        params = {"m": m, "k": k, "y": y_val, "tpl": "two_var_bound_neg", "variant": sub}
        ph = param_hash(params)
        if ph in exclude_params:
            continue
        ans = str(answer)
        sm, sx = spr_bounds(ans) if qt == "spr" else (None, None)
        dist = make_distractors(ans, [
            str(m * y_val + k),
            str(abs(answer)),
            str(m * y_val),
            str(y_val - k),
        ]) if qt == "mcq" else []
        ctx = (f"This is a SAT word problem about a two-variable inequality with a negative y value. "
               f"Verbal constraint: x is at most {k} less than {m} times y. "
               f"CRITICAL — the numbers play FIXED roles: "
               f"{m} is the COEFFICIENT that multiplies y. "
               f"{k} is the CONSTANT that is subtracted. "
               f"Inequality written out: x ≤ ({m} × y) − {k}. "
               f"DO NOT swap these: the coefficient of y is {m}, the subtracted constant is {k}. "
               f"Given y = {y_val}: x ≤ ({m} × {y_val}) − {k} = {m * y_val} − {k} = {answer}. "
               f"Verified answer: {answer}. "
               f"The question stem MUST state the verbal constraint exactly as: "
               f"'x is at most {k} less than {m} times y', then give y = {y_val}, "
               f"and ask: what is the greatest possible value of x? "
               f"Do NOT write a question about inequalities in one variable. "
               f"Do NOT write a question asking for x+y or any other combination. "
               f"Do NOT ask for the greatest integer satisfying a one-variable inequality. "
               f"The only question allowed is: what is the greatest possible value of x when y = {y_val}?")
        return _lin_result(3, params, ph, ans, (sm, sx), dist, qt, ctx)
    raise RuntimeError("two_var_bound_neg d3: could not generate unique params")


def _d3_system_pair(rng_obj, exclude_params, variant=None):
    """System pair: y ≤ ax+b AND y ≥ cx+d; find point satisfying both."""
    for _ in range(200):
        a = rng_obj.choice([v for v in range(-4, 5) if v != 0])
        if variant == "pos_a" and a <= 0:
            continue
        if variant == "neg_a" and a >= 0:
            continue
        sub = variant or ("pos_a" if a > 0 else "neg_a")
        b = rng_obj.randint(-5, 10)
        c = rng_obj.choice([v for v in range(-4, 5) if v not in {0, a}])
        d = rng_obj.randint(-5, 10)
        for _ in range(40):
            x_c = rng_obj.randint(-10, 10)
            y1 = a * x_c + b
            y2 = c * x_c + d
            if y2 <= y1:
                y_c = rng_obj.randint(y2, y1)
                break
        else:
            continue
        x_f1 = rng_obj.choice([v for v in range(-10, 11) if v != x_c])
        y_f1 = (a * x_f1 + b) + rng_obj.randint(3, 8)
        x_f2 = rng_obj.choice([v for v in range(-10, 11) if v not in {x_c, x_f1}])
        y_f2 = (c * x_f2 + d) - rng_obj.randint(3, 8)
        x_f3 = rng_obj.choice([v for v in range(-10, 11) if v not in {x_c, x_f1, x_f2}])
        y_f3 = (a * x_f3 + b) + rng_obj.randint(3, 8)

        def _sat(x, y):
            return (y <= a * x + b) and (y >= c * x + d)

        if not _sat(x_c, y_c) or _sat(x_f1, y_f1) or _sat(x_f2, y_f2) or _sat(x_f3, y_f3):
            continue
        ans_str = f"({x_c}, {y_c})"
        dist_pool = [f"({x_f1}, {y_f1})", f"({x_f2}, {y_f2})", f"({x_f3}, {y_f3})"]
        params = {"a": a, "b": b, "c": c, "d": d, "xc": x_c, "yc": y_c, "tpl": "system_pair", "variant": sub}
        ph = param_hash(params)
        if ph in exclude_params:
            continue
        dist = make_distractors(ans_str, dist_pool)
        expr1 = fmt_lin_rhs(a, b)
        expr2 = fmt_lin_rhs(c, d)
        ctx = (f"System: y ≤ {expr1}; y ≥ {expr2}. "
               f"Correct pair {ans_str} satisfies both (y1={a*x_c+b}, y2={c*x_c+d}). "
               f"The question must ask: Which ordered pair (x, y) is a solution to the given "
               f"system of inequalities?")
        return _lin_result(3, params, ph, ans_str, None, dist, "mcq", ctx)
    raise RuntimeError("system_pair d3: could not generate unique params")


def _d3_table_satisfies_twovar(rng_obj, exclude_params, variant=None):
    """Table: which table has all rows satisfying ax − y > K (large K)?"""
    for _ in range(200):
        a = rng_obj.choice([2, 3, 4, 5])
        if variant == "small_coeff" and a > 3:
            continue
        if variant == "large_coeff" and a <= 3:
            continue
        sub = variant or ("small_coeff" if a <= 3 else "large_coeff")
        K = rng_obj.randint(100, 500)
        base_x = _math.ceil((K + 6) / a) + rng_obj.randint(0, 2)
        xs = [base_x, base_x + 1, base_x + 2]
        ys_correct = [a * x - K - rng_obj.randint(2, 6) for x in xs]

        def _boundary(idx):
            ys = list(ys_correct)
            ys[idx] = a * xs[idx] - K
            return ys

        def _tbl(ys):
            return f"x: {', '.join(map(str, xs))} | y: {', '.join(map(str, ys))}"

        ans_str = _tbl(ys_correct)
        dist_pool = [_tbl(_boundary(0)), _tbl(_boundary(1)), _tbl(_boundary(2))]
        if any(d == ans_str for d in dist_pool):
            continue
        if not all(a * x - y > K for x, y in zip(xs, ys_correct)):
            continue
        domain, variables, logic = rng_obj.choice([
            (
                "a temperature monitoring system",
                f"x = heat output in BTUs, y = heat lost to the environment in BTUs",
                f"net heat gain ({a} × output − loss) must exceed {K} BTUs to maintain operating temperature",
            ),
            (
                "a financial performance report",
                f"x = revenue generated in dollars, y = expenses incurred in dollars",
                f"net profit ({a} × revenue − expenses) must exceed {K} dollars to meet the quarterly target",
            ),
            (
                "an electrical power grid analysis",
                f"x = power generated in megawatts, y = power lost during transmission in megawatts",
                f"net power delivered ({a} × generated − transmission loss) must exceed {K} MW to supply the region",
            ),
            (
                "a water resource study",
                f"x = water collected in liters, y = water lost to evaporation in liters",
                f"net water retained ({a} × collected − evaporation loss) must exceed {K} liters to sustain irrigation",
            ),
            (
                "a rocket propulsion test",
                f"x = thrust generated in newtons, y = drag force in newtons",
                f"net propulsive force ({a} × thrust − drag) must exceed {K} newtons to achieve liftoff",
            ),
            (
                "a climate research study",
                f"x = solar energy absorbed in joules, y = energy re-radiated into space in joules",
                f"net energy retained ({a} × absorbed − re-radiated) must exceed {K} joules to sustain warming",
            ),
        ])
        params = {"a": a, "K": K, "xs": xs, "ys": ys_correct, "scenario": domain,
                  "tpl": "table_satisfies_twovar", "variant": sub}
        ph = param_hash(params)
        if ph in exclude_params:
            continue
        dist = make_distractors(ans_str, dist_pool)
        ctx = (f"Strict inequality {a}x − y > {K}. Correct table: all rows strictly exceed "
               f"boundary. Each distractor has ONE row where {a}x − y = {K} exactly (fails strict >). "
               f"Context: {domain}. Variables: {variables}. "
               f"Real-world meaning: {logic}. "
               f"Keep all numbers exactly as given: x values {xs}, y values {ys_correct}, "
               f"coefficient {a}, constant {K}. Do NOT change any numbers. "
               f"The question must ask: For which of the following tables are all (x, y) values "
               f"solutions to the given inequality? "
               f"Write ONLY the question stem sentence in questionStem — no table data, no A/B/C/D labels. "
               f"Each table (with its x and y rows) goes as a separate entry in the choices field (A through D).")
        return _lin_result(3, params, ph, ans_str, None, dist, "mcq", ctx)
    raise RuntimeError("table_satisfies_twovar d3: could not generate unique params")


def _d3_interpret_term(rng_obj, exclude_params, variant=None):
    """Interpret p2*b in p1*a + p2*b ≤ cap: what does the term represent?"""
    for _ in range(200):
        p1 = rng_obj.randint(5, 15)
        p2 = rng_obj.randint(p1 + 2, p1 + 20)
        cap = rng_obj.randint((p1 + p2) * 3, (p1 + p2) * 10)
        if variant == "item_ab":
            item1, item2 = "item A", "item B"
        elif variant == "type_ab":
            item1, item2 = "type A", "type B"
        elif variant == "option_12":
            item1, item2 = "option 1", "option 2"
        else:
            item1, item2 = rng_obj.choice([
                ("item A", "item B"), ("type A", "type B"), ("option 1", "option 2"),
            ])
        sub = variant or {("item A", "item B"): "item_ab",
                          ("type A", "type B"): "type_ab",
                          ("option 1", "option 2"): "option_12"}[(item1, item2)]
        ans_str = f"total cost of all {item2} units"
        dist_pool = [
            f"cost of one {item2} unit",
            f"cost of one {item1} unit",
            f"total cost of all {item1} units",
        ]
        params = {"p1": p1, "p2": p2, "cap": cap, "i1": item1, "i2": item2,
                  "tpl": "interpret_term", "variant": sub}
        ph = param_hash(params)
        if ph in exclude_params:
            continue
        dist = make_distractors(ans_str, dist_pool)
        ctx = (f"Inequality: {p1}a + {p2}b ≤ {cap}, where a = number of {item1} units and "
               f"b = number of {item2} units. Interpret {p2}b: it is the product of the unit "
               f"price ({p2}) and the quantity (b) — i.e., the total cost of all {item2} units. "
               f"Correct: {ans_str}. "
               f"The question must ask: Which of the following is the best interpretation of "
               f"{p2}b in this context? "
               f"Write ONLY the question stem. Do NOT list or reference the answer choices.")
        return _lin_result(3, params, ph, ans_str, None, dist, "mcq", ctx)
    raise RuntimeError("interpret_term d3: could not generate unique params")


def _d3_complex_word(rng_obj, exclude_params, variant=None):
    """Complex word inequality: two_price_revenue / budget_min_total / consecutive_evens."""
    v = variant or rng_obj.choice(["two_price_revenue", "budget_min_total", "consecutive_evens"])
    for _ in range(200):
        if v == "two_price_revenue":
            n1 = rng_obj.randint(80, 250)
            n2 = rng_obj.randint(60, 200)
            diff = rng_obj.randint(3, 8)
            revenue_min = rng_obj.randint(2000, 6000)
            ans_str = f"{n1}(x + {diff}) + {n2}x ≥ {revenue_min:,}"
            dist_pool = [
                f"{n1}(x + {diff}) + {n2}x ≤ {revenue_min:,}",
                f"{n1}(x − {diff}) + {n2}x ≤ {revenue_min:,}",
                f"{n1}(x − {diff}) + {n2}x ≥ {revenue_min:,}",
            ]
            params = {"n1": n1, "n2": n2, "diff": diff, "R": revenue_min,
                      "tpl": "complex_word", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            dist = make_distractors(ans_str, dist_pool)
            ctx = (f"Two-price revenue: advance price = walk-in + {diff}; n1={n1}, n2={n2}; "
                   f"revenue ≥ {revenue_min}. Correct inequality: {ans_str}. "
                   f"The question must ask: Which inequality represents this situation?")
            return _lin_result(3, params, ph, ans_str, None, dist, "mcq", ctx)

        elif v == "budget_min_total":
            p_small = rng_obj.choice([4, 5, 6, 7])
            p_large = rng_obj.choice([12, 15, 18, 20])
            M = rng_obj.randint(150, 350)
            l_target = rng_obj.randint(int(M * 0.3), int(M * 0.8))
            s_target = M - l_target
            B = p_small * s_target + p_large * l_target + rng_obj.randint(0, p_large - 1)
            l_max = int((B - p_small * M) // (p_large - p_small))
            if l_max < 1 or l_max > M:
                continue
            assert p_small * (M - l_max) + p_large * l_max <= B
            params = {"ps": p_small, "pl": p_large, "M": M, "B": B,
                      "tpl": "complex_word", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans_val = str(l_max)
            qt = rng_obj.choice(["mcq", "spr"])
            sm, sx = spr_bounds(ans_val) if qt == "spr" else (None, None)
            dist_pool = [str(l_max + 1), str(l_max - 1), str(B // p_large)]
            dist = make_distractors(ans_val, dist_pool) if qt == "mcq" else []
            ctx = (f"Budget: {p_small}s + {p_large}l ≤ {B}; minimum total: s + l ≥ {M}. "
                   f"Substituting s = {M} − l: {p_small}({M} − l) + {p_large}l ≤ {B} "
                   f"→ l ≤ (B − {p_small}·{M}) / ({p_large} − {p_small}) = "
                   f"{(B - p_small*M) / (p_large - p_small):.3f}. "
                   f"Floor → {l_max}. "
                   f"The question must ask the maximum number of large units subject to budget + minimum total.")
            return _lin_result(3, params, ph, ans_val, (sm, sx), dist, qt, ctx)

        else:  # consecutive_evens
            offset = rng_obj.randint(10, 40)
            ans_str = f"5(n + 6) ≤ n + (n + 2) + {offset}"
            dist_pool = [
                f"5(n + 6) ≥ {offset} − (n + (n + 2))",
                f"5(n + 4) ≤ n + (n + 2) + {offset}",
                f"5(n + 4) ≥ {offset} − (n + (n + 2))",
            ]
            params = {"offset": offset, "tpl": "complex_word", "variant": v}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            dist = make_distractors(ans_str, dist_pool)
            ctx = (f"Four consecutive even integers starting at n: n, n+2, n+4, n+6. "
                   f"\"Product of 5 and the fourth\" = 5(n+6). "
                   f"\"At most {offset} more than the sum of the first and second\" = "
                   f"n + (n+2) + {offset}. Use ≤. Correct: {ans_str}. "
                   f"The question must ask: Which inequality represents this situation?")
            return _lin_result(3, params, ph, ans_str, None, dist, "mcq", ctx)

    raise RuntimeError("complex_word d3: could not generate unique params")


# ── Routing dicts ─────────────────────────────────────────────────────────────

_D1 = {
    "one_var_word_bound":    {"fn": _d1_one_var_word_bound,    "variants": ["min_additional", "max_additional", "packs_spr"]},
    "compound_range":        {"fn": _d1_compound_range,        "variants": ["direct", "scaled"]},
    "write_inequality_easy": {"fn": _d1_write_inequality_easy, "variants": ["total_cap", "rate_constraint", "budget", "fee_plus_hourly"]},
    "system_quadrant":       {"fn": _d1_system_quadrant,       "variants": ["q1", "q2", "q3", "q4"]},
}

_D2 = {
    "compound_range_scaled":    {"fn": _d2_compound_range_scaled,    "variants": ["scale_units", "threshold_select"]},
    "write_inequality_medium":  {"fn": _d2_write_inequality_medium,  "variants": ["perimeter", "system_two", "capacity_minus"]},
    "solve_one_var":            {"fn": _d2_solve_one_var,            "variants": ["mcq_type", "spr_type"]},
    "point_satisfies":          {"fn": _d2_point_satisfies,          "variants": ["less_than", "greater_than"]},
    "two_var_bound":            {"fn": _d2_two_var_bound,            "variants": ["mcq_type", "spr_type"]},
    "system_solve_x":           {"fn": _d2_system_solve_x,           "variants": ["coeff_small", "coeff_large"]},
    "table_satisfies":          {"fn": _d2_table_satisfies,          "variants": ["strict_less", "strict_greater"]},
}

_D3 = {
    "compound_range_algebraic": {"fn": _d3_compound_range_algebraic, "variants": ["commission", "triangle"]},
    "solve_one_var_tax":        {"fn": _d3_solve_one_var_tax,        "variants": ["small_n", "large_n"]},
    "two_var_bound_neg":        {"fn": _d3_two_var_bound_neg,        "variants": ["mcq_type", "spr_type"]},
    "system_pair":              {"fn": _d3_system_pair,              "variants": ["pos_a", "neg_a"]},
    "table_satisfies_twovar":   {"fn": _d3_table_satisfies_twovar,   "variants": ["small_coeff", "large_coeff"]},
    "interpret_term":           {"fn": _d3_interpret_term,           "variants": ["item_ab", "type_ab", "option_12"]},
    "complex_word":             {"fn": _d3_complex_word,             "variants": ["two_price_revenue", "budget_min_total", "consecutive_evens"]},
}

_ROUTING = {1: _D1, 2: _D2, 3: _D3}

# _LIN_TEMPLATES auto-derived — single source of truth
_LIN_TEMPLATES = {d: set(tpls.keys()) for d, tpls in _ROUTING.items()}


# ── Public metadata API ───────────────────────────────────────────────────────

def lin_variants(difficulty: int, template: str = None) -> dict:
    """
    Return variant metadata for linear_inequalities.

    If template is None: returns {template: [variants]} for all templates
    at the given difficulty level.

    If template is given: returns {"variants": [...]} for that template.
    """
    routing = _ROUTING.get(difficulty, {})
    if template is None:
        return {tpl: entry["variants"] for tpl, entry in routing.items()}
    if template not in routing:
        raise ValueError(
            f"Unknown template '{template}' for linear_inequalities d{difficulty}"
        )
    return {"variants": routing[template]["variants"]}


# ── Main generator ────────────────────────────────────────────────────────────

def gen_linear_inequalities(difficulty: int, rng_obj: random.Random, exclude_params: set,
                             force_template: str = None,
                             force_variant: str = None,
                             **_kwargs) -> dict:
    """
    Linear inequalities generator (LIN).

    Dispatches to a standalone per-template function via _D1/_D2/_D3 routing dicts.

    Args:
        force_template: pin to a specific template (e.g. "system_quadrant").
                        If None, picks randomly from the difficulty level's pool.
        force_variant:  pin to a specific variant within the template
                        (e.g. "q1", "less_than"). If None, no variant filter applied.
    """
    clamped = min(max(difficulty, 1), 3)
    routing = _ROUTING.get(clamped, _D3)

    if force_template is not None:
        if force_template not in routing:
            valid = sorted(routing.keys())
            raise ValueError(
                f"--template '{force_template}' is not valid for "
                f"linear_inequalities d{clamped}. Valid: {valid}"
            )
        tpl = force_template
    else:
        tpl = rng_obj.choice(list(routing.keys()))

    entry = routing[tpl]
    return entry["fn"](rng_obj, exclude_params, variant=force_variant)
