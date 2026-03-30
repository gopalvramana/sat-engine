# 12 — SAT Skill Taxonomy

**Canonical source:** `src/main/resources/taxonomy/sat_taxonomy.json`

This file lists every skill tracked by the question-generation pipeline.
Use the `key` values verbatim as the `--skill` argument when generating targeted questions.
Each skill has a matching row in the Coverage view at `http://localhost:8080/admin/validate.html`.

---

## How to use

```bash
java -jar sat-engine.jar \
  --job=generate --count=3 \
  --domain=<domain key> \
  --skill=<skill key> \
  --difficulty=4
```

Each question generated this way is saved with `skill_key = <skill key>` in the DB.
The Coverage view tracks how many approved questions exist per skill.

---

## Math

### Algebra — `--domain=algebra` (target: 20 questions)

| `--skill=` | Label |
|---|---|
| `linear_eq_one_var` | Linear equations in one variable |
| `linear_eq_word_problems` | Linear equation word problems |
| `linear_eq_two_var` | Linear equations in two variables |
| `graphs_linear` | Graphs of linear equations and functions |
| `linear_functions` | Linear functions |
| `linear_functions_word_problems` | Linear function word problems |
| `systems_linear_eq` | Systems of two linear equations |
| `systems_linear_word_problems` | Systems of linear equations — word problems |
| `linear_inequalities_one_var` | Linear inequalities in one variable |
| `linear_inequalities_two_var` | Linear inequalities in two variables |
| `systems_linear_inequalities` | Systems of linear inequalities |

### Advanced Math — `--domain=advanced_math` (target: 15 questions)

| `--skill=` | Label |
|---|---|
| `equivalent_expressions` | Equivalent expressions |
| `polynomial_operations` | Operations with polynomials |
| `factoring` | Factoring quadratic and polynomial expressions |
| `quadratic_equations` | Solving quadratic equations |
| `quadratic_functions` | Quadratic functions and graphs |
| `exponential_functions` | Exponential functions |
| `polynomial_functions` | Polynomial functions |
| `radicals_rational_exponents` | Radicals and rational exponents |
| `rational_expressions` | Rational expressions and equations |
| `radical_rational_abs_equations` | Radical, rational, and absolute value equations |
| `nonlinear_eq_systems` | Systems of one linear and one nonlinear equation |
| `function_notation` | Function notation, composition, and transformations |

### Problem Solving & Data Analysis — `--domain=problem_solving_data` (target: 20 questions)

| `--skill=` | Label |
|---|---|
| `ratios_rates` | Ratios and rates |
| `proportional_relationships` | Proportional relationships |
| `unit_conversion` | Units and unit conversion |
| `percentages` | Percentages |
| `data_center` | Measures of center |
| `data_spread` | Measures of spread |
| `data_distributions` | Data distributions |
| `scatterplots` | Scatterplots and lines of best fit |
| `two_var_models` | Two-variable data models |
| `probability` | Probability |
| `conditional_probability` | Conditional probability and two-way tables |
| `inference_statistics` | Inference from sample statistics |
| `evaluating_claims` | Evaluating statistical claims |

### Geometry & Trigonometry — `--domain=geometry_trigonometry` (target: 15 questions)

| `--skill=` | Label |
|---|---|
| `area_2d` | Area of 2D figures |
| `perimeter_2d` | Perimeter and circumference |
| `volume_surface_area` | Volume and surface area |
| `lines_angles` | Lines and angles |
| `triangles` | Triangle properties |
| `similar_congruent_triangles` | Similar and congruent triangles |
| `special_right_triangles` | Special right triangles |
| `pythagorean_theorem` | Pythagorean theorem |
| `right_triangle_trig` | Right triangle trigonometry |
| `law_sines_cosines` | Law of sines and cosines |
| `unit_circle_radians` | Unit circle and radian measure |
| `circle_properties` | Circle properties — arcs and angles |
| `circle_equations` | Equation of a circle |
| `coordinate_geometry` | Coordinate geometry |

---

## Reading & Writing

### Information & Ideas — `--domain=information_ideas` (target: 10 questions)

| `--skill=` | Label |
|---|---|
| `central_ideas` | Central ideas and details |
| `command_evidence_textual` | Command of evidence — textual |
| `command_evidence_quantitative` | Command of evidence — quantitative |
| `inferences` | Inferences |
| `cross_text_connections` | Cross-text connections |

### Craft & Structure — `--domain=craft_structure` (target: 10 questions)

| `--skill=` | Label |
|---|---|
| `words_in_context` | Words in context |
| `text_structure_purpose` | Text structure and purpose |
| `rhetorical_devices` | Rhetorical devices and author's perspective |

### Expression of Ideas — `--domain=expression_ideas` (target: 10 questions)

| `--skill=` | Label |
|---|---|
| `rhetorical_synthesis` | Rhetorically effective synthesis |
| `transitions` | Transitions |

### Standard English Conventions — `--domain=standard_english` (target: 10 questions)

| `--skill=` | Label |
|---|---|
| `boundaries` | Sentence boundaries |
| `subject_verb_agreement` | Subject-verb agreement |
| `pronoun_agreement` | Pronoun-antecedent agreement |
| `verb_tense_form` | Verb tense and form |
| `punctuation` | Punctuation |
| `modifiers` | Modifiers |

---

## Totals

| Section | Domains | Skills | Question Target |
|---|---|---|---|
| Math | 4 | 50 | 70 |
| Reading & Writing | 4 | 16 | 40 |
| **Total** | **8** | **66** | **110** |

---

## Notes

- `--section` is inferred from the domain automatically — you don't need to pass it when `--domain` is set.
- `--difficulty` is optional; omit it for weighted-random difficulty selection.
- Questions generated **without** `--skill` have `skill_key = NULL` in the DB. They still count toward the domain progress bar in the Coverage view but show as `0` per individual skill row.
- The canonical JSON at `src/main/resources/taxonomy/sat_taxonomy.json` is the single source of truth. The Coverage view in `validate.js` and the `GenerateStage.java` pipeline both reference these exact key values.
