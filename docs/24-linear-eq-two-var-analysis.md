# 24 — Linear Equations in Two Variables (L2V) — Analysis & Template Design

**Skill key:** `linear_eq_two_var`  
**Skill code:** `L2V`  
**SAT domain:** Algebra  
**Last updated:** 2026-04-17

---

## Source Data

**103 questions** analyzed from College Board Bluebook digital SAT, skill = "Linear equations in two variables".  
Source files: 61 JPG screenshots at `sat-engine/scripts/ALG-LEQ-2VAR/` (not committed — analysis artifacts only).

---

## Key Statistics

| Metric | Value |
|--------|-------|
| Total questions analyzed | 103 |
| Difficulty: Easy | 52% (≈ 54 questions) |
| Difficulty: Medium | 41% (≈ 42 questions) |
| Difficulty: Hard | 7% (≈ 7 questions) |
| Format: MCQ | 68 questions |
| Format: SPR (grid-in) | 35 questions |

---

## Cognitive Type Taxonomy

Questions are grouped by **what thinking they require**, not just what they ask.

| # | Type | Count | % | Primary Format | Difficulty |
|---|------|-------|---|----------------|------------|
| 1 | Word problems (SPR) — set up & solve from context | 35 | 34% | SPR | Easy–Medium |
| 2 | Slope — from points, equation, graph, table | 17 | 17% | MCQ + SPR | Easy–Medium |
| 3 | Match table ↔ equation | 9 | 9% | MCQ | Easy–Hard |
| 4 | Interpret coefficient / intercept in context | 9 | 9% | MCQ | Easy–Medium |
| 5 | Perpendicular / parallel slopes | 9 | 9% | MCQ + SPR | Easy–Medium |
| 6 | Write equation — from slope+point, two points | 9 | 9% | MCQ | Easy–Medium |
| 7 | Find y-intercept or x-intercept | 8 | 8% | MCQ + SPR | Easy–Hard |
| 8 | Match graph ↔ equation / table | 4 | 4% | MCQ | Easy |
| 9 | Write equation from graph (incl. translations) | 3 | 3% | MCQ + SPR | Hard |

---

## Implementation Order

Implementing from **least common → most common** so each type is validated before investing in heavier ones.

```
Phase 1:  Type 9  (3%)  ← current
Phase 2:  Type 8  (4%)
Phase 3:  Type 7  (8%)
Phase 4:  Type 6  (9%)
Phase 5:  Type 5  (9%)
Phase 6:  Type 4  (9%)
Phase 7:  Type 3  (9%)
Phase 8:  Type 2  (17%)
Phase 9:  Type 1  (34%)
```

---

## Difficulty Mapping (D1–D5 for the skill)

| D | Cognitive Types Covered | Notes |
|---|------------------------|-------|
| D1 | Type 2 (read slope from y=mx+b), Type 4 (interpret simple), Type 8 (read graph) | Direct read — no transformation |
| D2 | Type 6 (write eq from slope+y-int), Type 1 simple (substitute given value), Type 5 parallel (slope-intercept form) | One transformation step |
| D3 | Type 2 (slope from two points), Type 5 (perpendicular, slope-intercept), Type 3 (table match) | Must convert or solve |
| D4 | Type 7 (find intercept from standard form), Type 5 (perpendicular from Ax+By=C), Type 9A (function_shift) | Multi-step; indirect |
| D5 | Type 9B (translation intercept), Type 7 hard, Type 3 hard | Hard algebraic setup |

---

## Type 9 — Write Equation from Graph (incl. translations)

**3% of Bluebook questions. Hard difficulty only.**  
**Design decisions:** Follow screenshots exactly — no reinvention.

### Sub-type A: `function_shift` — MCQ (d4)

**What it tests:** Graph of `y = f(x) + k` is shown. Student must identify `f(x)`.

**Cognitive demand:** Student must recognize that the *graphed line* is not `f(x)` itself — they must subtract `k` from the visible y-intercept.

**Parameters Python generates:**
| Param | Range | Notes |
|-------|-------|-------|
| `m` | −3 to 3 (≠ 0) | Integer slope |
| `b` | ±{4, 6, 8, 10, 12} | True y-intercept of f(x) |
| `k` | ±{6, 8, 10, 12, 14} (≠ 0) | Vertical shift shown on graph |
| `visible_b` | `b + k` | What the graphed line's y-intercept actually is |

**SymPy verification:** Assert `visible_b - k == b`

**Answer format:** `f(x) = mx + b` (always use `f(x) = ...` format — not `y = ...`)

**Distractor logic:**
| Distractor | Error it traps |
|------------|----------------|
| `f(x) = mx + visible_b` | Forgot to subtract k — used graphed y-intercept directly |
| `f(x) = mx + (visible_b + k)` | Added k instead of subtracting (double-counted) |
| `f(x) = -mx + b` | Negated slope; got intercept right |

**Example:**
```
m = −2, b = 3, k = 14, visible_b = 17
Graph shows: y = −2x + 17 (labeled "y = f(x) + 14")
Question: "The graph of y = f(x) + 14 is shown. Which equation defines f?"
  A. f(x) = −2x + 3    ← CORRECT (17 − 14 = 3)
  B. f(x) = −2x + 17   ← forgot to subtract 14
  C. f(x) = −2x + 31   ← added 14 instead (17 + 14)
  D. f(x) = 2x + 3     ← negated slope
```

**Diagram:** Coordinate plane showing the SHIFTED line `y = mx + visible_b`.  
Label on graph reads `y = f(x) + k` (not the equation itself).

---

### Sub-type B: `translate_intercept` — SPR (d5)

**What it tests:** Line `Ax − By = C` translated **down** `k` units. Find x-coordinate of x-intercept of the resulting graph.

**Cognitive demand:** Student must (1) understand what translating down means algebraically, (2) derive the new equation, (3) find the x-intercept. Three separate steps.

**Parameters Python generates:**
| Param | Range | Notes |
|-------|-------|-------|
| `A` | {3, 4, 5, 6, 7, 9} | Must not share factor with C |
| `B` | {4, 5, 6, 7, 8, 9, 10} | ≠ A |
| `C` | `A × mult + offset` | Chosen so C % A ≠ 0 (non-integer x-intercept) |
| `k` | 2–6 | Units translated down |

**Math derivation:**
```
Original:  Ax − By = C   →   y = (A/B)x − C/B
Down k:    y = (A/B)x − C/B − k
New eq:    Ax − By = C + Bk
x-intercept (y=0):  x = (C + Bk) / A
```

**SymPy verification:** Assert `Rational(C + B*k, A) == x_intercept`

**Answer format:** Fraction `p/q` (SPR — student grids in the decimal or fraction)

**No distractors** — SPR format.

**Example (from Bluebook screenshot c73c84cc):**
```
A=9, B=10, C=19, k=4
New equation: 9x − 10y = 19 + 40 = 59
x-intercept: 59/9 ≈ 6.555...
Question: "The graph of 9x − 10y = 19 is translated down 4 units in the
xy-plane. What is the x-coordinate of the x-intercept of the resulting graph?"
Answer: 59/9 (accept 6.555 or 6.556)
```

**No diagram** for this sub-type (description only in question stem).

---

## Types 1–8 — Design Pending

These will be designed and documented here as each phase is implemented. High-level notes:

### Type 8 — Match Graph ↔ Equation / Table (4%)
- Easy difficulty, MCQ only
- Graph shown → student picks correct equation or table
- Sub-types: (a) read y-intercept from graph, (b) identify equation from graph

### Type 7 — Find y-intercept or x-intercept (8%)
- Easy–Hard, MCQ + SPR
- Sub-types: (a) read directly from y=mx+b [Easy], (b) derive from standard form Ax+By=C [Medium], (c) find from slope + x-intercept given [Hard]

### Type 6 — Write Equation — from slope+point, two points (9%)
- Easy–Medium, MCQ
- Sub-types: (a) slope + y-intercept → choose equation, (b) slope + non-y-intercept point, (c) two points

### Type 5 — Perpendicular / Parallel Slopes (9%)
- Easy–Medium, MCQ + SPR
- Sub-types: (a) parallel from slope-intercept [Easy], (b) perpendicular from slope-intercept [Easy/Medium], (c) parallel/perp from standard form Ax+By=C [Medium]
- Special case: write full equation of parallel/perpendicular line through a point [Medium]

### Type 4 — Interpret Coefficient / Intercept in Context (9%)
- Easy–Medium, MCQ
- Given ax + by = C in a word problem context
- Sub-types: (a) what does coefficient `a` represent (unit rate), (b) what does term `ax` represent (total for that category), (c) what does the y-intercept represent

### Type 3 — Match Table ↔ Equation (9%)
- Easy–Hard, MCQ
- Given equation, which table has correct (x, y) values — OR given table, which equation matches
- Hard version: fractional coefficients requiring careful substitution

### Type 2 — Slope — from points, equation, graph, table (17%)
- Easy–Medium, MCQ + SPR
- Sub-types: (a) read slope from y=mx+b [Easy], (b) compute from two points [Medium], (c) convert standard form [Medium], (d) read from graph [Easy], (e) compute from table [Medium], (f) simplify complex expression like y=(1/4)(27x+15)+7x [Medium]

### Type 1 — Word Problems (SPR) — set up & solve from context (34%)
- Easy–Medium, mostly SPR (some MCQ)
- Biggest category — needs the most templates
- Sub-types: (a) write equation and solve for unknown [Easy], (b) two-variable scenario with one value given [Easy/Medium], (c) interpret what term represents then compute [Medium], (d) multi-step setup [Hard]

---

## Design Constraints (apply to all types)

1. **Follow Bluebook exactly** — don't invent question formats that don't appear in the data
2. **Integer params preferred** for Easy/Medium; fractions allowed for Medium/Hard
3. **SPR answers must be finite decimals or simple fractions** (grid-in accepts up to 4 digits)
4. **Distractors must encode real student errors** — not random wrong values
5. **`questionContext` must be prescriptive** — tell Haiku exactly what to ask, what the answer is, and what the choices are
6. **No `y = ...` in choices for function_shift** — always `f(x) = ...`

---

## Few-Shot Examples File

Location: `src/main/resources/narration/examples/linear_eq_two_var.json`  
Status: **Pending** — to be created once first questions are generated and reviewed.
