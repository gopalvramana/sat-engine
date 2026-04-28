# Algebra Skills — Consolidated Bluebook Audit & Gap Action Plan

**Skills covered:** LFN · L1V · LIN · SLE · L2V  
**Catalogue docs:** docs/31 – docs/35  
**Audited:** 2026-04-26  
**Status:** All 5 skills fully catalogued and two-way audited. Ready for gap implementation.

---

## 1. Removals (do first — clean house before adding)

| # | Skill | Item | Reason | Action |
|---|-------|------|--------|--------|
| R-01 | LFN | `arithmetic_nth_term` (D2 routing entry + function) | Zero Bluebook questions observed. Template was written without BB anchor. | Delete from `_D2` dict + delete generator function |
| R-02 | LFN | `_d1_graph_read_context` function | Defined at line 463 of `lin_fn.py` but never added to `_D1` routing dict — dead code. | Either wire into `_D1` (if it produces valid questions) or delete |

---

## 2. Weak Anchor — Review Required

| # | Skill | Template | Issue | Recommendation |
|---|-------|----------|-------|----------------|
| W-01 | LIN | `two_var_bound_neg` | No BB question explicitly tests "divide by negative → flip sign". Template may be pedagogically valid but has no direct BB anchor. | Run a d3 test generation. If output matches `table_satisfies_twovar` pattern, deprecate. Otherwise keep with a note. |

---

## 3. New Templates Needed

Ranked by priority (BB question count and student impact).

### 🔴 Priority 1 — High (≥5 BB questions, significant structural gap)

#### GAP-01 · LIN · `graph_to_inequality`
- **BB anchor:** ~6 questions observed (pp.0001, 0014, 0017, 0034, 0048, 0062)
  - Easy variant (pp.0001, 0034): horizontal boundary; student reads y = c and picks y ≤ c or y ≥ c from shading
  - Medium variant (pp.0014, 0062): sloped dashed or solid boundary; student identifies slope + intercept + shading direction
  - Medium variant (pp.0017, 0048): graph shown, student picks which ordered pair lies in the shaded region
- **Cognitive type:** Shaded half-plane displayed; student reads boundary line and shading to select correct inequality
- **Difficulty:** d1 (horizontal boundary) / d2 (sloped boundary + shading direction)
- **Implementation note:** Requires new diagram capability — `shaded_half_plane` with boundary line, shading indicator, and dashed/solid line flag. Not currently in the renderer. Coordinate plane already exists; needs shading layer added.
- **Two variants needed:**
  - `identify_inequality` — "which inequality does this graph represent?" (multiple choice)
  - `identify_point_in_region` — "which ordered pair is a solution?" (can reuse `point_satisfies` pattern with diagram)

---

### 🟡 Priority 2 — Medium (3–5 BB questions, manageable scope)

#### GAP-02 · L1V · `classify_solutions`
- **BB anchor:** ~4 questions (pp.0048, 0054, 0061, 0072)
  - pp.0048, 0061, 0072: given equation with distribution on both sides; student expands, classifies (one / zero / ∞)
  - p.0054: identity form (ax = ax) → student recognises infinitely many
- **Cognitive type:** Fully-specified equation given; student expands both sides, collects terms, and classifies result
- **Difficulty:** d2 (medium — equation that simplifies to unique solution), d3 (hard — equation that collapses to contradiction or identity)
- **Distinct from existing templates:** Current `no_solution` and `infinite_solutions_*` ask "find the parameter". This asks "classify the equation" — different direction, different skill.
- **Implementation note:** Text-only; no diagram. Three-way classification: exactly one / no solution / infinitely many.

#### GAP-03 · SLE · `infinite_solutions_point`
- **BB anchor:** ~4 questions (pp.0010, 0016, 0052, 0078)
  - System is coincident (second equation is scalar multiple of first)
  - Free parameter r introduced; student shown four candidate points expressed as (r, f(r)) or (f(r), r)
  - Student must identify which expression is consistent with both equations for all real r
- **Cognitive type:** Coincident system + parametric point identification
- **Difficulty:** d3
- **Distinct from `infinite_find_constant`:** That template finds the constant b that makes two equations coincident. This template assumes they are already coincident and asks which point (in terms of r) lies on both lines.
- **Implementation note:** Text-only. Generate coincident pair, pick a free-parameter variable, express the line as y = mx + b, generate distractors by perturbing slope or intercept in the parametric expression.

#### GAP-04 · SLE · `unique_intersection_find_constant`
- **BB anchor:** ~2 questions (pp.0062, 0065)
  - p.0062: system has unknown constant a in a coefficient; told intersection is at x = 4; substitute x = 4 into one equation to find a
  - p.0065: system has unknown constant w multiplying a variable; told y = 19 at intersection; substitute y = 19 to find w
- **Cognitive type:** System has unknown constant; one coordinate of the (unique) solution given; back-solve for the constant
- **Difficulty:** d3
- **Distinct from `no_solution_find_param`:** That template finds the parameter that PREVENTS a solution. This template finds the parameter that produces a specific solution point.
- **Implementation note:** Text-only. Generate system with one unknown constant in a coefficient. Pick a specific solution point (x₀, y₀). Student substitutes the known coordinate into the equation containing the unknown constant.

#### GAP-05 · L2V · `interpret_coefficient_difference`
- **BB anchor:** ~4 questions (observed in L2V hard questions)
  - Real-world context; equation has two variable terms with different coefficients
  - Question asks what the difference between those coefficients (or the ratio) means in context
  - Cognitively distinct from "what does the slope mean?" — asks about the relationship between two slopes/rates
- **Cognitive type:** Two-coefficient interpretation; student identifies what the arithmetic difference of two rates represents in the described scenario
- **Difficulty:** d3
- **Distinct from existing `interpret_slope_in_context`:** That asks about a single slope. This asks about two rates and the meaning of their difference.
- **Implementation note:** Text-only. Extend the `word_problem_hard` family. Generate a scenario with two distinct per-unit rates; ask what the difference (or gap) represents.

---

### 🟢 Priority 3 — Low (1–2 BB questions, add as variants of existing templates)

#### GAP-06 · L2V · `interpret_solution_point`
- **BB anchor:** ~3 questions (observed in L2V medium–hard questions)
  - Given equation in context; student told the solution occurs at a specific (x, y) value; asked what that intersection represents in the real-world scenario
- **Cognitive type:** Interpret a specific solution point (not an intercept) in context
- **Difficulty:** d2–d3
- **Implementation note:** Can be a variant of `interpret_intercept_in_context` — the structure is nearly identical, just the special point is not an axis intercept.

#### GAP-07 · L1V · `select_modeling_equation`
- **BB anchor:** ~4 questions (pp.0022, 0049, 0077, 0079)
  - Word problem; student reads scenario and selects which of four equations correctly encodes it
  - No solving required — purely a translation task
- **Cognitive type:** Equation selection from verbal description (no solving)
- **Difficulty:** d1–d2
- **Distinct from existing `equivalent_equation`:** That gives a solved equation and asks for an equivalent form. This gives a word problem and asks which algebraic form matches.
- **Note:** ~40% of BB L1V questions are word problems handled by LWP skill. Confirm overlap before implementing so this doesn't duplicate LWP templates.

#### GAP-08 · LFN · `constant_function_recognition`
- **BB anchor:** ~2 questions (observed in LFN screenshots)
  - Graph of horizontal line (f(x) = c) or table with constant y values shown
  - Student recognises that the function is constant and selects the matching equation or evaluates f(anything) = c
- **Cognitive type:** Constant function (zero slope) identification
- **Difficulty:** d1
- **Implementation note:** Very low volume (2 questions). Can be added as a variant of `match_graph_to_equation_table` with the constraint slope = 0.

#### GAP-09 · LFN · `compound_function_x_intercept`
- **BB anchor:** ~1 question (observed: h(x) = f(x) + g(x) → find x-intercept of h)
- **Cognitive type:** Two linear functions summed; student finds x-intercept of the combined function
- **Difficulty:** d3
- **Note:** Volume is only 1. Add as a d3 variant of `evaluate_compound` only if the variant is cognitively distinct (which it is — finding x-intercept is different from evaluating at a point).

---

## 4. Full Priority-Ordered Action Plan

| Order | ID | Skill | Action | Effort | Diagram? |
|-------|----|-------|--------|--------|----------|
| 1 | R-01 | LFN | Delete `arithmetic_nth_term` from routing + function | Trivial | No |
| 2 | R-02 | LFN | Audit `_d1_graph_read_context` → wire or delete | Small | No |
| 3 | W-01 | LIN | Test `two_var_bound_neg` → confirm or deprecate | Small | No |
| 4 | GAP-01 | LIN | New template `graph_to_inequality` (d1/d2) | Large | **Yes — shaded half-plane** |
| 5 | GAP-02 | L1V | New template `classify_solutions` (d2/d3) | Medium | No |
| 6 | GAP-03 | SLE | New template `infinite_solutions_point` (d3) | Medium | No |
| 7 | GAP-04 | SLE | New template `unique_intersection_find_constant` (d3) | Medium | No |
| 8 | GAP-05 | L2V | New template `interpret_coefficient_difference` (d3) | Medium | No |
| 9 | GAP-06 | L2V | New variant `interpret_solution_point` (d2/d3) | Small | No |
| 10 | GAP-07 | L1V | New template `select_modeling_equation` (d1/d2) | Medium | No |
| 11 | GAP-08 | LFN | New variant `constant_function_recognition` (d1) | Small | No |
| 12 | GAP-09 | LFN | New variant `compound_function_x_intercept` (d3) | Small | No |

---

## 5. Template Health Summary (existing templates, post-audit)

| Skill | Total Templates | Confirmed BB Anchors | Weak/Dead | Remove |
|-------|----------------|----------------------|-----------|--------|
| LFN | ~22 | 20 | 2 (dead code) | 1 (`arithmetic_nth_term`) |
| L1V | 16 | 16 | 0 | 0 |
| LIN | 18 | 17 | 1 (`two_var_bound_neg`) | 0 (pending review) |
| SLE | 13 | 13 | 0 | 0 |
| L2V | 28 | 28 | 0 | 0 |
| **Total** | **97** | **94** | **3** | **1 confirmed** |

---

## 6. Diagram Capability Gap

The `shaded_half_plane` diagram type (required for GAP-01) does not exist in the current renderer. Before implementing GAP-01:

1. Add `shaded_half_plane` to the Python math engine's diagram output format
2. Add renderer support in `sympy-review.html` (and `pipeline.html`)
3. Support: boundary line (slope + intercept), solid vs dashed line, shading direction (above/below)
4. Viewport: standard ±5 with all intercepts within ±4

All other gaps (GAP-02 through GAP-09) are text-only and can be implemented without renderer changes.

---

## 7. Implementation Order Recommendation

**Phase A — Cleanup (no Bluebook examples needed):**
- R-01: Delete `arithmetic_nth_term`
- R-02: Wire or delete `_d1_graph_read_context`
- W-01: Test and decision on `two_var_bound_neg`

**Phase B — Text-only templates (Bluebook examples + generator):**
- GAP-02 (`classify_solutions`) — L1V
- GAP-03 (`infinite_solutions_point`) — SLE
- GAP-04 (`unique_intersection_find_constant`) — SLE
- GAP-05 (`interpret_coefficient_difference`) — L2V
- GAP-07 (`select_modeling_equation`) — L1V

**Phase C — Small variants (low effort, add to existing templates):**
- GAP-06 (`interpret_solution_point`) — L2V
- GAP-08 (`constant_function_recognition`) — LFN
- GAP-09 (`compound_function_x_intercept`) — LFN

**Phase D — Diagram-dependent (after renderer update):**
- GAP-01 (`graph_to_inequality`) — LIN (requires `shaded_half_plane` diagram type)
