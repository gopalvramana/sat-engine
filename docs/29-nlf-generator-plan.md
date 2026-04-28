# NLF Generator Plan — `nonlinear_fn.py`

**Status:** APPROVED, NOT YET IMPLEMENTED  
**Skill key:** `nonlinear_functions`  
**Narration examples:** `src/main/resources/narration/examples/nonlinear_functions.json` — 70 examples · 50 variants (9 synthetic examples removed: 3 piecewise, 3 function_composition, 3 inequality_system_nonlinear — no Bluebook backing)

---

## File location and registration

| Item | Detail |
|---|---|
| New file | `scripts/math_skills/nonlinear_fn.py` |
| Import in `math_engine.py` | `from math_skills.nonlinear_fn import gen_nonlinear_fn, nlf_variants` |
| Java wiring `SymPyGenerateStage.java` | 3 map entries: domain=`advanced_math`, display=`Nonlinear functions`, code=`NLF` |
| Pipeline test UI | Add `nonlinear_functions` key to `SKILL_TEMPLATES` in `pipeline.html` |

---

## File structure (mirrors `nonlinear_equations.py`)

```
imports
format helpers   (_poly_str, _exp_str, _lat, _frac_str)
result helper    (_nlf_result)

28 template functions  (_d1_* × 7, _d2_* × 10, _d3_* × 11)

_D1 = {7 templates}
_D2 = {10 templates}
_D3 = {11 templates}
_ROUTING = {1: _D1, 2: _D2, 3: _D3}

nlf_variants()        ← public metadata API
gen_nonlinear_fn()    ← main dispatcher
```

---

## D1 — 7 templates · 11 variants

| Template | Variants | BB anchor | Type |
|---|---|---|---|
| `evaluate_polynomial` | `find_output` | observed: evaluate f(x)=ax²+c or x³+c at given integer x | MCQ or SPR |
| `evaluate_exponential` | `find_output` | observed: evaluate a·bˣ at small non-negative x | MCQ or SPR |
| `evaluate_other_nonlinear` | `find_radical_output` | observed: evaluate √(x+c) at integer x | MCQ or SPR |
| | `find_rational_output` | observed: evaluate k/x at non-zero integer x | MCQ |
| | `find_absolute_value_output` | observed: evaluate \|x+c\| at integer x | MCQ or SPR |
| `interpret_y_intercept_context` | `interpret_initial_value` | observed: exponential model f(0)=v; which statement describes what v represents? | MCQ |
| `y_intercept_from_graph` 📊 | `identify_ordered_pair` | observed: curve shown; which ordered pair is the y-intercept? | MCQ |
| `vertex_from_graph` 📊 | `find_minimum` | observed: upward parabola shown; what is the minimum value? | MCQ or SPR |
| | `find_maximum` | observed: downward parabola shown; what is the maximum? | MCQ or SPR |
| `graph_translation` 📊 | `identify_shifted_graph` | observed: graph of f shown; which graph represents f(x)+k? | MCQ |
| | `find_output_after_shift` | observed: f(p)=v given; find f(p)+k | MCQ or SPR |

> `find_output_after_shift` is text-only — only `identify_shifted_graph` uses 📊.
> `piecewise_read_value` **removed** — zero Bluebook questions observed across 414 screenshots.

---

## D2 — 10 templates · 19 variants

| Template | Variants | BB anchor | Type |
|---|---|---|---|
| `evaluate_exponential_zero` | `find_initial_value` | observed: f(x)=a·(0.1)ˣ; evaluate at x=0; tests b⁰=1 | MCQ or SPR |
| | `interpret_initial_value` | observed: exponential model; what does f(0) represent in context? | MCQ |
| `interpret_exponential_statement` | `interpret_output_value` | observed: f(t)≈v stated; which statement correctly interprets this? | MCQ |
| | `interpret_growth_factor` | observed: f(x)=a(1.r)ˣ; what does the base represent per period? | MCQ |
| `minimum_from_vertex_form` | `find_minimum_value` | observed: g(x)=a(x−h)²+k; what is the minimum value? | MCQ or SPR |
| | `find_x_at_minimum` | observed: vertex form given; at what x does minimum occur? | MCQ or SPR |
| `x_for_min_from_factored` | `find_x_at_minimum` | observed: f(x)=(x−r)(x−s); x at min = midpoint of roots | MCQ or SPR |
| `interpret_x_intercept_context` | `interpret_physical_meaning` | observed: quadratic projectile/context; what does the positive zero represent? | MCQ |
| | `identify_positive_zero` | observed: two zeros given; which is physically meaningful? | MCQ |
| `exponential_from_table` | `identify_equation_from_table` | observed: constant-ratio (x, f(x)) table; identify the equation | MCQ |
| | `find_missing_table_value` | observed: same table with one cell hidden; find missing value | MCQ or SPR |
| `identify_quadratic_from_table` | `identify_equation_from_table` | observed: constant second-differences table; identify quadratic equation | MCQ |
| | `find_missing_value` | observed: same table; use second-difference pattern to find next value | MCQ or SPR |
| `exponential_growth_rate` | `find_growth_percentage` | observed: f(x)=a(1.r)ˣ/ᵏ; what is the growth rate per period as %? | MCQ |
| | `interpret_growth_rate` | observed: which statement correctly describes the % growth? | MCQ |
| `function_table_shift` | `identify_transformed_table` | observed: f(x) table given; g(x)=f(x)−k; which table represents g? | MCQ |
| | `find_specific_shifted_value` | observed: f(x) table + g(x)=f(x)±k defined; find g(a) by lookup | SPR |
| `graph_read_intercept_nonlinear` 📊 | `find_y_intercept` | observed: radical/exponential curve shown; identify y-intercept ordered pair | MCQ |
| | `find_x_intercept` | observed: same curve; identify x-intercept ordered pair | MCQ |
| `domain_range_graph` 📊 | `find_range_parabola` | observed: parabola on graph; which inequality represents the range? | MCQ |
| | `find_domain_radical` | observed: f(x)=√(x−a) given; what is the domain? | MCQ |

> `function_composition` **removed** — one Hard Bluebook example exists (complex abs-value + rational, f(a)=c then find g(c)) but does not match this d2 design. Redesign as d3 when additional examples are available.
> `inequality_system_nonlinear` **removed** — zero Bluebook questions observed across 414 screenshots.

---

## D3 — 11 templates · 22 variants

| Template | Variants | BB anchor | Type |
|---|---|---|---|
| `max_in_context` | `find_x_at_max` | observed: downward quadratic in context; at what x is the maximum? | MCQ or SPR |
| | `find_max_value` | observed: same; what is the maximum value? | MCQ or SPR |
| `compound_function_max` | `find_max_of_compound` | observed: g(t)=f(t)+k; find maximum of g given max of f | MCQ |
| | `find_shift_from_max` | observed: given max(f) and max(g); find the shift k | MCQ |
| `vertex_from_zeros` | `find_vertex_x` | observed: f(r₁)=f(r₂)=0; x-coordinate of vertex = (r₁+r₂)/2 | MCQ or SPR |
| | `find_vertex_y` | observed: factored form given; evaluate f at vertex x | MCQ |
| `identify_equivalent_form` | `reveal_maximum` | observed: standard form given; which equivalent form shows max/min as a constant? | MCQ |
| | `reveal_zeros` | observed: which form directly reveals the zeros? | MCQ |
| `exponential_two_points` | `find_parameter_value` | observed: h(x)=aˣ+b passes through 2 given points; find a | MCQ or SPR |
| | `find_product_of_params` | observed: same setup; find c+d or product of parameters | MCQ |
| `quadratic_parameter_properties` | `identify_true_statements` | observed: graph constraints given; which of I/II/III must be true about a,b,c? | MCQ |
| | `determine_sign_of_param` | observed: axis of symmetry direction given; deduce sign of b | MCQ |
| `exponential_reparameterize` | `convert_time_base` | observed: monthly rate model → rewrite in yearly base form | MCQ |
| | `find_percent_change` | observed: growth factor given; find equivalent annual % change | MCQ |
| `count_zeros_graph` | `count_x_intercepts` | observed: a·bˣ+c=0; how many real solutions / x-intercepts? | MCQ |
| | `count_intersections` | observed: exponential curve vs horizontal line; how many intersections? | MCQ |
| `minimum_completing_square` | `find_minimum_value` | observed: x²+bx+c given; find minimum by completing the square | MCQ or SPR |
| | `find_x_at_minimum` | observed: same; at what x does minimum occur? | SPR |
| `projectile_symmetry` | `find_time_to_return` | observed: quadratic projectile; find second time at a given height using symmetry | MCQ |
| | `find_max_height` | observed: same model; find maximum height | MCQ |
| `model_setup_quadratic` | `identify_equation` | observed: rectangle/area word problem; identify the correct quadratic equation | MCQ |
| | `write_equation` | observed: projectile context; set h(t)=target; find first positive solution | SPR |

---

## Implementation checklist (every template)

1. **`exactStem` required** whenever the stem contains specific numeric values, a table, a context name, or a direction that Haiku might reverse. Roughly 20/31 templates need it — err on the side of setting it.
2. **`b` even** in `minimum_completing_square` so h = −b/2 is always an integer.
3. **Table output values < 100** in `exponential_from_table`, `identify_quadratic_from_table`, `piecewise_read_value/find_output_formula`; use x∈[0,1,2,3] or [1,2,3,4].
4. **Context pool** for `interpret_y_intercept_context`, `interpret_exponential_statement`, `interpret_x_intercept_context` — use 4–5 scenario tags (bacteria, savings, population, temperature, revenue). exactStem always required.
5. **Diagram spec key present** for every 📊 variant; must exactly match the renderer contract below.
6. **No additional variants** — every variant listed is already cognitively distinct; no extras during coding.
7. **CRITICAL ctx note** for every template: tell Haiku not to state the key value (vertex coordinate, maximum, answer) directly in the stem.

---

## SVG renderer specs (new — built in Phase 3)

Three new renderers to add to `sympy-review.html`. The `parabola` renderer already exists and is reused for `vertex_from_graph`.

### `nonlinear_curve`

Used by: `y_intercept_from_graph`, `graph_translation/identify_shifted_graph`, `graph_read_intercept_nonlinear`

```json
{
  "type": "nonlinear_curve",
  "curveType": "exponential",
  "a": 2,
  "b": 3,
  "c": 0,
  "x_range": [-2, 4],
  "labeled_points": [{"x": 0, "y": 2, "label": "(0, 2)"}],
  "show_y_intercept": true
}
```

`curveType` values: `"exponential"` (y = a·bˣ + c), `"radical"` (y = a·√(x+b) + c)

### `piecewise_function`

Used by: `piecewise_read_value/find_output_graph`

```json
{
  "type": "piecewise_function",
  "pieces": [
    {"slope": 1, "intercept": 2, "domain": [-4, 1], "open_right": true},
    {"slope": -2, "intercept": 5, "domain": [1, 4], "open_left": false}
  ],
  "labeled_points": [{"x": 3, "y": -1, "label": "?"}],
  "x_range": [-4, 4]
}
```

### `inequality_nonlinear`

Used by: `inequality_system_nonlinear/identify_satisfying_region`

```json
{
  "type": "inequality_nonlinear",
  "parabola": {"a": 1, "h": 0, "k": 0},
  "line": {"m": 2, "b": 8},
  "shade": "between",
  "intersections": [{"x": -2, "y": 4}, {"x": 4, "y": 16}],
  "regions": ["I", "II", "III", "IV"],
  "x_range": [-5, 6]
}
```

---

## Routing dict (target shape)

```python
_D1 = {
    "evaluate_polynomial":          {"fn": _d1_evaluate_polynomial,          "variants": ["find_output"]},
    "evaluate_exponential":         {"fn": _d1_evaluate_exponential,         "variants": ["find_output"]},
    "evaluate_other_nonlinear":     {"fn": _d1_evaluate_other_nonlinear,     "variants": ["find_radical_output", "find_rational_output", "find_absolute_value_output"]},
    "interpret_y_intercept_context":{"fn": _d1_interpret_y_intercept_context,"variants": ["interpret_initial_value"]},
    "y_intercept_from_graph":       {"fn": _d1_y_intercept_from_graph,       "variants": ["identify_ordered_pair"]},
    "vertex_from_graph":            {"fn": _d1_vertex_from_graph,            "variants": ["find_minimum", "find_maximum"]},
    "graph_translation":            {"fn": _d1_graph_translation,            "variants": ["identify_shifted_graph", "find_output_after_shift"]},
    "piecewise_read_value":         {"fn": _d1_piecewise_read_value,         "variants": ["find_output_formula", "find_output_graph"]},
}

_D2 = {
    "evaluate_exponential_zero":        {"fn": _d2_evaluate_exponential_zero,        "variants": ["find_initial_value", "interpret_initial_value"]},
    "interpret_exponential_statement":  {"fn": _d2_interpret_exponential_statement,  "variants": ["interpret_output_value", "interpret_growth_factor"]},
    "minimum_from_vertex_form":         {"fn": _d2_minimum_from_vertex_form,         "variants": ["find_minimum_value", "find_x_at_minimum"]},
    "x_for_min_from_factored":          {"fn": _d2_x_for_min_from_factored,          "variants": ["find_x_at_minimum"]},
    "interpret_x_intercept_context":    {"fn": _d2_interpret_x_intercept_context,    "variants": ["interpret_physical_meaning", "identify_positive_zero"]},
    "exponential_from_table":           {"fn": _d2_exponential_from_table,           "variants": ["identify_equation_from_table", "find_missing_table_value"]},
    "identify_quadratic_from_table":    {"fn": _d2_identify_quadratic_from_table,    "variants": ["identify_equation_from_table", "find_missing_value"]},
    "exponential_growth_rate":          {"fn": _d2_exponential_growth_rate,          "variants": ["find_growth_percentage", "interpret_growth_rate"]},
    "function_table_shift":             {"fn": _d2_function_table_shift,             "variants": ["identify_transformed_table", "find_specific_shifted_value"]},
    "graph_read_intercept_nonlinear":   {"fn": _d2_graph_read_intercept_nonlinear,   "variants": ["find_y_intercept", "find_x_intercept"]},
    "function_composition":             {"fn": _d2_function_composition,             "variants": ["evaluate_f_of_g", "evaluate_g_of_f"]},
    "inequality_system_nonlinear":      {"fn": _d2_inequality_system_nonlinear,      "variants": ["identify_satisfying_point", "identify_satisfying_region"]},
}

_D3 = {
    "max_in_context":               {"fn": _d3_max_in_context,               "variants": ["find_x_at_max", "find_max_value"]},
    "compound_function_max":        {"fn": _d3_compound_function_max,        "variants": ["find_max_of_compound", "find_shift_from_max"]},
    "vertex_from_zeros":            {"fn": _d3_vertex_from_zeros,            "variants": ["find_vertex_x", "find_vertex_y"]},
    "identify_equivalent_form":     {"fn": _d3_identify_equivalent_form,     "variants": ["reveal_maximum", "reveal_zeros"]},
    "exponential_two_points":       {"fn": _d3_exponential_two_points,       "variants": ["find_parameter_value", "find_product_of_params"]},
    "quadratic_parameter_properties":{"fn": _d3_quadratic_parameter_properties,"variants": ["identify_true_statements", "determine_sign_of_param"]},
    "exponential_reparameterize":   {"fn": _d3_exponential_reparameterize,   "variants": ["convert_time_base", "find_percent_change"]},
    "count_zeros_graph":            {"fn": _d3_count_zeros_graph,            "variants": ["count_x_intercepts", "count_intersections"]},
    "minimum_completing_square":    {"fn": _d3_minimum_completing_square,    "variants": ["find_minimum_value", "find_x_at_minimum"]},
    "projectile_symmetry":          {"fn": _d3_projectile_symmetry,          "variants": ["find_time_to_return", "find_max_height"]},
    "model_setup_quadratic":        {"fn": _d3_model_setup_quadratic,        "variants": ["identify_equation", "write_equation"]},
}
```

---

## `pipeline.html` SKILL_TEMPLATES entry

```javascript
nonlinear_functions: {
  d1: [
    "evaluate_polynomial", "evaluate_exponential", "evaluate_other_nonlinear",
    "interpret_y_intercept_context", "y_intercept_from_graph",
    "vertex_from_graph", "graph_translation", "piecewise_read_value"
  ],
  d2: [
    "evaluate_exponential_zero", "interpret_exponential_statement",
    "minimum_from_vertex_form", "x_for_min_from_factored",
    "interpret_x_intercept_context", "exponential_from_table",
    "identify_quadratic_from_table", "exponential_growth_rate",
    "function_table_shift", "graph_read_intercept_nonlinear",
    "function_composition", "inequality_system_nonlinear"
  ],
  d3: [
    "max_in_context", "compound_function_max", "vertex_from_zeros",
    "identify_equivalent_form", "exponential_two_points",
    "quadratic_parameter_properties", "exponential_reparameterize",
    "count_zeros_graph", "minimum_completing_square",
    "projectile_symmetry", "model_setup_quadratic"
  ]
}
```

---

## Implementation order and test cadence

```
Step 1 — D1 (8 templates)
  Write all 8 _d1_* functions in nonlinear_fn.py
  Add D1 templates to pipeline.html SKILL_TEMPLATES
  Add Java wiring in SymPyGenerateStage.java
  Test d1 via pipeline.html (all 8 templates, both variants each)
  Build svgNonlinearCurve renderer (for y_intercept_from_graph, graph_translation)
  Build svgPiecewiseFunction renderer (for piecewise_read_value/find_output_graph)

Step 2 — D2 (12 templates)
  Write all 12 _d2_* functions
  Add D2 templates to pipeline.html
  Test d2 via pipeline.html
  Build svgInequalityNonlinear renderer (for inequality_system_nonlinear/identify_satisfying_region)

Step 3 — D3 (11 templates)
  Write all 11 _d3_* functions
  Add D3 templates to pipeline.html
  Test d3 via pipeline.html
  Full visual QA pass (d3 → d2 → d1)
```

---

## What stays unchanged

- `nonlinear_functions.json` narration examples — already complete (79 examples, 58 variants)
- `sympy-review.html` `parabola` renderer — reused as-is for `vertex_from_graph`
- All existing skill generators — NLF is purely additive
