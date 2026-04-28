# College Board SAT Framework → Template Cross-Check

**Source:** Assessment Framework for the Digital SAT Suite (Appendix B, Tables A34–A37)  
**URL:** https://satsuite.collegeboard.org/media/pdf/assessment-framework-for-digital-sat-suite.pdf  
**Scope:** Algebra + Advanced Math domains only  
**Date:** 2026-04-27  

Legend: ✅ Covered · ⚠️ Partial · ❌ Gap (new) · 🔗 Known gap (already in gaps.md)

---

## Domain 1: Algebra

### 1A. Linear equations in one variable (L1V)

| CB SKT | Status | Our template(s) | Notes |
|--------|--------|-----------------|-------|
| Create and use L1V eq to solve problems in context | ✅ | LWP skill handles this | Structural split intentional |
| Identify or create a L1V eq representing a context | 🔗 | — | A-17 `select_modeling_equation` |
| **Interpret a constant, variable, factor, term, or solution in context** | ❌ | — | L1V has NO interpret-in-context template. LFN covers functions; L1V covers raw equations (ax+b=c form). Different cognitive type. **NEW: A-23** |
| Solve a L1V making strategic use of algebraic structure | ✅ | `direct_solve_*`, `fractional_common_factor`, `isolate_expression`, `expression_as_unit` | |
| Determine conditions: no solution / unique / infinitely many | ⚠️ | `no_solution`, `infinite_solutions_*` cover "find the param"; classify-given-equation direction missing | A-12 |
| Fluently solve a L1V | ✅ | `direct_solve_one_step`, `direct_solve_two_step` | |

### 1B. Linear functions (LFN)

| CB SKT | Status | Our template(s) | Notes |
|--------|--------|-----------------|-------|
| Identify or create a linear fn to model a relationship | ✅ | `word_equation_simple`, `match_graph_to_equation_table` | |
| Interpret input/output pair, constant, variable, factor, term in context (incl. structure advantage) | ✅ | `interpret_slope_*`, `interpret_intercept_*`, `interpret_x_intercept`, `interpret_shift_or_coeff` | |
| Interpret the graph of a linear function in context | ✅ | `graph_read_intercept`, `graph_intercept_computed`, `graph_read_context` | |
| Make connections table/algebraic/graph NOT in context | ✅ | `match_graph_to_equation_table`, `coefficient_from_table`, `parameter_solve_simple` | |
| Make connections table/algebraic/graph IN context | ✅ | `linear_model_word_solve`, `linear_model_three_pts_hard` | |
| Given input find output / given output find input | ✅ | `evaluate_integer`, `evaluate_fraction`, `inverse_evaluate_easy` | |
| Write rule for linear fn given two input/output pairs or one pair + rate | ✅ | `equation_from_two_pts`, `parameter_solve_simple`, `coefficient_from_table` | |
| Evaluate linear fn / find input for output | ✅ | `evaluate_integer`, `evaluate_fraction` | |

### 1C. Linear equations in two variables (L2V)

| CB SKT | Status | Our template(s) | Notes |
|--------|--------|-----------------|-------|
| Identify or create L2V eq to model constraint | ✅ | `write_equation_*`, `table_to_equation` | |
| Interpret solution, constant, variable, factor, term in context (incl. structure advantage) | ⚠️ | `interpret_slope_in_context`, `interpret_intercept_in_context`, `interpret_term_in_context` | Coefficient-difference interpretation missing — A-15 |
| Interpret graph of Ax+By=C in context | ⚠️ | `slope_from_standard_form` (not in context), `find_y_intercept_std` | **No template reads Ax+By=C graph IN a real-world context. NEW: A-24** |
| Make connections algebraic ↔ graph NOT in context | ✅ | `match_graph_to_equation`, `read_slope`, `read_y_intercept`, `parallel_slope` | |
| Make connections table ↔ algebraic/graph NOT in context | ✅ | `table_to_equation`, `slope_from_table`, `match_equation_to_table` | |
| Make connections table/algebraic/graph IN context | ✅ | `word_problem_rate_model`, `word_problem_hard` | |
| Given value of one quantity find the other | ✅ | `find_x_intercept_standard_form`, `find_y_intercept_std` | |
| Write eq for line: two points / one point + slope / parallel or perpendicular | ✅ | `write_equation_two_points`, `write_equation_slope_point`, `parallel_from_standard_form`, `perpendicular_slope` | |

### 1D. Systems of two linear equations in two variables (SLE)

| CB SKT | Status | Our template(s) | Notes |
|--------|--------|-----------------|-------|
| Identify or create system to model constraints | ✅ | `word_problem_easy`, `word_problem_medium` | |
| Solve system making strategic use of algebraic structure | ✅ | `substitution_solve`, `linear_combination_trick`, `direct_substitution`, `sum_difference` | |
| Determine conditions: no / unique / infinitely many solutions | ⚠️ | `no_solution_find_param`, `no_solution_identify`, `infinite_find_constant` | A-13 (parametric point) + A-14 (unique intersection find constant) still open |
| Make connections algebraic ↔ graph NOT in context | ✅ | `graph_reading` | |
| **Make connections algebraic ↔ graph IN context** | ❌ | — | CB requires interpreting a system's graph in a real-world scenario (e.g., "the point of intersection represents when cost equals revenue"). No template exists. **NEW: A-25** |
| Fluently solve system | ✅ | `direct_substitution`, `sum_difference`, `solve_find_expression` | |

### 1E. Linear inequalities in one or two variables (LIN)

| CB SKT | Status | Our template(s) | Notes |
|--------|--------|-----------------|-------|
| Identify or create linear inequalities to model constraints | ✅ | `write_inequality_easy`, `write_inequality_medium` | |
| Interpret constant, variable, factor, term, solution | ✅ | `interpret_term` | |
| Interpret a point in xy-plane in terms of solution set | ✅ | `point_satisfies`, `system_quadrant` | |
| **Make connections tabular/algebraic/graphical** | ❌ | — | Graphical→algebraic: A-11 (`graph_to_inequality`). Tabular→algebraic (given a table of (x,y) pairs, write the inequality): also missing. **A-11 covers graph direction; tabular direction is NEW: A-26** |

---

## Domain 2: Advanced Math

### 2A. Equivalent expressions (EXP)

| CB SKT | Status | Our template(s) | Notes |
|--------|--------|-----------------|-------|
| Factor: common factor, difference of two squares, trinomials | ⚠️ | `factor_gcf`, `factor_polynomial_medium` | Difference of two squares not explicitly tested as a variant. **NEW: A-27** |
| Rational expressions, rational exponents, beyond-basic factoring (SAT only) | ✅ | `rational_expression_add`, `rational_exponent_radical`, `polynomial_factor_with_constant` | |
| Fluently add, subtract, multiply polynomials | ✅ | `add_subtract_polynomials`, `polynomial_multiply`, `combine_like_terms` | |

### 2B. Nonlinear equations in one variable and systems (NLE)

| CB SKT | Status | Our template(s) | Notes |
|--------|--------|-----------------|-------|
| Solve quadratic eq (wide variety of forms) | ✅ | `solve_by_factoring`, `perfect_square_solve`, `factored_form_solve` | |
| Solve abs value, rational, radical equations (SAT+PSAT) | ✅ | `absolute_value_easy/medium`, `rational_equation_solve`, `radical_equation_solve` | |
| Solve polynomial in factored form (SAT only) | ✅ | `factored_form_solve · three_factors` | |
| Solve systems of linear and nonlinear equations | ✅ | `system_linear_quadratic_solve`, `system_one_intersection` | |
| Determine conditions: no / one / two real solutions | ✅ | `count_solutions_discriminant`, `discriminant_no_solution`, `discriminant_constant_find` | |
| **Relate solutions of linear+nonlinear system to graphs** | ⚠️ | `greatest_intersection_x` only | CB tests "how many intersection points does this system have and what do they mean?" more broadly. `greatest_intersection_x` only asks for the largest x. Partial. |
| Solve for variable of interest (others as parameters) | ✅ | `literal_equation_rational`, `literal_rearrangement_hard` | |
| **Fluently solve quadratic using completing the square** | ⚠️ | `perfect_square_solve` handles already-perfect form | CB specifies completing the square from standard ax²+bx+c form. No template starts from standard form and completes the square. **NEW: A-28** |

### 2C. Nonlinear functions (NLF)

| CB SKT | Status | Our template(s) | Notes |
|--------|--------|-----------------|-------|
| Identify or create quadratic/exponential function to model | ✅ | `model_setup_quadratic`, `exponential_from_table`, `identify_quadratic_from_table` | |
| Interpret input/output pair including intercept/initial value in context | ✅ | `interpret_y_intercept_context`, `evaluate_exponential_zero`, `interpret_x_intercept_context` | |
| Interpret constant, variable, factor, term in context | ✅ | `interpret_exponential_statement`, `exponential_growth_rate` | |
| **Interpret a point on the graph in context (not just intercepts)** | ⚠️ | `interpret_x_intercept_context` covers x-intercepts; y-intercept covered | Arbitrary non-intercept point interpretation in context missing. **NEW: A-29** |
| Interpret parts of graph OTHER than a point or intercept (SAT+PSAT) | ⚠️ | `quadratic_parameter_properties` partially | E.g., "over what interval is the function increasing?" — not covered as a template type |
| Make connections table/algebraic/graph NOT involving transformation, NOT in context | ✅ | `identify_quadratic_from_table`, `exponential_from_table` | |
| Make connections involving transformation, NOT in context (SAT+PSAT) | ✅ | `graph_translation`, `function_table_shift` | |
| Make connections quad/exp NOT involving transformation, IN context | ✅ | `exponential_growth_rate`, `model_setup_quadratic` | |
| **Make connections: polynomial/simple rational/other nonlinear IN context, or transformation IN context (SAT+PSAT)** | ❌ | — | Simple rational function connections in a real-world context entirely missing. Related to A-22 but broader (table→equation, graph→equation for rational fn in context). **NEW: A-30** |
| Determine most suitable form for quadratic key features | ✅ | `identify_equivalent_form · reveal_zeros / reveal_maximum` | |
| **Determine most suitable form for exponential key features (SAT+PSAT)** | ⚠️ | `exponential_reparameterize` changes time base | CB tests: given exponential, which equivalent form reveals the growth rate / half-life / doubling period? Different from time-base conversion. **NEW: A-31** |
| x-intercepts = zeros, f(0) = y-intercept; connections and context (SAT only) | ✅ | `count_zeros_graph`, `graph_read_intercept_nonlinear` | |
| Evaluate nonlinear fn / find input for quadratic | ✅ | `evaluate_polynomial`, `max_in_context`, `projectile_symmetry` | |
| For exp/poly/radical/rational: find input for output (SAT+PSAT) | ✅ | `evaluate_other_nonlinear` | |
| **Rational function with two unknown constants — find constant from conditions** | ❌ | — | A-22 (already in gaps.md) |

---

## Summary: New Gaps Found by CB Framework Cross-Check

| Gap ID | Domain | SKT | Template name | Priority |
|--------|--------|-----|---------------|----------|
| A-23 | Algebra / L1V | Interpret constant/variable/factor/term/solution in context for ax+b=c form equations | `interpret_solution_context_l1v` | 🟡 Medium |
| A-24 | Algebra / L2V | Interpret graph of Ax+By=C in a real-world context | `interpret_standard_form_graph_context` | 🟡 Medium |
| A-25 | Algebra / SLE | Make connections between system graph and context (intersection = real-world meaning) | `interpret_system_intersection_context` | 🟡 Medium |
| A-26 | Algebra / LIN | Tabular→algebraic: given table of (x,y) pairs, write or identify the inequality | `table_to_inequality` | 🟢 Low |
| A-27 | Adv Math / EXP | Difference of two squares factoring (a²−b² = (a+b)(a−b)) as explicit template | `factor_difference_of_squares` | 🟢 Low |
| A-28 | Adv Math / NLE | Complete the square from standard ax²+bx+c form (not already-perfect form) | `complete_the_square` | 🟡 Medium |
| A-29 | Adv Math / NLF | Interpret an arbitrary (non-intercept) point on a nonlinear function graph in context | `interpret_graph_point_context` | 🟡 Medium |
| A-30 | Adv Math / NLF | Simple rational function in context — table/algebraic/graph connections | `rational_fn_connections_context` | 🟡 Medium |
| A-31 | Adv Math / NLF | Identify which equivalent exponential form reveals a specific key feature (growth rate / doubling period / half-life) | `identify_exponential_form_feature` | 🟡 Medium |

**Already-known gaps confirmed by this cross-check:** A-11, A-12, A-13, A-14, A-15, A-17, A-22

---

## What This Cross-Check Tells Us

The CB framework cross-check found **9 new gaps** beyond what our Bluebook screenshot audits found. This is because:

1. The Bluebook screenshots are a sample (~350 questions across 8 tests). The CB framework is the authoritative spec of ALL cognitive types tested.
2. Some SKTs appear rarely in practice tests but are tested in the live item bank.
3. "Interpret in context" variants of structural templates (solve, graph, conditions) are systematically under-represented — we built the structural templates but didn't always add the "now interpret this in a real scenario" counterpart.
