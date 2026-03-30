# 06 — Question Bank

---

## ADR-028 — Launch Target: 500–600 Questions

**Decision:** Launch with 500–600 reviewed questions. That equals 5–6 unique full practice tests.

**Why this is enough:**
- College Board only provides 8 official tests — ever
- 5–6 tests is a legitimate starting point
- Real feedback from real users is more valuable than waiting for 1,000 questions
- Growth plan: add 80 reviewed questions per week after launch

**Growth trajectory:**

| Milestone | Questions | Full Tests | Notes |
|-----------|----------|------------|-------|
| Launch | 500–600 | 5–6 | Enough to charge |
| Month 6 | ~800 | ~8 | Comparable to official tests |
| Month 12 | ~1,500 | ~15 | Competitive with Acely |
| Month 24 | ~3,000 | ~30 | Full competitive parity |

**Status:** ✅ DECIDED

---

## ADR-029 — Human Review Policy

**Decision:** Every single question reviewed by the founder before going live. No unreviewed question ever shown to a student. `is_reviewed = true` enforced at the repository query level.

**Review checklist for Math questions:**
- [ ] Exactly ONE answer is correct
- [ ] Wrong answers represent real student mistakes (not obviously wrong)
- [ ] Solvable in under 2.5 minutes
- [ ] Difficulty rating is honest
- [ ] LaTeX renders correctly (check in review_questions.html)
- [ ] Diagram matches the question if present
- [ ] Explanation shows the simplest method
- [ ] Units are consistent

**Review checklist for R&W questions:**
- [ ] Passage actually supports the correct answer
- [ ] Correct answer is the BEST answer — not just a possible answer
- [ ] Wrong answers are wrong for clear, articulable reasons
- [ ] Passage is internally coherent
- [ ] Question stem is unambiguous

**Review checklist for SVG diagrams:**
- [ ] Labeled measurements match the actual rendered shape
- [ ] Right angle marker at correct vertex
- [ ] Labels don't overlap
- [ ] Highlighted element matches what the question asks about

**Why this is non-negotiable:**  
Acely's #1 Reddit complaint is AI slop — mathematically impossible questions. Human review is the quality moat. This commitment IS the marketing message.

**Status:** ✅ DECIDED

---

## ADR-030 — Question Generation Workflow

**Decision:** All question generation, review, and enrichment runs as Java pipeline stages inside the sat-engine JAR. No separate Python or Node.js scripts.

**Pipeline stages:**

| Stage | Command | What it does | Status produced |
|-------|---------|-------------|-----------------|
| Generate | `--job=generate --count=20` | Calls Claude Haiku, writes directly to DB | `generated` |
| Agent Review | `--job=agent-review` | Runs 9 checks per question via Claude Opus | `reviewed` |
| Enrich | `--job=enrich` | Adds trapCategory, coreConcept, prerequisites, animation | `enriched` |
| Human Review | Open validate.html | Approve / reject / fix answer key | `approved` or `rejected` |

**Daily evening routine (45–60 minutes):**
1. 7:00 PM — `java -jar sat-engine.jar --job=generate --count=20` (15 min unattended)
2. 7:15 PM — `java -jar sat-engine.jar --job=agent-review` (runs in background)
3. 7:30 PM — `java -jar sat-engine.jar --job=enrich` (runs in background)
4. 7:45 PM — Open `http://localhost:8080/admin/validate.html` → review enriched questions → approve/reject (20 min)
5. 8:00 PM — Done. ~15 approved questions added to DB.

**Weekly output:** ~80 approved questions (20/day × 5 days × 80% pass rate)

**Status:** ✅ DECIDED — Pipeline built and running

---

## Question Status Lifecycle

Every question moves through these statuses in order:

```
generated → reviewed → enriched → approved
                                 ↘ rejected
```

| Status | Set by | Meaning |
|--------|--------|---------|
| `generated` | `--job=generate` | Raw question written to DB, not yet verified |
| `reviewed` | `--job=agent-review` | Agent has run 9-check review, issues logged |
| `enriched` | `--job=enrich` | Pedagogical fields added (trapCategory, coreConcept, prerequisites) |
| `approved` | Human in validate.html | Ready to serve to students |
| `rejected` | Human in validate.html | Disqualified — never served to students |

**Feedback loop:** A rejected or failing question can be pushed back to an earlier status and re-run through that stage:
- Push back to `generated` → re-run `--job=agent-review`
- Push back to `reviewed` → re-run `--job=enrich`

---

## ADR-031 — Domain Distribution for 500 Questions

**Target distribution:**

### Math (300 questions)
| Domain | Code | Target | % | Real SAT |
|--------|------|--------|---|---------|
| Algebra | ALG | 105 | 35% | 35% |
| Advanced Math | ADV | 105 | 35% | 35% |
| Problem Solving & Data | PS | 45 | 15% | 15% |
| Geometry & Trigonometry | GEO | 45 | 15% | 15% |

### Reading & Writing (200 questions)
| Domain | Code | Target | % | Real SAT |
|--------|------|--------|---|---------|
| Information & Ideas | INF | 52 | 26% | 26% |
| Craft & Structure | CRF | 56 | 28% | 28% |
| Expression of Ideas | EXP | 40 | 20% | 20% |
| Standard English Conventions | ENG | 52 | 26% | 26% |

### Difficulty Distribution (across all 500)
| Difficulty | Label | Target | % |
|-----------|-------|--------|---|
| 1 | Very easy | 25 | 5% |
| 2 | Easy | 75 | 15% |
| 3 | Medium-easy | 100 | 20% |
| 4 | Medium | 125 | 25% |
| 5 | Medium-hard | 100 | 20% |
| 6 | Hard | 50 | 10% |
| 7 | Very hard | 25 | 5% |

The generate pipeline stage handles weighted random selection automatically — distribution builds up naturally without manual tracking.

**Status:** ✅ DECIDED

---

## ADR-032 — DB Question Schema

Every generated question is written directly to PostgreSQL with this structure:

```json
{
  "externalId": "MATH-ALG-001",
  "section": "math",
  "domain": "algebra",
  "skill": "linear_equations_one_variable",
  "difficulty": 3,
  "questionType": "mcq",
  "questionStem": "If \\(3x + 7 = 22\\), what is the value of \\(x\\)?",
  "optionA": "3",
  "optionB": "4",
  "optionC": "5",
  "optionD": "6",
  "correctAnswer": "C",
  "sprMin": null,
  "sprMax": null,
  "explanationShort": "Isolate x in two steps.",
  "explanationSteps": [
    { "title": "Subtract 7", "content": "Subtract 7 from both sides.", "math": "3x = 15" },
    { "title": "Divide by 3", "content": "Divide both sides by 3.", "math": "x = 5" }
  ],
  "trapCategory": "calculation_error",
  "trapExplanation": "Students who divide first get x = 15/3 before subtracting, choosing option B (4).",
  "coreConcept": { "title": "Linear Equations", "summary": "...", "keyFormula": "ax + b = c" },
  "prerequisites": [{ "topic": "Arithmetic operations", "why": "Need to subtract and divide" }],
  "animation": { "eligible": false },
  "pool": "both",
  "passageText": null,
  "diagram": null,
  "calculatorOk": true,
  "source": "ai_generated",
  "status": "approved",
  "generatedAt": "2026-03-28T20:30:00Z"
}
```

**For questions with diagrams:**
```json
{
  "diagram": {
    "diagramType": "svg_programmatic",
    "svgConfig": {
      "shape": "right_triangle",
      "width": 220,
      "height": 190,
      "vertices": { ... },
      "sides": [ ... ],
      "rightAngleAt": "B",
      "angles": [ ... ]
    }
  }
}
```

**Status:** ✅ DECIDED

---

## Pipeline Quick Reference

```bash
# Generate questions — random domain/skill
java -jar sat-engine.jar --job=generate --count=20
java -jar sat-engine.jar --job=generate --count=10 --section=math
java -jar sat-engine.jar --job=generate --count=10 --section=math --difficulty=4

# Generate questions — targeted by skill (recommended for coverage building)
# Full skill list: docs/12-sat-skill-taxonomy.md
java -jar sat-engine.jar --job=generate --count=3 --domain=algebra --skill=linear_functions
java -jar sat-engine.jar --job=generate --count=3 --domain=geometry_trigonometry --skill=pythagorean_theorem --difficulty=5
java -jar sat-engine.jar --job=generate --count=3 --domain=problem_solving_data --skill=probability

# Agent review (runs on all status=generated questions)
java -jar sat-engine.jar --job=agent-review

# Re-review only failed questions
java -jar sat-engine.jar --job=agent-review --only-failed

# Enrich (runs on all status=reviewed questions)
java -jar sat-engine.jar --job=enrich

# Normal API server (no pipeline — starts web server)
java -jar sat-engine.jar
```

**Review UI:** `http://localhost:8080/admin/validate.html`
Questions with `status=enriched` appear automatically in the review queue.
Each action (Approve / Reject / Fix answer) calls the API immediately — no file downloads needed.

---

## Progress Tracker

Track this weekly:

| Domain | Code | Target | Generated | Reviewed | Enriched | Approved | Status |
|--------|------|--------|-----------|----------|----------|----------|--------|
| Algebra | ALG | 105 | | | | | |
| Advanced Math | ADV | 105 | | | | | |
| Problem Solving | PS | 45 | | | | | |
| Geometry/Trig | GEO | 45 | | | | | |
| Information/Ideas | INF | 52 | | | | | |
| Craft/Structure | CRF | 56 | | | | | |
| Expression Ideas | EXP | 40 | | | | | |
| Standard English | ENG | 52 | | | | | |
| **TOTAL** | | **500** | | | | | |

---

## ADR-033 — Practice Mode vs Exam Mode Pool Requirements

**Decision:** The 5-questions-per-skill strategy covers practice mode. Exam (full mock test) mode requires a separate, larger pool.

### Practice Mode — 5 per skill is sufficient
Students pick a skill, get served questions from that skill pool. 5 questions gives a reasonable rotation before repeats. The coverage page in validate.html tracks this directly.

### Exam / Full Mock Test Mode — needs more

A full SAT module has:
- Math: ~22 questions × 2 modules = **44 math questions per test**
- R&W: ~27 questions × 2 modules = **54 R&W questions per test**
- **~98 questions per unique full test**

To offer N unique non-repeating full tests you need N × 98 questions in the pool.

### Two-Phase Strategy

| Phase | Goal | Questions | Timeline |
|---|---|---|---|
| **Phase 1** | Skill coverage — practice mode | 5/skill × 66 skills = **330** | Weeks 1–7 |
| **Phase 2** | Pool expansion — exam mode | +5/skill × 66 skills = **+330** | Months 3–6 |

Phase 1 + existing questions (~45) gets to ~375 approved → enough for **3 unique full tests + full practice coverage**.
Phase 2 doubles the pool → **6–7 unique full tests** → strong launch for exam mode.

**Status:** ✅ DECIDED

---

## ADR-034 — 6-Week Skill Coverage Plan (Phase 1)

**Decision:** Generate 5 questions per skill in this order over 6 weeks.

### Difficulty spread per skill (5 questions)
| # | Difficulty | Label |
|---|---|---|
| 1 | 2 | Easy |
| 2 | 3 | Medium-easy |
| 3 | 4 | Medium |
| 4 | 5 | Medium-hard |
| 5 | 6 | Hard |

### Week-by-Week Plan

**Week 1 — Algebra** (11 skills × 5 = 55 questions)
```
linear_eq_one_var            linear_eq_word_problems       linear_eq_two_var
graphs_linear                linear_functions              linear_functions_word_problems
systems_linear_eq            systems_linear_word_problems
linear_inequalities_one_var  linear_inequalities_two_var   systems_linear_inequalities
```

**Week 2 — Advanced Math** (12 skills × 5 = 60 questions)
```
equivalent_expressions       polynomial_operations         factoring
quadratic_equations          quadratic_functions           exponential_functions
polynomial_functions         radicals_rational_exponents   rational_expressions
radical_rational_abs_equations  nonlinear_eq_systems       function_notation
```

**Week 3 — Problem Solving & Data** (13 skills × 5 = 65 questions)
```
ratios_rates                 proportional_relationships    unit_conversion
percentages                  data_center                   data_spread
data_distributions           scatterplots                  two_var_models
probability                  conditional_probability       inference_statistics
evaluating_claims
```

**Week 4 — Geometry & Trigonometry** (14 skills × 5 = 70 questions)
```
area_2d                      perimeter_2d                  volume_surface_area
lines_angles                 triangles                     similar_congruent_triangles
special_right_triangles      pythagorean_theorem           right_triangle_trig
law_sines_cosines            unit_circle_radians           circle_properties
circle_equations             coordinate_geometry
```

**Week 5 — R&W Part 1** (9 skills × 5 = 45 questions)
```
central_ideas                command_evidence_textual      command_evidence_quantitative
inferences                   cross_text_connections
words_in_context             text_structure_purpose        rhetorical_devices
boundaries
```

**Week 6 — R&W Part 2** (7 skills × 5 = 35 questions)
```
subject_verb_agreement       pronoun_agreement             verb_tense_form
punctuation                  modifiers
rhetorical_synthesis         transitions
```

### Daily Routine (~45 min)
```bash
# Pick 2 skills for the day (5 questions each = 10 total)
java -jar sat-engine.jar --job=generate --count=5 --domain=algebra --skill=linear_eq_one_var
java -jar sat-engine.jar --job=generate --count=5 --domain=algebra --skill=linear_functions

# Run pipeline (unattended ~20 min)
java -jar sat-engine.jar --job=agent-review
java -jar sat-engine.jar --job=enrich

# Human review in validate.html (~20 min)
open http://localhost:8080/admin/validate.html
```

~10 questions/day → ~33 working days → Phase 1 complete in 6–7 weeks.

### Definition of "Skill Complete"
A skill is done when the coverage page shows **5 approved questions** for that skill key. Rejected questions do not count. The coverage card turns fully green.

**Status:** ✅ DECIDED

---

## ADR-035 — AI Generation Quality Standard

**Decision:** Questions generated by this pipeline are production-quality when every question passes human review. The pipeline is the tool; the review standard is the quality ceiling.

### Why the pipeline produces good questions
- **Claude as generator** — structured JSON output, skill-targeted prompts, difficulty parameter give the model clear constraints
- **Claude Opus agent review** — 9 checks per question before human ever sees it (correct answer verified, distractors checked, stem clarity, difficulty calibration, LaTeX validity)
- **Human review** — every question reviewed by the founder before approved status; nothing unapproved is ever served to students

### Where AI still makes mistakes — review checklist additions

| Area | Risk | What to check |
|---|---|---|
| **R&W passages** | Passage can be bland, circular, or internally inconsistent | Read it as a student — does the passage actually support the correct answer and *only* the correct answer? |
| **Trap answers** | Distractors sometimes too obvious or accidentally also correct | Solve each wrong answer — confirm it's wrong for a clear articulable reason |
| **Advanced Math** | Complex multi-step problems can have arithmetic errors in the explanation | Work through every explanation step yourself |
| **Diagrams** | Labels, angles, or measurements can contradict each other | Verify every labeled value matches the rendered SVG |
| **"Best answer" R&W** | Two answers can both be plausible — AI picks the weaker one as correct | If anything feels arguable, reject it |

### Competitor comparison

| | College Board | Khan Academy | Acely | **This pipeline** |
|---|---|---|---|---|
| Generation | Human-written | Human-written | AI (no human review) | AI + human review |
| Volume ceiling | 8 tests, fixed | Fixed | High | High |
| Quality ceiling | Highest | Very high | Variable (Reddit: "AI slop") | As high as the review standard |
| Skill targeting | No | Yes | Unknown | Yes — 66 skills |
| Coverage tracking | No | No | Unknown | Yes — live in validate.html |

The quality moat is not the AI — it's the **commitment to review every single question**. That is the marketing message.

**Status:** ✅ DECIDED
