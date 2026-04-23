import math
import random
import sympy as sp
from sympy import symbols, solve, sqrt, Rational
from .core import (
    param_hash, fmt_num, fmt_fn, fmt_fx, fmt_lin_rhs,
    spr_bounds, make_distractors, pick_scenario, validate_math_object,
    PYTH_TRIPLES, LWP_SCENARIOS, PCT_SCENARIOS, RAT_SCENARIOS, PRP_SCENARIOS,
)

# ── Generator: two_way_tables ─────────────────────────────────────────────────

TWT_ROWS = [("Cats", "Dogs"), ("Pass", "Fail"), ("Yes", "No"), ("Morning", "Evening")]
TWT_COLS = [("Male", "Female"), ("Grade_9", "Grade_10"), ("City", "Rural"), ("Team_A", "Team_B")]


def _gcd(a, b):
    while b:
        a, b = b, a % b
    return a


def gen_two_way_tables(difficulty: int, rng_obj: random.Random, exclude_params: set, **_):
    for _ in range(200):
        row_labels = list(rng_obj.choice(TWT_ROWS))
        col_labels = list(rng_obj.choice(TWT_COLS))
        a = rng_obj.randint(5, 25)
        b = rng_obj.randint(5, 25)
        c = rng_obj.randint(5, 25)
        d_cell = rng_obj.randint(5, 25)
        r1t = a + b
        r2t = c + d_cell
        c1t = a + c
        c2t = b + d_cell
        grand = a + b + c + d_cell

        if difficulty == 1:
            params = {"a": a, "b": b, "c": c, "d": d_cell, "rows": row_labels, "cols": col_labels, "d": 1}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(a)
            diag = _twt_diag(row_labels, col_labels, a, b, c, d_cell)
            distractors = make_distractors(ans, [str(b), str(c), str(r1t)])
            return _twt(1, params, ph, ans, (None, None), diag, distractors, "mcq")
        elif difficulty == 2:
            params = {"a": a, "b": b, "c": c, "d": d_cell, "rows": row_labels, "cols": col_labels, "d": 2}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(r1t)
            diag = _twt_diag(row_labels, col_labels, a, b, c, d_cell)
            distractors = make_distractors(ans, [str(a), str(c1t), str(grand)])
            return _twt(2, params, ph, ans, (None, None), diag, distractors, "mcq")
        elif difficulty == 3:
            g = _gcd(a, r1t)
            p_num, p_den = a // g, r1t // g
            params = {"a": a, "b": b, "c": c, "d": d_cell, "rows": row_labels, "cols": col_labels, "d": 3}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = f"{p_num}/{p_den}" if p_den > 1 else str(p_num)
            diag = _twt_diag(row_labels, col_labels, a, b, c, d_cell)
            g2 = _gcd(a, grand)
            d2 = [f"{a // g2}/{grand // g2}", f"{b}/{r1t}", f"{c1t}/{grand}"]
            return _twt(3, params, ph, ans, (None, None), diag, d2, "mcq")
        elif difficulty == 4:
            # Hide cell d_cell, give row/col totals
            params = {"a": a, "b": b, "c": c, "r2t": r2t, "c2t": c2t, "grand": grand,
                      "rows": row_labels, "cols": col_labels, "d": 4}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            ans = str(d_cell)
            # Show table with d_cell hidden (0 placeholder)
            diag = _twt_diag(row_labels, col_labels, a, b, c, 0, highlight_row=1, highlight_col=1)
            qt = "spr" if rng_obj.random() < 0.5 else "mcq"
            sb = spr_bounds(ans) if qt == "spr" else (None, None)
            distractors = make_distractors(ans, [str(d_cell + 2), str(d_cell - 3), str(grand - a - b - c + 1)])
            return _twt(4, params, ph, ans, sb, diag, distractors, qt)
        elif difficulty == 5:
            # Compare P(col1|row1) vs P(col1|row2)
            p1 = a / r1t
            p2 = c / r2t
            ans = row_labels[0] if p1 > p2 else row_labels[1]
            params = {"a": a, "b": b, "c": c, "d": d_cell, "rows": row_labels, "cols": col_labels, "d": 5}
            ph = param_hash(params)
            if ph in exclude_params:
                continue
            other = row_labels[1] if ans == row_labels[0] else row_labels[0]
            diag = _twt_diag(row_labels, col_labels, a, b, c, d_cell)
            d2 = [other, "equal", "cannot be determined"]
            return _twt(5, params, ph, ans, (None, None), diag, d2, "mcq")
        raise RuntimeError(f"Could not generate unique params for two_way_tables d{difficulty}")
    raise RuntimeError(f"Could not generate unique params for two_way_tables d{difficulty}")


def _twt_diag(row_labels, col_labels, a, b, c, d_cell, highlight_row=None, highlight_col=None):
    r1t = a + b
    r2t = c + d_cell
    c1t = a + c
    c2t = b + d_cell
    grand = a + b + c + d_cell
    return {"type": "two_way_table", "row_labels": row_labels, "col_labels": col_labels,
            "cells": [[a, b], [c, d_cell]], "row_totals": [r1t, r2t],
            "col_totals": [c1t, c2t], "grand_total": grand,
            "highlight_row": highlight_row, "highlight_col": highlight_col}


def _twt(d, params, ph, ans, spr_val, diag, distractors, qt="mcq"):
    sb = spr_val if qt == "spr" else (None, None)
    return {"skill": "two_way_tables", "difficulty": d, "questionType": qt,
            "params": params, "paramHash": ph, "verifiedAnswer": ans,
            "distractors": distractors if qt == "mcq" else [], "sprMin": sb[0], "sprMax": sb[1],
            "scenarioTag": None, "diagramSpec": diag, "questionContext": ""}
