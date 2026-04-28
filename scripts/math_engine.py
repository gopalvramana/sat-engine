#!/usr/bin/env python3
"""
math_engine.py — thin orchestrator that imports all skill generators
from the math_skills package and dispatches --skill requests.

Usage:
    python math_engine.py --skill=linear_eq_one_var --difficulty=3 --count=3
    python math_engine.py --skill=all --difficulty=3 --count=11
    python math_engine.py --count=10   # round-robin all skills

Output: N JSON lines on stdout (one MathObject per line).
Exit code: 0 on success, non-zero on any verification or generation failure.
"""

import argparse
import json
import random
import sys

# ── Import core registry ──────────────────────────────────────────────────────
from math_skills.core import SKILL_CODES, ALL_SKILLS, validate_math_object

# ── Import all skill generators ───────────────────────────────────────────────
from math_skills.lin_eq      import gen_linear_eq_one_var, leq_variants
from math_skills.lin_wp      import gen_linear_eq_word_problems
from math_skills.systems     import gen_systems_linear_eq, sle_variants
from math_skills.lin_fn      import gen_linear_functions, lfn_variants
from math_skills.lin_2v      import gen_linear_eq_two_var, l2v_variants
from math_skills.quadratic_eq import gen_quadratic_equations
from math_skills.percentages import gen_percentages
from math_skills.ratios      import gen_ratios_rates
from math_skills.proportional import gen_proportional_relationships
from math_skills.pythagorean import gen_pythagorean_theorem
from math_skills.area_2d     import gen_area_2d
from math_skills.coordinate  import gen_coordinate_geometry
from math_skills.circles     import gen_circles
from math_skills.volume_3d   import gen_volume_3d
from math_skills.plane_geom  import gen_plane_geometry
from math_skills.data_analysis import gen_data_analysis
from math_skills.statistics  import gen_statistics
from math_skills.sequences   import gen_sequences_series
from math_skills.exponents   import gen_exponents_radicals
from math_skills.complex_nums import gen_complex_numbers
from math_skills.polynomials import gen_polynomials
from math_skills.probability import gen_probability
from math_skills.two_way     import gen_two_way_tables
from math_skills.inequalities import gen_linear_inequalities, lin_variants
from math_skills.absolute_val import gen_absolute_value
from math_skills.special_tri import gen_special_triangles
from math_skills.trigonometry import gen_trigonometry
from math_skills.quadratic_fn import gen_quadratic_functions
from math_skills.scatterplot  import gen_scatterplot_analysis
from math_skills.equiv_expr          import gen_equivalent_expressions, exp_variants
from math_skills.nonlinear_equations import gen_nonlinear_equations, nle_variants
from math_skills.nonlinear_fn        import gen_nonlinear_fn, nlf_variants


# ── Dispatch ──────────────────────────────────────────────────────────────────

def generate_one(skill: str, difficulty: int, rng_obj: random.Random,
                 exclude_params: set, exclude_scenarios: set,
                 force_template: str = None,
                 exclude_templates: set = None,
                 force_variant: str = None) -> dict:
    kw = dict(difficulty=difficulty, rng_obj=rng_obj, exclude_params=exclude_params)
    if force_template is not None:
        kw["force_template"] = force_template
    if exclude_templates:
        kw["exclude_templates"] = exclude_templates
    if force_variant is not None:
        kw["force_variant"] = force_variant
    dispatch = {
        "linear_eq_one_var":          gen_linear_eq_one_var,
        "linear_eq_word_problems":    lambda **k: gen_linear_eq_word_problems(
                                          **k, exclude_scenarios=exclude_scenarios),
        "systems_linear_eq":          gen_systems_linear_eq,
        "linear_functions":           gen_linear_functions,
        "linear_eq_two_var":          gen_linear_eq_two_var,
        "quadratic_equations":        gen_quadratic_equations,
        "percentages":                lambda **k: gen_percentages(
                                          **k, exclude_scenarios=exclude_scenarios),
        "ratios_rates":               lambda **k: gen_ratios_rates(
                                          **k, exclude_scenarios=exclude_scenarios),
        "proportional_relationships": lambda **k: gen_proportional_relationships(
                                          **k, exclude_scenarios=exclude_scenarios),
        "pythagorean_theorem":        gen_pythagorean_theorem,
        "area_2d":                    gen_area_2d,
        "coordinate_geometry":        gen_coordinate_geometry,
        "circles":                    gen_circles,
        "volume_3d":                  gen_volume_3d,
        "plane_geometry":             gen_plane_geometry,
        "data_analysis":              gen_data_analysis,
        "statistics":                 gen_statistics,
        "sequences_series":           gen_sequences_series,
        "exponents_radicals":         gen_exponents_radicals,
        "complex_numbers":            gen_complex_numbers,
        "polynomials":                gen_polynomials,
        "probability":                lambda **k: gen_probability(
                                          **k, exclude_scenarios=exclude_scenarios),
        "two_way_tables":             gen_two_way_tables,
        "linear_inequalities":        gen_linear_inequalities,
        "absolute_value":             gen_absolute_value,
        "special_triangles":          gen_special_triangles,
        "trigonometry":               gen_trigonometry,
        "quadratic_functions":        gen_quadratic_functions,
        "scatterplot_analysis":       lambda **k: gen_scatterplot_analysis(
                                          **k, exclude_scenarios=exclude_scenarios),
        "equivalent_expressions":     gen_equivalent_expressions,
        "nonlinear_equations":        gen_nonlinear_equations,
        "nonlinear_functions":        gen_nonlinear_fn,
    }
    if skill not in dispatch:
        raise ValueError(f"Unknown skill: {skill}")
    return dispatch[skill](**kw)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="SymPy SAT math question generator")
    parser.add_argument("--skill",      default="linear_eq_one_var",
                        help="Skill key or 'all' for round-robin")
    parser.add_argument("--difficulty", type=int, default=3,
                        help="Difficulty 1-7  (6-7 auto-fallback to 4)")
    parser.add_argument("--count",      type=int, default=1)
    parser.add_argument("--seed",       type=int, default=None)
    parser.add_argument("--exclude-params",    default="",
                        help="Comma-separated param hashes to skip")
    parser.add_argument("--exclude-scenarios", default="",
                        help="Comma-separated scenario tags to avoid")
    parser.add_argument("--exclude-templates", default="",
                        help="Comma-separated template names already used in this batch")
    parser.add_argument("--template",          default=None,
                        help="Pin to a specific template within the skill+difficulty "
                             "(e.g. function_shift, translate_intercept, one_var_word_bound). "
                             "Supported for linear_eq_one_var, linear_eq_two_var, linear_inequalities.")
    parser.add_argument("--variant",           default=None,
                        help="Pin to a specific variant within the template "
                             "(e.g. neg_slope, pos_int, shift_down). "
                             "Currently supported for linear_eq_two_var.")
    parser.add_argument("--list-variants",     action="store_true", default=False,
                        help="Print available variants for --skill + --difficulty (+ optional --template) "
                             "as JSON to stdout, then exit.")
    args = parser.parse_args()

    rng_obj            = random.Random(args.seed)
    exclude_params     = set(h for h in args.exclude_params.split(",")    if h)
    exclude_scenarios  = set(s for s in args.exclude_scenarios.split(",") if s)
    exclude_templates  = set(t for t in args.exclude_templates.split(",") if t)

    # Clamp to SAT 3-level taxonomy (d1=Easy, d2=Medium, d3=Hard)
    difficulty = min(args.difficulty, 3)

    # ── --list-variants: print metadata and exit ──────────────────────────────
    if args.list_variants:
        _VARIANTS_SUPPORTED = {"linear_eq_one_var", "linear_eq_two_var",
                               "linear_inequalities", "systems_linear_eq",
                               "linear_functions", "equivalent_expressions",
                               "nonlinear_equations", "nonlinear_functions"}
        skill = args.skill
        if skill not in _VARIANTS_SUPPORTED:
            print(json.dumps({"error": f"--list-variants is only supported for {sorted(_VARIANTS_SUPPORTED)}"}),
                  file=sys.stderr)
            sys.exit(1)
        if skill == "linear_eq_one_var":
            data = leq_variants(difficulty, template=args.template)
        elif skill == "linear_eq_two_var":
            data = l2v_variants(difficulty, template=args.template)
        elif skill == "linear_inequalities":
            data = lin_variants(difficulty, template=args.template)
        elif skill == "systems_linear_eq":
            data = sle_variants(difficulty, template=args.template)
        elif skill == "linear_functions":
            data = lfn_variants(difficulty, template=args.template)
        elif skill == "equivalent_expressions":
            data = exp_variants(difficulty, template=args.template)
        elif skill == "nonlinear_equations":
            data = nle_variants(difficulty, template=args.template)
        elif skill == "nonlinear_functions":
            data = nlf_variants(difficulty, template=args.template)
        print(json.dumps(data))
        sys.exit(0)

    # Warn if --template is used with a skill that doesn't support it
    _TEMPLATE_SUPPORTED = {"linear_eq_one_var", "linear_eq_two_var",
                            "linear_inequalities", "systems_linear_eq",
                            "linear_functions", "equivalent_expressions",
                            "nonlinear_equations", "nonlinear_functions"}
    if args.template is not None and args.skill not in _TEMPLATE_SUPPORTED and args.skill != "all":
        print(json.dumps({"warning": f"--template is only supported for {sorted(_TEMPLATE_SUPPORTED)}; "
                                     f"ignoring for skill '{args.skill}'"}), file=sys.stderr)

    if args.skill == "all":
        skills = (ALL_SKILLS * (args.count // len(ALL_SKILLS) + 1))[:args.count]
    else:
        if args.skill not in SKILL_CODES:
            print(json.dumps({"error": f"Unknown skill: {args.skill}"}), file=sys.stderr)
            sys.exit(1)
        skills = [args.skill] * args.count

    for skill in skills:
        try:
            mo = generate_one(skill, difficulty, rng_obj, exclude_params, exclude_scenarios,
                              force_template=args.template,
                              exclude_templates=exclude_templates,
                              force_variant=args.variant)
            exclude_params.add(mo["paramHash"])           # prevent param-level duplicates
            tpl = (mo.get("params") or {}).get("tpl")
            if tpl:
                exclude_templates.add(tpl)               # prevent template repeats in batch
            print(json.dumps(mo))
            sys.stdout.flush()
        except NotImplementedError as e:
            print(json.dumps({"error": str(e), "skill": skill, "difficulty": difficulty}),
                  file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(json.dumps({"error": str(e), "skill": skill, "difficulty": difficulty}),
                  file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
