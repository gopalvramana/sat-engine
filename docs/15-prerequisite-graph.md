# 15 — Prerequisite Graph

---

## Overview

The SAT skill taxonomy is structured as a **5-level directed acyclic graph (DAG)**, not a flat list. Every skill has 0–3 direct prerequisites. When a student fails a skill, the engine checks whether prerequisite gaps are the root cause before drilling the skill itself.

**Math dependencies are hard** — you literally cannot factor without understanding polynomials.
**R&W dependencies are softer** — they are diagnostic hints, not strict blockers.

---

## Floor Skills (Level 1)

These skills have no prerequisites within our system. If a student fails at Level 1, a **foundations micro-lesson** is triggered. There is no deeper remediation within the platform.

| Domain | Floor Skill |
|---|---|
| Algebra | Linear equations in one variable |
| Problem Solving & Data | Ratios and rates |
| Problem Solving & Data | Measures of center |
| Geometry | Lines and angles |
| Geometry | Area of 2D figures |
| R&W — Craft & Structure | Words in context |
| R&W — Information & Ideas | Central ideas and details |
| R&W — Standard English | Sentence boundaries |
| R&W — Standard English | Noun number and possessives |

---

## Math — Chain A: Algebra & Linear

```mermaid
graph TD
    A["🟤 linear_eq_one_var\nLinear equations in one variable\nLevel 1"]

    A --> B["linear_eq_word_problems\nLevel 2"]
    A --> C["linear_eq_two_var\nLinear equations in two variables\nLevel 2"]
    A --> D["equivalent_expressions\nLevel 3"]

    C --> E["graphs_linear\nGraphs of linear equations\nLevel 3"]
    C --> F["linear_functions\nLinear functions\nLevel 3"]
    C --> G["systems_linear_eq\nSystems of linear equations\nLevel 3"]
    C --> H["linear_inequalities_one_var\nLevel 3"]

    E --> I["linear_functions_word_problems\nLevel 4"]
    F --> I
    G --> J["systems_linear_word_problems\nLevel 4"]
    H --> K["linear_inequalities_two_var\nLevel 4"]
    E --> K
    K --> L["systems_linear_inequalities\nLevel 5"]
    G --> M["nonlinear_eq_systems\nLevel 5"]
```

---

## Math — Chain B: Advanced Math

```mermaid
graph TD
    A["🟤 linear_eq_one_var\nLevel 1"] --> B

    B["equivalent_expressions\nLevel 3"] --> C["factoring\nLevel 3"]

    C --> D["quadratic_equations\nSolving quadratic equations\nLevel 4"]
    C --> E["polynomial_operations\nLevel 4"]

    D --> F["quadratic_functions\nQuadratic functions and graphs\nLevel 5"]
    D --> G["radicals_rational_exponents\nLevel 5"]
    E --> H["rational_expressions\nLevel 5"]
    E --> F

    G --> I["radical_rational_abs_equations\nLevel 5"]
    H --> I

    F --> J["function_notation\nFunction notation, composition,\ntransformations · Level 5"]
    F --> K["polynomial_functions\nLevel 5"]
    E --> K

    D --> L["nonlinear_eq_systems\nLevel 5"]

    B --> M["exponential_functions\nLevel 4"]
    F --> J
    M --> J
```

---

## Math — Chain C: Geometry

```mermaid
graph TD
    A["🟤 lines_angles\nLines and angles\nLevel 1"]
    B["🟤 area_2d\nArea of 2D figures\nLevel 1"]

    A --> C["triangles\nTriangle properties\nLevel 2"]
    B --> D["perimeter_2d\nPerimeter and circumference\nLevel 2"]

    C --> E["similar_congruent_triangles\nLevel 3"]
    C --> F["pythagorean_theorem\nLevel 3"]
    B --> F

    F --> G["special_right_triangles\nLevel 4"]
    F --> H["right_triangle_trig\nSOH-CAH-TOA · Level 4"]
    E --> H
    F --> I["coordinate_geometry\nLevel 4"]

    H --> J["unit_circle_radians\nRadian measure and arc length\nLevel 5"]
    E --> K["circle_properties\nArcs and angles · Level 5"]
    B --> K
    K --> J

    I --> L["circle_equations\nEquation of a circle · Level 5"]
    K --> L
```

---

## Math — Chain D: Data Analysis

```mermaid
graph TD
    A["🟤 ratios_rates\nRatios and rates\nLevel 1"]
    B["🟤 data_center\nMeasures of center\nLevel 1"]

    A --> C["proportional_relationships\nLevel 2"]
    A --> D["unit_conversion\nLevel 2"]
    A --> E["percentages\nLevel 2"]
    B --> F["data_spread\nMeasures of spread\nLevel 2"]

    F --> G["data_distributions\nLevel 3"]
    E --> H["probability\nLevel 3"]

    G --> I["scatterplots\nScatterplots and lines of best fit\nLevel 4"]
    H --> J["conditional_probability\nLevel 4"]

    I --> K["two_var_models\nTwo-variable data models\nLevel 5"]
    J --> L["inference_statistics\nInference from sample statistics\nLevel 5"]
    I --> L

    L --> M["evaluating_claims\nEvaluating statistical claims\nLevel 5"]
```

---

## Reading & Writing — Prerequisite Graph

```mermaid
graph TD
    subgraph Reading Skills
        R1["🟤 central_ideas\nCentral ideas and details\nLevel 1"]
        R2["🟤 words_in_context\nWords in context\nLevel 1"]

        R1 --> R3["inferences\nLevel 3"]
        R1 --> R4["text_structure_purpose\nLevel 3"]
        R3 --> R5["command_evidence_textual\nLevel 4"]
        R4 --> R6["transitions\nLevel 4"]
        R5 --> R7["cross_text_connections\nLevel 5"]
        R4 --> R8["rhetorical_synthesis\nLevel 5"]
        R6 --> R8
        R1 --> R9["command_evidence_quantitative\nLevel 5"]
    end

    subgraph Grammar Skills
        G1["🟤 boundaries\nSentence boundaries\nLevel 1"]
        G2["🟤 noun_number_possessives\nLevel 1"]

        G1 --> G3["subject_verb_agreement\nLevel 2"]
        G2 --> G4["pronoun_agreement\nLevel 2"]
        G1 --> G5["punctuation\nLevel 3"]
        G3 --> G6["verb_tense_form\nLevel 3"]
        G5 --> G7["modifiers\nLevel 4"]
        G6 --> G7
    end
```

---

## Reading the Graphs

| Symbol | Meaning |
|---|---|
| 🟤 | Floor skill — no prerequisites in system |
| Arrow A → B | "B requires A" — A must be mastered before drilling B |
| Level 1 | No prerequisites |
| Level 5 | Deepest skill in the chain |

**DAG rules:**
- Some skills have 2 parents (e.g. `circle_equations` needs both `coordinate_geometry` and `circle_properties`)
- The engine checks **all** direct prerequisites before starting a drill
- A prerequisite is considered clear when `masteryScore ≥ 0.6`

---

## Prerequisite Check — Engine Logic

```mermaid
flowchart LR
    A["Student selects skill X"] --> B["Load direct prerequisites\nfrom taxonomy"]
    B --> C{"For each prerequisite:\nmasteryScore ≥ 0.6?"}
    C -->|All clear| D["Proceed to drill skill X"]
    C -->|Gap found| E["Queue lowest-level\ngap skill first"]
    E --> F["Drill or micro-lesson\non gap skill"]
    F --> C
```

The engine always resolves the **deepest gap first**. If a student wants to drill `quadratic_equations` but is missing both `equivalent_expressions` (L3) and `factoring` (L3), it drills `equivalent_expressions` first (it appears earlier in the chain).
