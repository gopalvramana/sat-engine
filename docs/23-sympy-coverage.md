# SymPy Pipeline — Coverage Reference

Last updated: 2026-04-22  
Source of truth: `sat-engine/scripts/math_engine.py`

**Coverage: 29 topics · 22 diagram types (88%)**  
**Variant-driven: L1V (32 variants), L2V (41 variants), LIN (44 variants), SLE (30 variants), LFN (69 variants) — all fully tested.**

---

## Question Types & Difficulty Levels by Topic

All 28 topics implement **D1–D5** fully. D6–D7 are not implemented (fall back to D4 in the CLI).

| Topic | Code | Domain | D1 | D2 | D3 | D4 | D5 | SPR Difficulties |
|---|---|---|---|---|---|---|---|---|
| Linear equations (1 variable) | LEQ | Algebra | ✓ | ✓ | ✓ | ✓ | ✓ | D3 (30%), D4 (40%) |
| Linear equation word problems | LWP | Algebra | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Systems of linear equations | SLE | Algebra | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Linear functions | LFN | Algebra | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Linear equations (2 variables) | L2V | Algebra | ✓ | ✓ | ✓ | ✓ | ✓ | D5 (Type 9B) |
| Quadratic equations | QEQ | Algebra | ✓ | ✓ | ✓ | ✓ | ✓ | D4 (40%) |
| Linear inequalities | LIN | Algebra | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Absolute value | ABV | Algebra | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Percentages | PCT | Problem Solving & Data Analysis | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Ratios & rates | RAT | Problem Solving & Data Analysis | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Proportional relationships | PRP | Problem Solving & Data Analysis | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Statistics | STA | Problem Solving & Data Analysis | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Probability | PRB | Problem Solving & Data Analysis | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Two-way tables | TWT | Problem Solving & Data Analysis | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Scatterplot analysis | SCA | Problem Solving & Data Analysis | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Data analysis | DAT | Problem Solving & Data Analysis | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Pythagorean theorem | PYT | Geometry & Trigonometry | ✓ | ✓ | ✓ | ✓ | ✓ | D3 (40%), D4 (40%) |
| Area (2D shapes) | ARA | Geometry & Trigonometry | ✓ | ✓ | ✓ | ✓ | ✓ | D4 (40%) |
| Coordinate geometry | CGE | Geometry & Trigonometry | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Circles | CIR | Geometry & Trigonometry | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Volume (3D shapes) | VOL | Geometry & Trigonometry | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Plane geometry | PLG | Geometry & Trigonometry | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Special triangles | SPT | Geometry & Trigonometry | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Trigonometry | TRG | Geometry & Trigonometry | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Exponents & radicals | EXR | Advanced Math | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Polynomial operations | POL | Advanced Math | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Quadratic functions | QFN | Advanced Math | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Sequences & series | SEQ | Advanced Math | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Complex numbers | CMX | Advanced Math | ✓ | ✓ | ✓ | ✓ | ✓ | — |

**SPR** = Student-Produced Response (numeric grid-in). All other difficulties are MCQ (4 choices).  
Topics with no SPR column produce MCQ only at all difficulties.

---

## Variant System — Architecture Summary

Five skills (L1V, L2V, LIN, SLE, LFN) have been refactored to the full variant-driven architecture
(2026-04-22). All other skills use the older single-function design.

### What the variant system provides

| Feature | Before | After |
|---|---|---|
| Template isolation | One giant if/elif function | Standalone `_d1_*` / `_d2_*` / `_d3_*` functions |
| Variant enumeration | Internal `rng.choice(["v1","v2"])` hidden | Named variants in routing dict, exposed via API |
| Path A — exact | Not supported | `--template=T --variant=V` → exactly 1 question |
| Path B — exhaustive | Not supported | `--template=T` → 1 question per variant |
| Path C — batch | Supported | `--count=N` → random rotation |
| Java `listVariants()` | Not available | `GET /api/admin/sympy/variants?skill=S&difficulty=D[&template=T]` |
| pipeline.html dropdown | Not available | Variant dropdown auto-populated from API |
| Crash isolation | Bug in one branch → whole skill fails | Bug in one function → only that template fails |

### Variant counts by skill

| Skill | Code | d1 | d2 | d3 | Total variants |
|---|---|---|---|---|---|
| `linear_eq_one_var` | LEQ | 18 (9 tmpl × 2) | 8 (4 tmpl × 2) | 6 (3 tmpl × 2) | **32** |
| `linear_eq_two_var` | L2V | 13 (5 tmpl) | 16 (7 tmpl) | 12 (5 tmpl) | **41** |
| `linear_inequalities` | LIN | 13 (4 tmpl) | 15 (7 tmpl) | 16 (7 tmpl) | **44** |
| `systems_linear_eq` | SLE | 9 (4 tmpl) | 11 (5 tmpl) | 10 (4 tmpl) | **30** |
| `linear_functions` | LFN | 24 (8 tmpl) | 30 (11 tmpl) | 15 (5 tmpl) | **69** |

### How to query variants via the API

```
# All templates + variants at d2 for LEQ:
GET /api/admin/sympy/variants?skill=linear_eq_one_var&difficulty=2

# Variants for a specific template:
GET /api/admin/sympy/variants?skill=linear_inequalities&difficulty=3&template=complex_word
→ {"variants": ["two_price_revenue", "budget_min_total", "consecutive_evens"]}
```

### How to generate via pipeline.html

1. Select skill → template dropdown appears
2. Select template → variant dropdown appears (for L1V / L2V / LIN)
3. Select variant (or leave "All variants") → count auto-filled
   - Variant selected: count = 1 (Path A)
   - Template only: count = number of variants (Path B)
   - Neither: count field free-edit (Path C)

---

## Difficulty Progression by Topic

### Linear Equations — One Variable (LEQ) — 16 templates · 32 variants

Uses SAT 3-level taxonomy (d1=Easy, d2=Medium, d3=Hard). Each template has 2 named variants.

| d | Template | Variants | Cognitive Type |
|---|---|---|---|
| d1 | `direct_solve_one_step` | `small_coeff`, `large_coeff` | ax = c; solve for x |
| d1 | `direct_solve_two_step` | `pos_const`, `neg_const` | ax + b = c; positive or negative constant |
| d1 | `direct_solve_distribute` | `small_outer`, `large_outer` | a(bx + c) = d; distribute then solve |
| d1 | `find_expression_given_x` | `small_n`, `large_n` | Given x, evaluate nx + k |
| d1 | `find_expression_shift` | `small_b`, `large_b` | If ax = c, find ax + b |
| d1 | `find_expression_divide` | `small_k`, `large_k` | If ax + b = c, find x/k + b |
| d1 | `equivalent_equation` | `small_rhs`, `large_rhs` | Which form is equivalent to ax + b = c? |
| d1 | `infinite_solutions_simple` | `small_product`, `large_product` | n(ax + b) = cx + d; find n for infinitely many solutions |
| d1 | `reciprocal_expression` | `small_vals`, `large_vals` | If x + 1/x = k, find 3x + 3/x |
| d2 | `scale_simple` | `small_c`, `large_c` | cx/a = b; find x |
| d2 | `scale_compound` | `pos_b`, `neg_b` | (ax + b)/c = d; positive or negative b |
| d2 | `isolate_expression` | `pos_k`, `neg_k` | Solve for expression kx from ax + bx = c |
| d2 | `fractional_common_factor` | `mcq_type`, `spr_type` | ax/b + cx/b = d; factor out 1/b |
| d3 | `expression_as_unit` | `mcq_type`, `spr_type` | Treat (ax + b) as unit; solve for it |
| d3 | `infinite_solutions_complex` | `small_r`, `large_r` | (Ax+B)/C − s/D = r(x−E); find s |
| d3 | `no_solution` | `small_n`, `large_n` | n(ax+b) = cx+d; find n for no solution |

### Linear Equation Word Problems (LWP)
| D | Problem Type |
|---|---|
| D1 | Rate × quantity + fixed fee (e.g. phone bill) |
| D2 | Rate × quantity + fixed fee (wider range) |
| D3 | Two unknowns summing to total with given difference |
| D4 | Two different unit rates, total cost (mixture-style) |
| D5 | Two objects traveling at different speeds (d = st) |

### Systems of Linear Equations (SLE) — see full variant table below
13 named templates · 30 variants across 3 difficulty levels. Full variant table under "Systems of Linear Equations (SLE) — 13 templates · 30 variants".

### Linear Functions (LFN) — 24 templates · 69 variants

Uses SAT 3-level taxonomy (d1=Easy, d2=Medium, d3=Hard). Full variant-driven refactor complete 2026-04-22. Pipeline tested and all flags resolved.

| d | Template | Variants | Cognitive Type |
|---|---|---|---|
| d1 | `evaluate_integer` | `pos_input`, `neg_input`, `neg_slope`, `eval_at_zero`, `unit_coefficient` | Evaluate f(x)=mx+b at integer x |
| d1 | `evaluate_fraction` | `pos_frac`, `neg_frac`, `decimal_coeff` | Evaluate f(x) with fractional/decimal coefficient |
| d1 | `interpret_slope_easy` | `rate_per_unit`, `cost_per_item`, `decrease_rate` | Interpret slope as rate in real-world context |
| d1 | `interpret_intercept_easy` | `initial_value`, `starting_amount`, `constant_in_growth`, `find_y_intercept` | Interpret y-intercept as initial/fixed value |
| d1 | `graph_read_intercept` | `x_intercept`, `y_intercept`, `identify_y_coord` | Read intercept coordinates from coordinate plane |
| d1 | `word_equation_simple` | `flat_plus_rate`, `verbal_description`, `service_contract` | Identify linear equation from word description |
| d1 | `inverse_evaluate_easy` | `one_step`, `two_step` | Given f(x)=v, solve for x (1-step or 2-step) |
| d1 | `match_graph_to_equation_table` | `table_to_equation` | Match table of (x, f(x)) values to correct equation |
| d2 | `evaluate_compound` | `combine_two_fns`, `scaled_output`, `coefficient_gather`, `difference_single_fn`, `symbolic_input` | Evaluate compound or composite function expressions |
| d2 | `interpret_slope_medium` | `rate_in_formula`, `rate_from_graph`, `gas_tank_rate` | Interpret slope in applied linear model |
| d2 | `interpret_intercept_medium` | `juice_volume`, `fabric_relation` | Interpret y-intercept in real-world model |
| d2 | `interpret_x_intercept` | `time_zero_context`, `break_even_context` | Interpret x-intercept (break-even point, time=0) |
| d2 | `equation_from_two_pts` | `integer_slope`, `larger_slope`, `from_slope_and_point`, `negative_slope_decreasing` | Write equation from two points or point + slope |
| d2 | `coefficient_from_table` | `find_m`, `find_b`, `two_unknowns` | Find m or b from a table of (x, f(x)) values |
| d2 | `parameter_solve_simple` | `solve_m`, `solve_b`, `inverse_then_solve` | Solve for m or b given f(x)=v and a constraint |
| d2 | `linear_model_word_solve` | `forward_interp`, `specific_input`, `acceleration_like`, `savings_balance` | Evaluate applied linear model at a specific input |
| d2 | `graph_intercept_computed` | `sum_of_intercepts`, `intercept_after_shift` | Compute intercept algebraically from shifted/combined line |
| d2 | `parallel_slope_from_fn` | `parallel_to_linear_fn` | Find slope of a line parallel to the graph of f |
| d2 | `arithmetic_nth_term` | `forward` | Arithmetic sequence as linear model; find nth term |
| d3 | `parameter_solve_compound` | `double_param`, `expr_input`, `implicit_b`, `table_derived` | Solve for unknown parameter from compound constraints |
| d3 | `word_model_multistep` | `flat_plus_daily`, `tiered_rate`, `coverage_double` | Multi-step real-world linear model application |
| d3 | `linear_model_three_pts_hard` | `interpolate`, `extrapolate`, `window_repair` | Build model from 3 data points; interpolate or extrapolate |
| d3 | `literal_formula_solve` | `isolate_var`, `kelvin_inverse` | Solve literal equation for one variable |
| d3 | `interpret_shift_or_coeff` | `signed_change`, `abs_change`, `coefficient_from_growth` | Interpret parameter change in transformed model |

### Linear Equations — Two Variables (L2V) — 17 templates · 41 variants

Uses SAT 3-level taxonomy (d1=Easy, d2=Medium, d3=Hard). Full variant-driven refactor complete 2026-04-21.

| d | Template | Variants | Cognitive Type |
|---|---|---|---|
| d1 | `read_slope` | `pos_slope`, `neg_slope` | T2a — read slope from y=mx+b |
| d1 | `read_y_intercept` | `pos_intercept`, `neg_intercept`, `zero_intercept` | T2b/T7a — read y-intercept from y=mx+b |
| d1 | `match_graph_to_equation` | `pos_slope`, `neg_slope`, `zero_slope` | T8 — identify y-intercept as ordered pair from graph |
| d1 | `parallel_slope` | `pos_slope`, `neg_slope` | T5a (d1) — matching parallel slope from y=mx+b |
| d1 | `parallel_from_standard_form` | `neg_int_slope`, `neg_slope_3`, `unit_slope`, `large_neg` | T5a (std form) — Ax+By=C; parallel slope = −A/B |
| d2 | `slope_from_two_points` | `pos_slope`, `neg_slope`, `unit_slope` | T2c — (y₂−y₁)/(x₂−x₁) |
| d2 | `perpendicular_slope` | `pos_original`, `neg_original` | T5a — slope of perpendicular = −1/m |
| d2 | `slope_from_standard_form` | `proper_frac`, `improper_frac` | T2d — Ax+By=C → slope −A/B |
| d2 | `find_y_intercept_std` | `small_intercept`, `large_intercept` | T7b — Ax+By=C → y-intercept C/B |
| d2 | `match_graph_to_equation` | `pos_slope`, `neg_slope` | T8 — identify slope-intercept equation from graph |
| d2 | `parallel_slope` | `pos_slope`, `neg_slope` | T5a (d2) — parallel slope from y=mx+b (larger numbers) |
| d2 | `parallel_from_standard_form` | `proper_frac`, `improper_frac`, `large_num`, `small_denom` | T5a — std form parallel; negative fractional slope |
| d3 | `function_shift` | `shift_up`, `shift_down` | T9A — graph of y=f(x)+k; identify f(x) |
| d3 | `translate_intercept` | `positive_intercept`, `negative_intercept` | T9B — Ax−By=C translated down k; find x-intercept (SPR) |
| d3 | `slope_complex_expr` | `pos_slope`, `neg_slope` | T2e — simplify (1/q)(ax+b)+cx to find slope |
| d3 | `match_graph_to_equation` | `pos_R`, `neg_R` | T8 — standard form with unknown R; which eq has R>0 |
| d3 | `parallel_from_standard_form` | `proper_frac`, `improper_frac`, `large_neg_num`, `small_denom` | T5a — std form parallel (hardest coefficients) |

**Remaining phases (from `docs/24-linear-eq-two-var-analysis.md`):**
- Phase 3: T7 — x-intercept from standard form (d2) + y-intercept from slope+point (d3)
- Phase 4: T6 — Write equation from slope+point / two points
- Phase 5: T5 — Parallel slope + full parallel/perp equation
- Phase 6: T4 — Interpret coefficient/intercept in context
- Phase 7: T3 — Match table ↔ equation
- Phase 8: T2 — Remaining slope sub-types (table, graph-read)
- Phase 9: T1 — Word problems (34% of Bluebook — biggest category)

Full design reference: `docs/24-linear-eq-two-var-analysis.md`

### Systems of Linear Equations (SLE) — 13 templates · 30 variants

Uses SAT 3-level taxonomy (d1=Easy, d2=Medium, d3=Hard). Full variant-driven refactor complete 2026-04-21.

| d | Template | Variants | Cognitive Type |
|---|---|---|---|
| d1 | `direct_substitution` | `x_given`, `y_expr`, `ratio_sub` | Substitute a given value; ask x or y |
| d1 | `sum_difference` | `sum_seq`, `diff_direct` | Given sum+difference equations; find x+y or x−y |
| d1 | `graph_reading` | `find_pair`, `find_x` | Two lines on graph; read intersection (x,y) or just x |
| d1 | `word_problem_easy` | `ratio_total`, `additive_total` | Model with system; choose correct equation pair |
| d2 | `substitution_solve` | `ask_x`, `ask_y` | Solve 2×2 system; ask for value of x or y |
| d2 | `solve_find_expression` | `both_pos_vars`, `mixed_sign_vars` | Solve system; evaluate px + qy |
| d2 | `no_solution_identify` | `small_k`, `large_k` | Which of four systems has no solution? |
| d2 | `infinite_find_constant` | `pos_constant`, `neg_constant` | Find k so system has infinitely many solutions |
| d2 | `word_problem_medium` | `pricing`, `speed_time`, `vote_count` | Mixture/pricing/speed/vote word problem |
| d3 | `no_solution_find_param` | `mcq_type`, `spr_type` | Find k so Ax + ky = C has no solution with other equation |
| d3 | `word_problem_hard` | `total_and_multiple`, `two_prices`, `length_split` | Multi-step word problem; find specific quantity |
| d3 | `linear_combination_trick` | `add_both`, `subtract_eq2`, `scale_add` | Find px+qy directly by combining equations |
| d3 | `solve_find_xy_product` | `pos_product`, `neg_product` | Solve system; find x·y (positive or negative product) |

### Quadratic Equations (QEQ)
| D | Form | What is Asked |
|---|---|---|
| D1 | (x − r)² = 0 | Single root (perfect square) |
| D2 | x² + bx + c = 0 | Two positive integer roots |
| D3 | x² + bx + c = 0 | One positive, one negative root |
| D4 | ax² + bx + c = 0 (a > 1) | Positive root; 40% SPR |
| D5 | x² + bx + c = 0 | Product of roots (= c) |

### Linear Inequalities (LIN) — 18 templates · 44 variants

Uses SAT 3-level taxonomy (d1=Easy, d2=Medium, d3=Hard). Full variant-driven refactor complete 2026-04-21. No diagrams — all text-based.

| d | Template | Variants | Cognitive Type |
|---|---|---|---|
| d1 | `one_var_word_bound` | `min_additional`, `max_additional`, `packs_spr` | Word problem: need ≥/≤ goal; packs round-up (SPR) |
| d1 | `compound_range` | `direct`, `scaled` | a ≤ v ≤ b; direct or scaled variable |
| d1 | `write_inequality_easy` | `total_cap`, `rate_constraint`, `budget`, `fee_plus_hourly` | Write inequality from real-world scenario |
| d1 | `system_quadrant` | `q1`, `q2`, `q3`, `q4` | Which system x>0/x<0, y>0/y<0 contains a given point? |
| d2 | `compound_range_scaled` | `scale_units`, `threshold_select` | Scaled compound range or threshold filter |
| d2 | `write_inequality_medium` | `perimeter`, `system_two`, `capacity_minus` | Write inequality for perimeter/system/capacity scenarios |
| d2 | `solve_one_var` | `mcq_type`, `spr_type` | Greatest-integer-satisfying budget problem |
| d2 | `point_satisfies` | `less_than`, `greater_than` | Which (x,y) satisfies y < mx+b or y > mx+b? |
| d2 | `two_var_bound` | `mcq_type`, `spr_type` | x ≤ my − k word problem; positive y |
| d2 | `system_solve_x` | `coeff_small`, `coeff_large` | System y > L; ax + y < R; find max x given y |
| d2 | `table_satisfies` | `strict_less`, `strict_greater` | Which table has all rows satisfying strict inequality? |
| d3 | `compound_range_algebraic` | `commission`, `triangle` | Algebraic compound range from commission or triangle rules |
| d3 | `solve_one_var_tax` | `small_n`, `large_n` | Max unit price under budget including sales tax |
| d3 | `two_var_bound_neg` | `mcq_type`, `spr_type` | x ≤ my − k with negative y value |
| d3 | `system_pair` | `pos_a`, `neg_a` | Which (x,y) satisfies both y ≤ ax+b and y ≥ cx+d? |
| d3 | `table_satisfies_twovar` | `small_coeff`, `large_coeff` | Which table satisfies ax − y > K (large K)? |
| d3 | `interpret_term` | `item_ab`, `type_ab`, `option_12` | What does p₂b represent in p₁a + p₂b ≤ cap? |
| d3 | `complex_word` | `two_price_revenue`, `budget_min_total`, `consecutive_evens` | Multi-constraint word problem or consecutive-integer inequality |

### Absolute Value (ABV)
| D | Problem Type |
|---|---|
| D1 | \|x\| = a (single solution) |
| D2 | \|ax + b\| = c (two solutions) |
| D3 | \|ax + b\| < c (compound inequality) |
| D4 | \|ax + b\| > c (disjoint inequality) |
| D5 | Word problem with absolute value constraint |

### Percentages (PCT)
| D | Problem Type |
|---|---|
| D1 | Find p% of n (clean percentages) |
| D2 | Find what percent part is of whole |
| D3 | Percent change (increase or decrease) |
| D4 | Find original value given final and percent increase |
| D5 | Compound percent changes (two sequential %) |

### Ratios & Rates (RAT)
| D | Problem Type |
|---|---|
| D1 | Divide total in ratio a:b |
| D2 | Unit rate (n items → m items cost) |
| D3 | Divide total in 3-part ratio a:b:c |
| D4 | Distance / speed / time (find t) |
| D5 | Average speed (two legs at different speeds) |

### Proportional Relationships (PRP)
| D | Problem Type |
|---|---|
| D1 | Given k and x, find y = kx |
| D2 | Given (x₁,y₁) and x₂, find y₂ |
| D3 | Fractional constant y = (a/b)x |
| D4 | Reverse: given k and y, find x |
| D5 | Table with missing value (4 data points) |

### Statistics (STA)
| D | What is Asked | Diagram |
|---|---|---|
| D1 | Mean of a data set | — |
| D2 | Median of a data set | — |
| D3 | Mode and range | — |
| D4 | IQR (Q3 − Q1) | box_plot |
| D5 | Standard deviation (conceptual) | — |

### Probability (PRB)
| D | Problem Type |
|---|---|
| D1 | Simple probability P(A) = favorable/total |
| D2 | Complement probability P(not A) = 1 − P(A) |
| D3 | Two independent events P(A and B) |
| D4 | Conditional probability P(A\|B) |
| D5 | At-least-one probability using complement |

### Two-Way Tables (TWT)
| D | What is Asked | Diagram |
|---|---|---|
| D1 | Joint frequency (read a single cell) | two_way_table |
| D2 | Marginal frequency (row/column total) | two_way_table |
| D3 | Conditional frequency (given row or column) | two_way_table |
| D4 | Missing cell (total − known cells) | two_way_table |
| D5 | Conditional probability from table | two_way_table |

### Scatterplot Analysis (SCA)
| D | What is Asked | Diagram |
|---|---|---|
| D1 | Read a value from the scatter plot | scatter_plot |
| D2 | Identify positive/negative association | scatter_plot |
| D3 | Use line of best fit to predict a value | scatter_plot |
| D4 | Interpret slope of line of best fit | scatter_plot |
| D5 | Identify outlier or residual | scatter_plot |

### Data Analysis (DAT)
| D | Chart Type | What is Asked |
|---|---|---|
| D1 | Bar chart | Read a specific bar value |
| D2 | Bar chart | Max − min difference |
| D3 | Pie chart | Convert % to count (count = total × pct / 100) |
| D4 | Bar chart (missing bar) | Find missing value (missing = total − known) |
| D5 | Bar chart | Calculate one category as % of total |

### Pythagorean Theorem (PYT)
| D | Form | Diagram |
|---|---|---|
| D1 | Find hypotenuse (simple triple) | right_triangle (hyp = ?) |
| D2 | Find leg (simple triple) | right_triangle (leg = ?) |
| D3 | Find hypotenuse (scaled triple); 40% SPR | right_triangle (hyp = ?) |
| D4 | Find hypotenuse (scaled triple); 40% SPR | right_triangle (hyp = ?) |
| D5 | Find area of triangle (leg + hypotenuse given) | right_triangle (leg = ?) |

### Area 2D (ARA)
| D | Shape | Diagram |
|---|---|---|
| D1 | Rectangle A = l × w | rectangle |
| D2 | Triangle A = ½bh | triangle |
| D3 | Composite L-shaped area | composite_rectangle |
| D4 | Rectangle — find missing width; 40% SPR | rectangle (w = ?) |
| D5 | Scaling — if dimensions scale by k, area scales by k² | scaled_rectangle |

### Coordinate Geometry (CGE)
| D | What is Asked | Diagram |
|---|---|---|
| D1 | Slope between two points | Coordinate plane + 2 points |
| D2 | X-coordinate of midpoint | Coordinate plane + midpoint |
| D3 | Distance between two points | Coordinate plane + 2 points |
| D4 | Missing endpoint given midpoint and one endpoint | Coordinate plane + highlight |
| D5 | Y-coordinate of third collinear point | Coordinate plane + 3 points + line |

### Circles (CIR)
| D | What is Asked | Diagram |
|---|---|---|
| D1 | Circumference given radius (C = 2πr) | circle (radius) |
| D2 | Area given radius (A = πr²) | circle (radius) |
| D3 | Circumference given diameter (C = πd) | circle (diameter) |
| D4 | Arc length of sector — answer as Nπ | circle + sector (angle θ) |
| D5 | Sector area — answer as Nπ | circle + sector (angle θ) |

### Volume 3D (VOL)
| D | Shape | Formula | Diagram |
|---|---|---|---|
| D1 | Rectangular prism | V = l·w·h | rectangular_prism |
| D2 | Cylinder | V = πr²h | cylinder |
| D3 | Cone | V = ⅓πr²h | cone |
| D4 | Sphere | V = 4/3 πr³ | sphere |
| D5 | Cylinder (find height) | V = πr²h → h = V/πr² | cylinder (h = ?) |

### Plane Geometry (PLG)
| D | Shape | What is Asked | Diagram |
|---|---|---|---|
| D1 | Parallelogram | Area = base × height | parallelogram |
| D2 | Trapezoid | Area = ½(b₁+b₂)h | trapezoid |
| D3 | Parallelogram | Find missing height | parallelogram (h = ?) |
| D4 | Trapezoid | Find missing height | trapezoid (h = ?) |
| D5 | House shape (rect + triangle) | Total composite area | house_shape |

### Special Triangles (SPT)
| D | Type | What is Asked | Diagram |
|---|---|---|---|
| D1 | 45-45-90 | Find hypotenuse given leg | special_triangle |
| D2 | 30-60-90 | Find long leg given short leg | special_triangle |
| D3 | 45-45-90 | Find leg given hypotenuse | special_triangle |
| D4 | 30-60-90 | Find hypotenuse given long leg | special_triangle |
| D5 | Mixed | Multi-step using triangle ratios | special_triangle |

### Trigonometry (TRG)
| D | What is Asked | Diagram |
|---|---|---|
| D1 | sin θ = opposite/hypotenuse | right_triangle (label_angle) |
| D2 | cos θ = adjacent/hypotenuse | right_triangle (label_angle) |
| D3 | tan θ = opposite/adjacent | right_triangle (label_angle) |
| D4 | Find missing side using SOHCAHTOA | right_triangle (label_angle) |
| D5 | Find angle given ratio (inverse trig conceptual) | right_triangle (label_angle) |

### Exponents & Radicals (EXR)
| D | Rule | What is Asked |
|---|---|---|
| D1 | Product rule: xᵃ · xᵇ = xᵃ⁺ᵇ | Simplify expression |
| D2 | Power of a power: (xᵃ)ᵇ = xᵃᵇ | Simplify expression |
| D3 | Simplify √(a·b²) | Extract perfect square factors |
| D4 | Rational exponents: x^(1/n) = ⁿ√x | Convert and evaluate |
| D5 | Negative exponents: x⁻ⁿ = 1/xⁿ | Simplify expression |

### Polynomial Operations (POL)
| D | Operation | What is Asked |
|---|---|---|
| D1 | FOIL: (x + a)(x + b) | Expand to standard form |
| D2 | Factor: x² + bx + c | Find factors |
| D3 | Evaluate: p(a) for given a | Substitute and compute |
| D4 | Add/subtract polynomials | Combine like terms |
| D5 | Divide: (x² + bx + c) ÷ (x + a) | Polynomial long division |

### Quadratic Functions (QFN)
| D | Form | What is Asked | Diagram |
|---|---|---|---|
| D1 | f(x) = (x − h)² + k | Identify vertex | parabola |
| D2 | f(x) = a(x − h)² + k | Min/max value | parabola |
| D3 | f(x) = (x − h)² + k | Minimum value of function | parabola |
| D4 | f(x) = ax² + bx + c | Axis of symmetry x = −b/2a | parabola |
| D5 | f(x) = a(x − h)² + k | Interpret transformation | parabola |

### Sequences & Series (SEQ)
| D | Type | What is Asked |
|---|---|---|
| D1 | Arithmetic: nth term = a + (n−1)d | Find nth term |
| D2 | Geometric: nth term = a · rⁿ⁻¹ | Find nth term |
| D3 | Arithmetic series | Sum of first n terms |
| D4 | Geometric series | Sum of finite geometric series |
| D5 | Mixed | Identify sequence type and find term |

### Complex Numbers (CMX)
| D | Operation | What is Asked |
|---|---|---|
| D1 | Add/subtract complex numbers | Combine real and imaginary parts |
| D2 | Multiply: (a + bi)(c + di) | Expand using i² = −1 |
| D3 | Powers of i (i¹ through i⁴ cycle) | Evaluate iⁿ |
| D4 | Modulus: \|a + bi\| = √(a² + b²) | Find absolute value |
| D5 | Divide: (a + bi)/(c + di) | Multiply by conjugate |

---

## Diagram Types

| Diagram Type | Topics | Notes |
|---|---|---|
| `coordinate_plane` | LFN (D1–D5), CGE (D1–D5), SLE d1 `graph_reading` | Function line, data points, highlight_point, hideLabel flag; SLE uses `lines[]` multi-line format |
| `right_triangle` | PYT (D1–D5), TRG (D1–D5) | Legs and hypotenuse; missing value shown as "?"; label_angle for trig |
| `special_triangle` | SPT (D1–D5) | 30-60-90 or 45-45-90 with angle arcs and labeled sides |
| `rectangle` | ARA (D1, D4) | Length × width; D4 has width = "?" |
| `triangle` | ARA (D2) | Base and height with dashed altitude |
| `composite_rectangle` | ARA (D3) | L-shaped figure with labeled sub-dimensions |
| `scaled_rectangle` | ARA (D5) | Two rectangles with scale arrow (× k) |
| `circle` | CIR (D1–D5) | D1–D3: radius or diameter; D4–D5: sector with angle θ |
| `parallelogram` | PLG (D1, D3) | Height shown as dashed vertical line inside shape |
| `trapezoid` | PLG (D2, D4) | Both parallel sides and dashed height labeled |
| `house_shape` | PLG (D5) | Rectangle + triangle composite |
| `rectangular_prism` | VOL (D1) | Isometric 3D box with l, w, h labels |
| `cylinder` | VOL (D2, D5) | Top ellipse with radius; side with height |
| `cone` | VOL (D3) | Dashed altitude and base radius labeled |
| `sphere` | VOL (D4) | Dashed equator + dashed radius line |
| `bar_chart` | DAT (D1, D2, D4, D5) | D4: one bar shown as "?" with dashed outline |
| `pie_chart` | DAT (D3) | Color-coded segments with legend + total |
| `number_line` | LIN (D1–D5), ABV (D3–D4) | Open/closed points, shading arrows for inequality direction |
| `scatter_plot` | SCA (D1–D5) | Data points + dashed line of best fit; auto-scaled axes |
| `box_plot` | STA (D4) | Whiskers, IQR box, median line, Q1/Med/Q3 labels |
| `two_way_table` | TWT (D1–D5) | Header row, row labels, highlight support for target cell |
| `parabola` | QFN (D1–D5) | Dynamic scaling, vertex dot + label, dashed axis of symmetry, optional roots |

**No diagram:** LEQ, LWP, QEQ, PCT, RAT, PRP, ABV (D1–D2), STA (D1–D3, D5), PRB, EXR, POL, SEQ, CMX  
**SLE:** diagram only for `graph_reading` (d1); all other SLE templates are text-only.

---

## Known Gaps (Low Priority)

| Item | Notes |
|---|---|
| Conic sections (ellipse, hyperbola) | Not on most SAT tests; parabolas covered via QFN |
| Histogram diagram | Would require a frequency-distribution statistics sub-type |
| Unit circle diagram | Full trig unit circle; current TRG uses right_triangle |
| Compound bar / stacked bar | Multi-variable data analysis not yet modeled |
| Systems of linear inequalities | Compound constraint problems |
| Inference / margin of error | Statistical sampling questions |
