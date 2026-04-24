# Advanced Math — Bluebook Analysis

**Source:** `/Users/ramana/SatEngine/AdvancedMath/AM/` (414 screenshots, AM1 + AM2)  
**Analyzed:** 2026-04-22  
**Status:** Analysis complete. Implementation deferred — Algebra gaps to be closed first.

---

## Dataset

| Item | Count |
|---|---|
| Total pages | 414 |
| Continuation pages (graphs/rationale only) | 38 |
| Complete questions | **376** |

---

## 3 Bluebook Skill Labels (only 3)

| Bluebook Skill | Short code | Count | % |
|---|---|---|---|
| Nonlinear functions | NLF | 179 | 48% |
| Nonlinear equations in one variable and systems of equations in two variables | NLE | 140 | 37% |
| Equivalent expressions | EXP | 57 | 15% |

**SEQ (sequences_series) and CMX (complex_numbers) do not appear in any of the 376 questions.**  
They are not Bluebook Advanced Math skills. No redesign needed for those generators.

---

## Difficulty Distribution (estimated from full read)

| Skill | Easy | Medium | Hard |
|---|---|---|---|
| EXP | ~25 (44%) | ~18 (32%) | ~14 (25%) |
| NLF | ~55 (31%) | ~62 (35%) | ~62 (35%) |
| NLE | ~42 (30%) | ~50 (36%) | ~48 (34%) |

---

## Generator Mapping

| Bluebook Skill | Generator | Status |
|---|---|---|
| EXP | `equiv_expr` (new, replaces EXR/POL) | ✅ **Implemented** — 13 templates · 25 variants; covers rational expressions, polynomial manipulation, exponent equations |
| NLE | `nonlinear_equations` (new, replaces QEQ) | ✅ **Implemented** — 22 templates · 42 variants; covers systems, Vieta's, discriminant, tangent, radical equations, literal rearrangement |
| NLF | `nonlinear_fn` (new, replaces QFN) | 🔜 **Planned** — 31 templates · 58 variants; exponential, radical, rational, quadratic, composition, piecewise, inequality systems |

---

## Template Inventory (consolidated)

### EXP — 13 templates

| d | Template | Description |
|---|---|---|
| d1 | `combine_like_terms` | Distribute single parenthesis then collect; or pure like-term collection |
| d1 | `factor_gcf` | Factor out GCF from polynomial: `8x¹⁰−8x⁹+88x → 8x(x⁹−x⁸+11)` |
| d1 | `rational_exponent_radical` | Convert `x^(1/k)` ↔ `ᵏ√x` |
| d1 | `factor_trinomial` | Factor `x²+bx+c` or `ax²+bx+c` into binomial product |
| d2 | `polynomial_multiply` | Expand `(linear)(quadratic)` or `(linear)(linear with exponents)` |
| d2 | `add_subtract_polynomials` | Add or subtract two polynomial expressions (degree 2–3) |
| d2 | `exponent_rules` | Product rule, power-of-power, negative exponent simplification |
| d2 | `factor_polynomial_medium` | Factor polynomial by grouping or complex GCF (medium difficulty) |
| d3 | `factor_to_reveal_property` | Identify which equivalent form displays max/min as constant → complete the square |
| d3 | `rational_expression_add` | Add rational expressions with polynomial denominators |
| d3 | `polynomial_factor_with_constant` | Find integer `k` in factored quadratic; or identify which expression is a factor |
| d3 | `polynomial_coefficient_find` | Expand polynomial product; identify coefficient of specific term |
| d3 | `exponent_equation_solve` | Solve `p^(3n−1)=t^(8/3)` type — rational exponent equation |

#### EXP Variant Mapping (✅ implemented — `equiv_expr.py`)

| d | Template | Variants |
|---|---|---|
| d1 | `combine_like_terms` | `distribute_first`, `pure_collect` |
| d1 | `factor_gcf` | `monomial_gcf`, `binomial_gcf` |
| d1 | `rational_exponent_radical` | `radical_to_exp`, `exp_to_radical` |
| d1 | `factor_trinomial` | `monic`, `non_monic` |
| d2 | `polynomial_multiply` | `linear_linear`, `linear_quadratic` |
| d2 | `add_subtract_polynomials` | `add_type`, `subtract_type` |
| d2 | `exponent_rules` | `product_rule`, `power_rule`, `negative_exp` |
| d2 | `factor_polynomial_medium` | `grouping`, `complex_gcf` |
| d3 | `factor_to_reveal_property` | `complete_square` |
| d3 | `rational_expression_add` | `poly_denom` |
| d3 | `polynomial_factor_with_constant` | `find_k`, `identify_factor` |
| d3 | `polynomial_coefficient_find` | `specific_term`, `compare_forms` |
| d3 | `exponent_equation_solve` | `rational_exp`, `solve_for_var` |

**Totals:** d1 → 4 templates / 8 variants · d2 → 4 / 9 · d3 → 5 / 8 = **13 templates · 25 variants**

### NLF — 31 templates

**Function types observed:** quadratic, exponential (a·bˣ), radical (√x±c), rational (1/kx), absolute value, cubic, piecewise.

**Three additional templates added 2026-04-23 (not from Bluebook screenshots — added by design decision):**
- `function_composition` — covers f(g(x)) which Bluebook tests but was not in the original 28-template inventory
- `inequality_system_nonlinear` — covers systems where at least one boundary is nonlinear (parabola inequality); decided to place in NLF rather than LIN
- `piecewise_read_value` — piecewise functions observed in Bluebook function-type list; added as d1 template with formula-read and graph-read variants

| d | Template | Description |
|---|---|---|
| d1 | `evaluate_polynomial` | f(x)=ax² or x³+c; evaluate at integer x |
| d1 | `evaluate_exponential` | f(x)=a·bˣ; evaluate at x=0 or small integer |
| d1 | `evaluate_other_nonlinear` | f(x)=1/(kx), √x+c, or \|x+c\|; evaluate at given x |
| d1 | `interpret_y_intercept_context` | Exponential model f(0)=v; what does this mean in real-world context? |
| d1 | `y_intercept_from_graph` | Exponential/radical/log curve shown; identify y-intercept as ordered pair |
| d1 | `vertex_from_graph` | Parabola shown; read minimum or maximum vertex |
| d1 | `graph_translation` | Graph of f shown; identify graph of f+k (shifted up/down k units) |
| d2 | `evaluate_exponential_zero` | f(x)=a·(0.1)ˣ; evaluate at x=0 (tests b⁰=1 understanding) |
| d2 | `interpret_exponential_statement` | f(x)=65(1.03)ˣ; what does "f(8)≈82" mean in context? |
| d2 | `minimum_from_vertex_form` | g(x)=x²+k or a(x−h)²+k; state the minimum value |
| d2 | `x_for_min_from_factored` | f(x)=(x−r)(x−s); find x for minimum = midpoint of roots |
| d2 | `interpret_x_intercept_context` | Quadratic model; interpret x-intercept (hits ground / break-even) |
| d2 | `exponential_from_table` | Which equation matches given (x, f(x)) table? |
| d2 | `identify_quadratic_from_table` | Table of (x, f(x)); identify correct quadratic equation |
| d2 | `exponential_growth_rate` | f(x)=a(1.06)^(x/12); interpret growth rate percentage |
| d2 | `function_table_shift` | Given f(x) table, find table for y=f(x)−3 |
| d2 | `graph_read_intercept_nonlinear` | Graph of radical/log function shown; what is the y-intercept? |
| d2 | `function_composition` | Given f(x) and g(x) as simple formulas, compute f(g(a)) at a specific integer value |
| d2 | `inequality_system_nonlinear` | Which ordered pair (x,y) satisfies both a linear inequality and y < ax²+bx+c (or y > …)? |
| d3 | `max_in_context` | f(x)=ax²+bx+c (a<0); at what x is the maximum? Uses axis of symmetry x=−b/2a |
| d3 | `compound_function_max` | g(t)=f(t)+k; find maximum of g using vertex of f |
| d3 | `vertex_from_zeros` | f(r₁)=f(r₂)=0; find x-coordinate of vertex = (r₁+r₂)/2 |
| d3 | `identify_equivalent_form` | f(x) in standard form; which of 4 forms reveals max/min as a constant? |
| d3 | `exponential_two_points` | h(x)=aˣ+b passes through 2 points; find parameter value or product |
| d3 | `quadratic_parameter_properties` | f(x)=ax²+bx+c; given symmetry constraints, which statements must be true? |
| d3 | `exponential_reparameterize` | Convert f(t)=a·bᵗ to different time base; e.g. monthly → yearly |
| d3 | `count_zeros_graph` | From graph or analysis of f(x)=ab^x+c; how many x-intercepts exist? |
| d3 | `minimum_completing_square` | f(x)=x²+bx+c; find minimum by completing the square |
| d3 | `projectile_symmetry` | Quadratic projectile; find time to return to height h using parabola symmetry |
| d3 | `model_setup_quadratic` | Word problem → write quadratic equation representing the situation |

#### NLF Variant Mapping (🔜 planned — `nonlinear_fn.py`)

📊 = requires diagram renderer (parabola / exponential curve SVG)

**d1 — 8 templates · 13 variants**

| Template | Variants |
|---|---|
| `evaluate_polynomial` | `find_output` |
| `evaluate_exponential` | `find_output` |
| `evaluate_other_nonlinear` | `find_radical_output`, `find_rational_output`, `find_absolute_value_output` |
| `interpret_y_intercept_context` | `interpret_initial_value` |
| `y_intercept_from_graph` 📊 | `identify_ordered_pair` |
| `vertex_from_graph` 📊 | `find_minimum`, `find_maximum` |
| `graph_translation` 📊 | `identify_shifted_graph`, `find_output_after_shift` |
| `piecewise_read_value` | `find_output_formula`, `find_output_graph` 📊 |

**d2 — 12 templates · 23 variants**

| Template | Variants |
|---|---|
| `evaluate_exponential_zero` | `find_initial_value`, `interpret_initial_value` |
| `interpret_exponential_statement` | `interpret_output_value`, `interpret_growth_factor` |
| `minimum_from_vertex_form` | `find_minimum_value`, `find_x_at_minimum` |
| `x_for_min_from_factored` | `find_x_at_minimum` |
| `interpret_x_intercept_context` | `interpret_physical_meaning`, `identify_positive_zero` |
| `exponential_from_table` | `identify_equation_from_table`, `find_missing_table_value` |
| `identify_quadratic_from_table` | `identify_equation_from_table`, `find_missing_value` |
| `exponential_growth_rate` | `find_growth_percentage`, `interpret_growth_rate` |
| `function_table_shift` | `identify_transformed_table`, `find_specific_shifted_value` |
| `graph_read_intercept_nonlinear` 📊 | `find_y_intercept`, `find_x_intercept` |
| `function_composition` | `evaluate_f_of_g`, `evaluate_g_of_f` |
| `inequality_system_nonlinear` | `identify_satisfying_point`, `identify_satisfying_region` 📊 |

**d3 — 11 templates · 22 variants**

| Template | Variants |
|---|---|
| `max_in_context` | `find_x_at_max`, `find_max_value` |
| `compound_function_max` | `find_max_of_compound`, `find_shift_from_max` |
| `vertex_from_zeros` | `find_vertex_x`, `find_vertex_y` |
| `identify_equivalent_form` | `reveal_maximum`, `reveal_zeros` |
| `exponential_two_points` | `find_parameter_value`, `find_product_of_params` |
| `quadratic_parameter_properties` | `identify_true_statements`, `determine_sign_of_param` |
| `exponential_reparameterize` | `convert_time_base`, `find_percent_change` |
| `count_zeros_graph` | `count_x_intercepts`, `count_intersections` |
| `minimum_completing_square` | `find_minimum_value`, `find_x_at_minimum` |
| `projectile_symmetry` | `find_time_to_return`, `find_max_height` |
| `model_setup_quadratic` | `write_equation` (SPR), `identify_equation` (MCQ) |

**Totals:** d1 → 8 templates / 13 variants · d2 → 12 / 23 · d3 → 11 / 22 = **31 templates · 58 variants**

**New SVG renderers (built in Phase 3 alongside the generator):**
- `nonlinear_curve` — exponential y=a·bˣ and radical y=√(x+c)+d curves; used by `y_intercept_from_graph`, `graph_translation`, `graph_read_intercept_nonlinear`
- `piecewise_function` — 2-segment piecewise with open/closed endpoints; used by `piecewise_read_value/find_output_graph`
- `inequality_nonlinear` — parabola + line with shaded region; used by `inequality_system_nonlinear/identify_satisfying_region`
- `parabola` renderer already exists — reused for `vertex_from_graph`

### NLE — 22 templates

| d | Template | Description |
|---|---|---|
| d1 | `perfect_square_solve` | x²=k²; find positive solution → x=k |
| d1 | `factored_form_solve` | (x−a)(x+b)=0 already set up; zero product property |
| d1 | `absolute_value_easy` | \|x−c\|=d; find solutions |
| d1 | `system_from_graph` | Graph shows parabola + line; identify intersection point |
| d1 | `literal_equation` | Solve for one variable in terms of others (two or three linear variables) |
| d2 | `solve_by_factoring` | ax²+bx+c=0; factor and solve, state positive root |
| d2 | `solve_from_context_area` | Area/geometry word problem → quadratic → factor → positive root |
| d2 | `rational_equation_solve` | Solve a/(bx+c)=d; multiply and rearrange |
| d2 | `literal_equation_rational` | Solve for variable in rational or square-root form (multi-step) |
| d2 | `absolute_value_medium` | \|ax+b\|=−c (no solution) or \|x+c\|=d; find sum of solutions |
| d2 | `count_solutions_discriminant` | How many real solutions? Compute b²−4ac |
| d2 | `system_linear_quadratic_solve` | y=ax²+bx+c and y=mx+d; substitute and find x |
| d3 | `system_one_intersection` | Quadratic+linear system; exactly one intersection → find x-value or constant |
| d3 | `vieta_sum_of_roots` | ax²+bx+c=0 with unknown parameters; find sum of roots = −b/a (Vieta's) |
| d3 | `discriminant_no_solution` | x(kx−n)=−m; no real solution; find least integer k using b²−4ac<0 |
| d3 | `tangent_condition` | Find constant so line y=mx+b is tangent to parabola (discriminant=0) |
| d3 | `radical_equation_solve` | Square both sides, solve quadratic, verify no extraneous solutions |
| d3 | `literal_rearrangement_hard` | Multi-step: (14z)/(7y)=2√(w+19); solve for w → w=(z/y)²−19 |
| d3 | `count_distinct_zeros` | Count distinct x-intercepts of polynomial in factored form |
| d3 | `discriminant_constant_find` | Find constant c so quadratic has exactly one real solution |
| d3 | `sum_of_roots_cubic` | Cubic or quartic; find sum or product of roots from factored form |
| d3 | `greatest_intersection_x` | System of equations; find greatest x-value where they intersect |

#### NLE Variant Mapping (✅ implemented — `nonlinear_equations.py`)

| d | Template | Variants |
|---|---|---|
| d1 | `perfect_square_solve` | `spr_root`, `mcq_with_coeff` |
| d1 | `factored_form_solve` | `two_factors`, `three_factors` |
| d1 | `absolute_value_easy` | `find_positive`, `sum_of_solutions` |
| d1 | `system_from_graph` | `read_coordinates`, `count_intersections` |
| d1 | `literal_equation` | `two_var_linear`, `three_var_linear` |
| d2 | `solve_by_factoring` | `find_root`, `find_sum` |
| d2 | `solve_from_context_area` | `rectangle_area`, `projectile_context` |
| d2 | `rational_equation_solve` | `simple_rational`, `rational_with_quadratic` |
| d2 | `literal_equation_rational` | `rational_form`, `square_root_form` |
| d2 | `absolute_value_medium` | `find_sum`, `no_solution` |
| d2 | `count_solutions_discriminant` | `count_roots`, `find_k` |
| d2 | `system_linear_quadratic_solve` | `find_coordinates`, `find_y` |
| d3 | `system_one_intersection` | `find_k_in_quadratic`, `find_x` |
| d3 | `vieta_sum_of_roots` | `sum_of_roots`, `product_of_roots` |
| d3 | `discriminant_no_solution` | `least_integer_k`, `greatest_integer_b` |
| d3 | `tangent_condition` | `find_c`, `find_slope` |
| d3 | `radical_equation_solve` | `simple_radical`, `square_both_sides` |
| d3 | `literal_rearrangement_hard` | `solve_for_var` |
| d3 | `count_distinct_zeros` | `factored_form`, `identify_factor` |
| d3 | `discriminant_constant_find` | `find_constant` |
| d3 | `sum_of_roots_cubic` | `sum_of_roots`, `product_of_roots` |
| d3 | `greatest_intersection_x` | `greatest_x`, `find_y` |

**Totals:** d1 → 5 templates / 10 variants · d2 → 7 / 14 · d3 → 10 / 18 = **22 templates · 42 variants**

---

## Scale Estimate

| Skill | Templates | Variants | Status |
|---|---|---|---|
| EXP | 13 | 25 | ✅ Implemented |
| NLE | 22 | 42 | ✅ Implemented |
| NLF | 30 | 55 | 🔜 Planned |
| **Total** | **65** | **122** | |

**Algebra comparison:** 5 skills → 88 templates → 216 variants  
**Advanced Math:** 3 generators → 65 templates → 122 variants (≈ 57% of Algebra workload)

---

## Implementation Order + Status

1. ✅ **EXP** — 13 templates · 25 variants — implemented (`equiv_expr.py`), pipeline.html tested
2. ✅ **NLE** — 22 templates · 42 variants — implemented (`nonlinear_equations.py`), pipeline.html tested
3. 🔜 **NLF** — 30 templates · 55 variants — planned (`nonlinear_fn.py`); largest skill, most diverse function types

Per methodology: narration examples before generator code. All examples written and coverage table approved before Phase 2 (diagram renderers).
