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

**Decision:** Python script `generate_questions.py` handles all generation.

**Daily evening routine (45–60 minutes):**
1. 7:00 PM — Run: `python3 generate_questions.py --count 20` (15 min unattended)
2. 7:15 PM — Open `review_questions.html`, load batch file, review visually (30 min)
3. 8:00 PM — Done. ~16 reviewed questions added to bank.

**Weekly output:** ~80 reviewed questions (20/day × 5 days × 80% pass rate)

**Time to 500 questions:** 6–7 weeks of evenings

**Status:** ✅ DECIDED — Script built and running

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

The generation script handles weighted random selection automatically — distribution builds up naturally without manual tracking.

**Status:** ✅ DECIDED

---

## ADR-032 — Question JSON Format

Every generated question is stored in this format (maps directly to DB schema for easy import):

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
  "explanation": "Subtract 7 from both sides: \\(3x = 15\\). Divide by 3: \\(x = 5\\).",
  "explanationShort": "Isolate x in two steps.",
  "passageText": null,
  "passageSource": null,
  "diagram": null,
  "calculatorOk": true,
  "source": "ai_generated",
  "reviewed": false,
  "reviewNotes": "",
  "generatedAt": "2026-03-23T20:30:00"
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

## Generation Script — Quick Reference

```bash
# Generate 20 random questions (all types, all difficulties)
python3 generate_questions.py --count 20

# Generate 50 Math only
python3 generate_questions.py --count 50 --section math

# Generate 30 R&W only
python3 generate_questions.py --count 30 --section reading_writing

# Custom output location
python3 generate_questions.py --count 20 --output questions/my_batch.json
```

**Output location:** `questions/batch_YYYYMMDD_HHMMSS.json`

**Review tool:** Open `review_questions.html` in Chrome → Load batch file → Review visually → Download reviewed file

---

## Progress Tracker

Track this weekly:

| Domain | Code | Target | Generated | Reviewed | Passed | Status |
|--------|------|--------|-----------|----------|--------|--------|
| Algebra | ALG | 105 | | | | |
| Advanced Math | ADV | 105 | | | | |
| Problem Solving | PS | 45 | | | | |
| Geometry/Trig | GEO | 45 | | | | |
| Information/Ideas | INF | 52 | | | | |
| Craft/Structure | CRF | 56 | | | | |
| Expression Ideas | EXP | 40 | | | | |
| Standard English | ENG | 52 | | | | |
| **TOTAL** | | **500** | | | | |
