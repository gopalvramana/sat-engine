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
