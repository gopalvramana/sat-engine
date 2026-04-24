#!/usr/bin/env python3
"""
math_engine.py — SymPy-based deterministic SAT math question generator.

Usage:
    python math_engine.py --skill=linear_eq_one_var --difficulty=3 --count=3
    python math_engine.py --skill=all --difficulty=3 --count=11
    python math_engine.py --count=10   # round-robin all skills

Output: N JSON lines on stdout (one MathObject per line).
Exit code: 0 on success, non-zero on any verification or generation failure.

Supported skills (Phase 1):
    linear_eq_one_var, linear_eq_word_problems, systems_linear_eq,
    linear_functions, quadratic_equations, percentages, ratios_rates,
    proportional_relationships, pythagorean_theorem, area_2d,
    coordinate_geometry
"""

import argparse
import hashlib
import json
import math
import random
import sys

try:
    import sympy as sp
    from sympy import symbols, solve, sqrt, Rational
except ImportError:
    print('{"error": "sympy not installed — run: pip install sympy==1.13.3"}',
          file=sys.stderr)
    sys.exit(1)

# ── Skill registry ────────────────────────────────────────────────────────────

SKILL_CODES = {
    "linear_eq_one_var":          "LEQ",
    "linear_eq_word_problems":    "LWP",
    "systems_linear_eq":          "SLE",
    "linear_functions":           "LFN",
    "linear_eq_two_var":          "L2V",
    "quadratic_equations":        "QEQ",
    "percentages":                "PCT",
    "ratios_rates":               "RAT",
    "proportional_relationships": "PRP",
    "pythagorean_theorem":        "PYT",
    "area_2d":                    "ARA",
    "coordinate_geometry":        "CGE",
    "circles":                    "CIR",
    "volume_3d":                  "VOL",
    "plane_geometry":             "PLG",
    "data_analysis":              "DAT",
    "statistics":                 "STA",
    "sequences_series":           "SEQ",
    "exponents_radicals":         "EXR",
    "complex_numbers":            "CMX",
    "polynomials":                "POL",
    "probability":                "PRB",
    "two_way_tables":             "TWT",
    "linear_inequalities":        "LIN",
    "absolute_value":             "ABV",
    "special_triangles":          "SPT",
    "trigonometry":               "TRG",
    "quadratic_functions":        "QFN",
    "scatterplot_analysis":       "SCA",
    "equivalent_expressions":     "EXP",
    "nonlinear_equations":        "NLE",
}

ALL_SKILLS = list(SKILL_CODES.keys())

# ── Utilities ─────────────────────────────────────────────────────────────────

def param_hash(params: dict) -> str:
    """SHA-256 of canonically serialized params."""
    serialized = json.dumps(params, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode()).hexdigest()


def fmt_num(n) -> str:
    """Format a number: integer string when whole, fraction or 2dp otherwise."""
    if isinstance(n, sp.Basic):
        if n.is_Integer or (n.is_Rational and n == int(n)):
            return str(int(n))
        if isinstance(n, sp.Rational) and n.q <= 20:
            return f"{n.p}/{n.q}"
        return f"{float(n):.2f}"
    if isinstance(n, float):
        return str(int(n)) if n == int(n) else f"{n:.2f}"
    return str(n)


def fmt_fn(m, b) -> str:
    """Format a linear function as 'y=mx+b' — normalises m=±1 to 'x'/'-x'."""
    mx = "x" if m == 1 else ("-x" if m == -1 else f"{m}x")
    if b == 0:
        return f"y={mx}"
    elif b > 0:
        return f"y={mx}+{b}"
    else:
        return f"y={mx}{b}"   # b is already negative, str(b) starts with '-'


def fmt_fx(m, b) -> str:
    """Format f(x) = mx + b cleanly for answer choices (used by linear_eq_two_var Type 9)."""
    mx = "x" if m == 1 else ("-x" if m == -1 else f"{m}x")
    if b == 0:
        return f"f(x) = {mx}"
    elif b > 0:
        return f"f(x) = {mx} + {b}"
    else:
        return f"f(x) = {mx} - {abs(b)}"


def fmt_lin_rhs(m, b, var: str = "x") -> str:
    """Format a linear expression mx + b cleanly using Unicode minus.

    Handles m=±1 as 'x'/'−x' (not '1x'/'-1x') and merges sign of b
    into the connector so negatives read as 'x − 5', not 'x + -5'.
    """
    if m == 0:
        return str(b)
    if m == 1:
        mx = var
    elif m == -1:
        mx = f"−{var}"
    elif m > 0:
        mx = f"{m}{var}"
    else:
        mx = f"−{abs(m)}{var}"
    if b == 0:
        return mx
    if b > 0:
        return f"{mx} + {b}"
    return f"{mx} − {abs(b)}"


def spr_bounds(answer_str: str):
    """(sprMin, sprMax) for SPR — exact match for integers, ±0.01 for decimals."""
    try:
        from fractions import Fraction
        val = float(Fraction(answer_str))
        if val == int(val):
            return (val, val)
        return (round(val - 0.01, 4), round(val + 0.01, 4))
    except Exception:
        return (None, None)


def make_distractors(correct_str: str, candidates: list) -> list:
    """Return exactly 3 distinct distractors (never equal to correct).

    Fallback sequence uses varied offsets to avoid obvious answer±1 patterns.
    """
    seen = {correct_str}
    result = []
    for d in candidates:
        s = str(d)
        if s not in seen and s.strip():
            seen.add(s)
            result.append(s)
        if len(result) == 3:
            break
    # Fallback: varied offsets so we never emit answer, answer+1, answer+2
    _fallback_offsets = [-1, 2, -2, 3, -3, 4, -4, 5, -5]
    fi = 0
    while len(result) < 3:
        try:
            base = int(float(correct_str.split("/")[0]))
        except Exception:
            base = 0
        offset = _fallback_offsets[fi] if fi < len(_fallback_offsets) else fi + 2
        fi += 1
        s = str(base + offset)
        if s not in seen:
            seen.add(s)
            result.append(s)
    return result[:3]


# Known Pythagorean triples for clean integer answers
PYTH_TRIPLES = [
    (3, 4, 5), (5, 12, 13), (8, 15, 17), (7, 24, 25),
    (6, 8, 10), (9, 12, 15), (10, 24, 26), (20, 21, 29),
    (9, 40, 41), (12, 16, 20), (15, 20, 25), (28, 45, 53),
]

# Scenario tag pools
LWP_SCENARIOS = [
    "bakery", "garden", "classroom", "sports_team", "road_trip",
    "savings", "ticket_sales", "grocery", "farm", "construction",
    "age_problem", "coins", "distance_rate", "rental", "catering",
]
PCT_SCENARIOS = [
    "sale_discount", "tax_calculation", "tip_restaurant", "population_growth",
    "test_scores", "stock_price", "salary_raise", "survey_results",
    "budget_allocation", "membership_fee",
]
RAT_SCENARIOS = [
    "recipe_scaling", "map_scale", "mixing_solutions", "speed_comparison",
    "production_rate", "fuel_efficiency", "class_ratio", "currency_exchange",
    "survey_results", "ingredient_ratio",
]
PRP_SCENARIOS = [
    "unit_price", "conversion_factor", "similar_triangles", "scale_model",
    "calorie_counting", "water_usage", "earnings_per_hour", "paint_coverage",
    "distance_time", "batch_recipe",
]


def pick_scenario(pool: list, exclude: set, rng_obj: random.Random) -> str:
    available = [s for s in pool if s not in exclude]
    return rng_obj.choice(available) if available else rng_obj.choice(pool)


# ── Constraint definitions ────────────────────────────────────────────────────
#
# Per-skill, per-difficulty rules checked on the final MathObject AFTER it is
# built. Inline guards (continue) handle generation-time rejection (e.g. x1==x2).
# This layer catches output-level issues: missing SPR bounds, duplicate
# distractors, answer appearing in distractors, etc.
#
# Keys per entry:
#   require_integer_answer  bool   MCQ answer must be a plain integer string
#   max_abs_answer          int    abs(float(answer)) must be ≤ this value
#   mcq_distractor_count    int    exactly this many distractors for MCQ (default 3)

CONSTRAINTS: dict = {
    "linear_eq_two_var": {
        1: {"require_integer_answer": True,  "max_abs_answer": 12},
        2: {"require_integer_answer": False, "max_abs_answer": 20},
        3: {"require_integer_answer": False, "max_abs_answer": 500},
    },
}


def validate_math_object(obj: dict) -> list:
    """Check a generated MathObject against skill+difficulty constraints.

    Returns a list of violation strings.  Empty list = all checks pass.
    Callers should `continue` the retry loop when violations are non-empty.
    """
    skill      = obj["skill"]
    difficulty = obj["difficulty"]
    qt         = obj["questionType"]
    ans        = str(obj.get("verifiedAnswer", ""))
    distractors = obj.get("distractors") or []

    violations = []
    c = CONSTRAINTS.get(skill, {}).get(difficulty, {})

    # ── Universal checks (all skills / difficulties) ──────────────────────────

    # 1. Answer must not be empty
    if not ans.strip():
        violations.append("empty verifiedAnswer")

    # 2. MCQ: exactly 3 distractors required
    if qt == "mcq":
        req = c.get("mcq_distractor_count", 3)
        if len(distractors) != req:
            violations.append(
                f"MCQ needs {req} distractors, got {len(distractors)}"
            )

    # 3. MCQ: correct answer must not appear in distractors
    if qt == "mcq" and ans in distractors:
        violations.append(f"correct answer '{ans}' duplicated in distractors")

    # 4. MCQ: all distractors must be distinct
    if qt == "mcq" and len(set(distractors)) != len(distractors):
        violations.append("duplicate distractors")

    # 5. SPR: sprMin and sprMax must be set
    if qt == "spr":
        if obj.get("sprMin") is None or obj.get("sprMax") is None:
            violations.append("SPR missing sprMin/sprMax")

    # ── Skill-specific checks ─────────────────────────────────────────────────

    # 6. Integer answer requirement (skip non-numeric answers like "f(x) = 2x+3")
    if c.get("require_integer_answer") and qt == "mcq":
        try:
            v = float(ans)
            if v != int(v):
                violations.append(
                    f"d{difficulty} requires integer answer, got '{ans}'"
                )
        except ValueError:
            pass  # non-numeric answer string — exempt from integer check

    # 7. Max absolute answer value
    max_abs = c.get("max_abs_answer")
    if max_abs is not None:
        try:
            from fractions import Fraction
            v = abs(float(Fraction(ans)))
            if v > max_abs:
                violations.append(
                    f"answer magnitude {v} exceeds max {max_abs} for d{difficulty}"
                )
        except (ValueError, ZeroDivisionError):
            pass  # non-numeric (e.g. "f(x) = ...") — exempt

    return violations
