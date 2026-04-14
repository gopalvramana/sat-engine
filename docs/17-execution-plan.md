# 17 — Execution Plan

---

## Core Principle

> A student who gets a diagnostic result and has nowhere to go will never come back.
> **Diagnostic without immediate action = wasted trust.**

The diagnostic and adaptive drills launch together as a single complete loop. A student never hits a dead end.

---

## Three Parallel Tracks (throughout all phases)

| Track | When | What |
|---|---|---|
| **Build** | Weekends | APIs, UI, DB migrations |
| **Questions** | Weekday evenings | Generate → review → approve questions |
| **Concept guides** | Weekday evenings | Curate JSON concept guides per skill |

Both content tracks run every evening independently of code work. Questions and concept guides are the most likely bottlenecks for Phase 1 launch.

---

## Critical Path

```
#59 Prereq graph
  → #87 dependency_type
    → #62 GenerateStage modes
      → #63 Generate diagnostic questions (content)
        ↓
        #64 DB migrations  ──→  #65 Diagnostic API  ──→  #67 Diagnostic UI
                           ──→  #69 Prereq check    ──→  #73 Drill UI
                           ──→  #70 Difficulty API        ↓
                           ──→  #71 Foundations API  ──→  #74 Foundations UI
                                                          ↓
                                              ★ LAUNCH: Full loop
```

---

## Phase 0 — Infrastructure
**Deliverable:** Pipeline generates right questions for the right pool. Admin dashboard tracks both pools. No student-facing changes.

### Sprint 1 (Weekend 1)
All taxonomy JSON changes — do together in one sitting.

| Issue | Task | Depends on |
|---|---|---|
| #59 | Add prerequisite graph to `sat_taxonomy.json` | — |
| #60 | Add `poolTarget` + `hasConceptGuide` fields per skill | — |
| #87 | Add `dependency_type` (HARD/SOFT) to prerequisite links | #59 |

### Sprint 2 (Weekend 2)

| Issue | Task | Depends on |
|---|---|---|
| #62 | `GenerateStage` mode flag: DIAGNOSTIC / DRILL / TEST | #59, #60, #87 |
| #61 | Spread dashboard: two-pool view | #60 |

### Content track A — Questions (starts Sprint 2, runs every evening)

| Issue | Task | Gate for |
|---|---|---|
| #63 | 200 diagnostic questions (d3–d4, all 66 skills) | Phase 1 launch |
| #75 | 600 drill questions (Algebra + Advanced Math) | Phase 1 launch |
| #80 | 940 test-pool questions (all domains, `pool: test`) | Phase 2 launch |

### Content track B — Concept Guides (starts Sprint 1, runs every evening)

27 curated JSON files. SAT-filtered — no JEE-only content. See issue #91 for full checklist and schema.

| Priority | Guides | Gate for |
|---|---|---|
| **P1** | Geometry (11 files): `circle_properties`, `circle_equations`, `special_right_triangles`, `right_triangle_trig`, `pythagorean_theorem`, `triangles`, `similar_congruent_triangles`, `lines_angles`, `area_2d`, `coordinate_geometry`, `unit_circle_radians` | Phase 1 launch |
| **P1** | Algebra (5 files): `linear_functions`, `systems_linear_eq`, `linear_eq_two_var`, `linear_inequalities_two_var`, `equivalent_expressions` | Phase 1 launch |
| **P2** | Advanced Math (5 files): `quadratic_equations`, `quadratic_functions`, `exponential_functions`, `function_notation`, `radicals_rational_exponents` | Phase 2 launch |
| **P2** | PS & Data (3 files): `probability`, `scatterplots`, `inference_statistics` | Phase 2 launch |
| **P2** | R&W (3 files): `boundaries`, `subject_verb_agreement`, `transitions` | Phase 2 launch |

```
★ Phase 0 complete when:
  Taxonomy has prereq graph + dependency_type + poolTarget + hasConceptGuide
  GenerateStage runs in DIAGNOSTIC / DRILL / TEST modes
  Spread dashboard shows drill vs test pool separately
  concept-guides/ directory created with at least P1 guides (16 files)
```

---

## Phase 1 — Complete Loop (Diagnostic + Drills)

**Why combined:** Building the diagnostic without drills leaves students with nowhere to go after seeing their skill map. Both ship together as a single student-facing launch.

**Deliverable:** Student signs up → two-stage diagnostic → skill map with confidence levels → basic drill plan → drills weak skills → mastery updates → foundations micro-lesson if floor gap detected. One complete end-to-end loop.

### Sprint 3 (Weekend 3)
All DB migrations in one sprint — never revisit schema for this phase.

| Issue | Task | Depends on |
|---|---|---|
| #64 | DB: `user_skill_mastery` Flyway migration | Phase 0 done |
| #72 | DB: add `errorType` column to `session_answer` | Phase 0 done |
| #88 | Mastery score calculation service (recency-weighted) | #64 |

### Sprint 4 (Weekend 4)
Diagnostic API + Drill prerequisite API in parallel — both needed for the complete loop.

| Issue | Task | Depends on |
|---|---|---|
| #65 | API: two-stage diagnostic session | #64 |
| #69 | API: prerequisite check before drill start | #59, #87 |

### Sprint 5 (Weekend 5)

| Issue | Task | Depends on |
|---|---|---|
| #66 | API: skill map endpoint with confidence levels | #64, #65 |
| #70 | API: rolling 4-question difficulty adjustment | #69 |
| #71 | API: foundations micro-lesson session type | #69 |

### Sprint 6 (Weekend 6)
Diagnostic UI + Skill map UI + Basic plan UI.

| Issue | Task | Depends on |
|---|---|---|
| #67 | UI: diagnostic test screen | #65 |
| #68 | UI: skill map with confidence badges + basic drill plan | #66 |

**Basic plan logic (no formula yet):**
```
1. Take all Weak + Likely Weak skills
2. Order by prerequisite depth (foundational first — HARD prereqs respected)
3. Show top 3 with label: "Start here — fix these first"
```

### Sprint 7 (Weekend 7)
Drill UIs — complete the loop.

| Issue | Task | Depends on |
|---|---|---|
| #73 | UI: adaptive drill session screen | #69, #70 |
| #74 | UI: foundations micro-lesson screen | #71 |

```
★ PHASE 1 LAUNCH — Complete Loop
  Sign up
  → Two-stage diagnostic (30–44Q · ~25 min)
     Stage 1: 3Q × 8 domains = 24Q → Strong / Developing / Weak per domain
     Stage 2: 2Q × 2–3 foundational skills in each Weak domain
  → Skill map (Measured / Inferred weak / Inferred strong / Untested)
  → Basic drill plan: top 3 weak skills in prereq order
  → Drill session: adaptive difficulty, rolling 4Q window
  → Floor gap? → Foundations micro-lesson (5×d1-d2 + 2 bridge at d4)
  → Mastery updates on skill map after every session

  Content gate:
    200 diagnostic questions approved (#63)
    600 drill questions approved for Algebra + Advanced Math (#75)
```

---

## Phase 2 — Full Practice Tests

**Deliverable:** Student can take a timed 98-question practice test mirroring real SAT. Score report with domain bands and skill breakdown. Full test is a progress checkpoint — student reaches it via skill map, not as an entry point.

### Sprint 8 (Weekend 8)

| Issue | Task | Depends on |
|---|---|---|
| #76 | API: full practice test (98Q, timed, adaptive Module 2) | Phase 1 done |
| #77 | API: score report (domain bands, skill breakdown) | #76 |

### Sprint 9 (Weekend 9)

| Issue | Task | Depends on |
|---|---|---|
| #78 | UI: timed exam mode | #76 |
| #79 | UI: score report screen | #77 |

```
★ PHASE 2 LAUNCH
  Skill map → "Ready for a full test?"
  → 98Q timed exam (Module 1 → adaptive Module 2)
  → Score report: estimated score + domain bands + skill breakdown
  → Skill map updated from test results

  Content gate: 940 test-pool questions approved (#80)
```

---

## Phase 3 — Error Intelligence

**Deliverable:** Every wrong answer classified by error type. Student sees WHY they keep failing a skill. Trap explanations surface in drill feedback.

### Sprint 10 (Weekend 10)

| Issue | Task | Depends on |
|---|---|---|
| #89 | Build `MistakeClassifierService` (trapCategory + time → errorType) | #72 |
| #81 | Classify wrong answers — store `errorType` on every wrong answer | #89 |

### Sprint 11 (Weekend 11)

| Issue | Task | Depends on |
|---|---|---|
| #82 | Show dominant error type badge on skill map | #81 |
| #83 | Show trap explanation in drill feedback panel | #81 |

```
★ PHASE 3 LAUNCH
  Wrong answer in drill → "⚠️ Common trap: [trapExplanation]"
  Skill map → each skill shows:
    CONCEPT / APPLICATION / SETUP / CARELESS badge
```

---

## Phase 4 — Smart Recommendations

**Deliverable:** Platform tells student what to work on — no guessing. Basic plan upgraded to smart plan with domain weights and test date. Mastered skills resurface automatically. Topic Refresher after every drill.

### Sprint 12 (Weekend 12)

| Issue | Task | Depends on |
|---|---|---|
| #90 | Implement priority formula (domain_weight × time_factor × mastery gap) | Phase 3 data |
| #84 | Upgrade drill plan: smart ordering with priority formula | #90 |

### Sprint 13 (Weekend 13)

| Issue | Task | Depends on |
|---|---|---|
| #85 | Spaced repetition: resurface mastered skills after 7–14 days | #84 |
| #86 | Topic Refresher screen after drill session | Phase 1 drill data |

```
★ PHASE 4 LAUNCH — Full Product
  Log in → "Your plan this week" (3–4 skills, smart-ordered by impact)
  → Drill → After session: Topic Refresher for gap skills
  → Mastered skills auto-resurface after 7–14 days
  → Plan adapts as test date approaches
```

---

## Sprint Summary

| Sprint | Weekend | Build | Questions | Concept guides |
|---|---|---|---|---|
| 1 | W1 | #59, #60, #87 — taxonomy | — | Start P1 guides (Geometry) |
| 2 | W2 | #62, #61 — pipeline + dashboard | Start generating | Continue Geometry |
| 3 | W3 | #64, #72, #88 — all DB migrations | ~80Q | Complete Geometry (11 files) |
| 4 | W4 | #65, #69 — diagnostic + prereq APIs | ~130Q | Start Algebra (5 files) |
| 5 | W5 | #66, #70, #71 — skill map + drill APIs | ~180Q | Complete Algebra |
| 6 | W6 | #67, #68 — diagnostic + skill map UI | ~220Q + 100 drill Q | **16 P1 guides done ✅** |
| 7 | W7 | #73, #74 — drill UIs → **Phase 1 launches** | **200Q + 600Q ✅** | **16 P1 guides ✅** |
| 8 | W8 | #76, #77 — test APIs | Continue test pool | Start P2 guides (AdvMath) |
| 9 | W9 | #78, #79 — test UIs → **Phase 2 launches** | **940Q ✅** | **27 guides done ✅** |
| 10 | W10 | #89, #81 — classifier | Continue | — |
| 11 | W11 | #82, #83 — error UIs → **Phase 3 launches** | Continue | — |
| 12 | W12 | #90, #84 — smart plan | Continue | — |
| 13 | W13 | #85, #86 — resurface + refresher → **Phase 4 launches** | Continue | — |

**13 weekends → full product (~3 months)**

---

## Content Gates

| Launch | Questions | Concept guides | Notes |
|---|---|---|---|
| Phase 1 | 200 diagnostic + 600 drill (Algebra + AdvMath) | 16 P1 guides (Geometry + Algebra) | All needed together |
| Phase 2 | 940 test-pool questions | 27 guides complete | All 8 domains |
| Full product | ~3,390 drill questions | 27 guides | All 66 skills × 50 |

**Start both content tracks from Sprint 1.** Concept guides can be written on weekday evenings alongside question generation — they take ~20 min per skill to curate carefully.
