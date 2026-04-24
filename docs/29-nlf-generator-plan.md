# NLF Generator Plan — `nonlinear_fn.py`

**Status:** APPROVED, NOT YET IMPLEMENTED  
**Skill key:** `nonlinear_functions`  
**Narration examples:** `src/main/resources/narration/examples/nonlinear_functions.json` — 79 examples · 58 variants · committed `31069dc`

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

31 template functions  (_d1_* × 8, _d2_* × 12, _d3_* × 11)

_D1 = {8 templates}
_D2 = {12 templates}
_D3 = {11 templates}
_ROUTING = {1: _D1, 2: _D2, 3: _D3}

nlf_variants()        ← public metadata API
gen_nonlinear_fn()    ← main dispatcher
```

---

## D1 — 8 templates · 13 variants

| Template | Variants | Key logic | Type |
|---|---|---|---|
| `evaluate_polynomial` | `find_output` | pick a∈[1..4], b∈[0..5], x∈[−3..5]; compute ax²+b or x³+b | MCQ or SPR |
| `evaluate_exponential` | `find_output` | pick a∈[2..5], b∈[2..3], x∈[0..3]; compute a·bˣ | MCQ or SPR |
| `evaluate_other_nonlinear` | `find_radical_output` | pick x+c = perfect square; compute √(x+c) | MCQ or SPR |
| | `find_rational_output` | pick k∈[2..6], x∈[±2..±6]; compute k/x | MCQ |
| | `find_absolute_value_output` | pick c∈[−5..5], x so \|x+c\| is a positive integer | MCQ or SPR |
| `interpret_y_intercept_context` | `interpret_initial_value` | f(0)=a in real-world context; 4 MCQ choices describe meaning; exactStem required | MCQ |
| `y_intercept_from_graph` 📊 | `identify_ordered_pair` | exponential or radical curve shown; read (0, f(0)) | MCQ |
| `vertex_from_graph` 📊 | `find_minimum` | upward parabola; read vertex min | MCQ or SPR |
| | `find_maximum` | downward parabola; read vertex max | MCQ or SPR |
| `graph_translation` 📊 | `identify_shifted_graph` | f(x) shown; which graph shows f(x)+k? | MCQ |
| | `find_output_after_shift` | given f(p)=v, what is f(p)+k? (no diagram) | MCQ or SPR |
| `piecewise_read_value` | `find_output_formula` | 2-piece formula; evaluate at x in specified piece; exactStem | MCQ or SPR |
| | `find_output_graph` 📊 | 2-piece graph shown; read f(a) from graph | MCQ |

> `find_output_after_shift` is text-only — only `identify_shifted_graph` uses 📊.

---

## D2 — 12 templates · 23 variants

| Template | Variants | Key logic | Type |
|---|---|---|---|
| `evaluate_exponential_zero` | `find_initial_value` | f(x)=a·bˣ; f(0)=a | MCQ or SPR |
| | `interpret_initial_value` | same model; what does f(0) mean in context? exactStem | MCQ |
| `interpret_exponential_statement` | `interpret_output_value` | f(t)=v means "after t units, value is v"; exactStem | MCQ |
| | `interpret_growth_factor` | f(x)=a(1.r)ˣ; what does base (1.r) represent? | MCQ |
| `minimum_from_vertex_form` | `find_minimum_value` | g(x)=a(x−h)²+k; min = k | MCQ or SPR |
| | `find_x_at_minimum` | same; x at min = h | MCQ or SPR |
| `x_for_min_from_factored` | `find_x_at_minimum` | f(x)=(x−r)(x−s); x at min = (r+s)/2 | MCQ or SPR |
| `interpret_x_intercept_context` | `interpret_physical_meaning` | quadratic h(t)=0; what does this mean in context? exactStem | MCQ |
| | `identify_positive_zero` | two zeros given; which is physically meaningful (positive)? | MCQ |
| `exponential_from_table` | `identify_equation_from_table` | constant-ratio table; 4 equation choices | MCQ |
| | `find_missing_table_value` | same table, one cell hidden; find missing value | MCQ or SPR |
| `identify_quadratic_from_table` | `identify_equation_from_table` | constant second-differences table; 4 equation choices | MCQ |
| | `find_missing_value` | same; use second-difference pattern to extend | MCQ or SPR |
| `exponential_growth_rate` | `find_growth_percentage` | f(x)=a(1.r)ˣ; growth rate per period as % | MCQ |
| | `interpret_growth_rate` | which statement about the rate is correct? | MCQ |
| `function_table_shift` | `identify_transformed_table` | given f table; which table matches g(x)=f(x)−k? | MCQ |
| | `find_specific_shifted_value` | given f(a)=v; what is f(a)+k? | SPR |
| `graph_read_intercept_nonlinear` 📊 | `find_y_intercept` | radical/exponential curve shown; identify y-intercept | MCQ |
| | `find_x_intercept` | same curve; identify x-intercept | MCQ |
| `function_composition` | `evaluate_f_of_g` | f quadratic or exponential, g linear; compute f(g(a)) at integer a | MCQ or SPR |
| | `evaluate_g_of_f` | same pair; compute g(f(a)) | MCQ or SPR |
| `inequality_system_nonlinear` | `identify_satisfying_point` | 4 ordered pairs; check which satisfies linear + quadratic inequality | MCQ |
| | `identify_satisfying_region` 📊 | parabola + line graph with labeled regions; identify correct region | MCQ |

---

## D3 — 11 templates · 22 variants

| Template | Variants | Key logic | Type |
|---|---|---|---|
| `max_in_context` | `find_x_at_max` | f(x)=ax²+bx+c (a<0); x at max = −b/2a | MCQ or SPR |
| | `find_max_value` | same; evaluate f at x=−b/2a | MCQ or SPR |
| `compound_function_max` | `find_max_of_compound` | max of g(x)=f(x)+k = max(f)+k | MCQ |
| | `find_shift_from_max` | given max(f) and max(g), solve for k | MCQ |
| `vertex_from_zeros` | `find_vertex_x` | f(r₁)=f(r₂)=0; vertex x = (r₁+r₂)/2 | MCQ or SPR |
| | `find_vertex_y` | f(x)=a(x−r₁)(x−r₂); evaluate f at vertex x | MCQ |
| `identify_equivalent_form` | `reveal_maximum` | which form shows max/min as explicit constant? → vertex form | MCQ |
| | `reveal_zeros` | which form reveals zeros directly? → factored form | MCQ |
| `exponential_two_points` | `find_parameter_value` | h(x)=aˣ+b through 2 points; find a | MCQ or SPR |
| | `find_product_of_params` | h(x)=c·2ˣ+d through 2 points; find c+d | MCQ |
| `quadratic_parameter_properties` | `identify_true_statements` | graph constraints → which of I/II/III must be true? | MCQ |
| | `determine_sign_of_param` | from axis/opening direction, deduce sign of b | MCQ |
| `exponential_reparameterize` | `convert_time_base` | monthly model → yearly: (b¹²)ᵗ form | MCQ |
| | `find_percent_change` | compute (1+r)¹²−1 ≈ annual rate; nearest % | MCQ |
| `count_zeros_graph` | `count_x_intercepts` | a·bˣ+c=0 has exactly one solution | MCQ |
| | `count_intersections` | exponential vs horizontal line; how many intersections? | MCQ |
| `minimum_completing_square` | `find_minimum_value` | x²+bx+c (b even); min = c−(b/2)² | MCQ or SPR |
| | `find_x_at_minimum` | same; x at min = −b/2 | SPR |
| `projectile_symmetry` | `find_time_to_return` | h(t)=−16t²+vt+c; h(t₁)=h, find t₂=2·axis−t₁ | MCQ |
| | `find_max_height` | same model; find h at axis of symmetry | MCQ |
| `model_setup_quadratic` | `identify_equation` | rectangle/fence word problem → identify area equation | MCQ |
| | `write_equation` | projectile model; set h(t)=target; find first solution | SPR |

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
