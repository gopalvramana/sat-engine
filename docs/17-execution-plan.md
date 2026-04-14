# 17 — Execution Plan

---

## Core Principle

> A student who gets a diagnostic result and has nowhere to go will never come back.
> **Diagnostic without immediate action = wasted trust.**

The diagnostic and adaptive drills launch together as a single complete loop. A student never hits a dead end.

---

## Two Parallel Tracks (throughout all phases)

| Track | When | What |
|---|---|---|
| **Build** | Weekends | APIs, UI, DB migrations |
| **Content** | Weekday evenings | Generate → review → approve questions |

Question generation runs every evening regardless of which sprint is active. It is the most likely bottleneck for every phase launch.

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
| #60 | Add `poolTarget` field per skill | — |
| #87 | Add `dependency_type` (HARD/SOFT) to prerequisite links | #59 |

### Sprint 2 (Weekend 2)

| Issue | Task | Depends on |
|---|---|---|
| #62 | `GenerateStage` mode flag: DIAGNOSTIC / DRILL / TEST | #59, #60, #87 |
| #61 | Spread dashboard: two-pool view | #60 |

### Content — starts Sprint 2, runs every evening

| Issue | Task | Gate for |
|---|---|---|
| #63 | 200 diagnostic questions (d3–d4, all 66 skills) | Phase 1 launch |
| #75 | 600 drill questions (Algebra + Advanced Math) | Phase 1 launch |
| #80 | 940 test-pool questions (all domains, `pool: test`) | Phase 2 launch |

```
★ Phase 0 complete when:
  Taxonomy has prereq graph + dependency_type + poolTarget
  GenerateStage runs in DIAGNOSTIC / DRILL / TEST modes
  Spread dashboard shows drill vs test pool separately
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

| Sprint | Weekend | Build | Content milestone |
|---|---|---|---|
| 1 | W1 | #59, #60, #87 — taxonomy | Start generating |
| 2 | W2 | #62, #61 — pipeline + dashboard | ~30Q generated |
| 3 | W3 | #64, #72, #88 — all DB migrations | ~80Q generated |
| 4 | W4 | #65, #69 — diagnostic + prereq APIs | ~130Q generated |
| 5 | W5 | #66, #70, #71 — skill map + drill APIs | ~180Q generated |
| 6 | W6 | #67, #68 — diagnostic + skill map UI | ~220Q + 100 drill Q |
| 7 | W7 | #73, #74 — drill UIs → **Phase 1 launches** | **200Q + 600Q ✅** |
| 8 | W8 | #76, #77 — test APIs | Continue test pool |
| 9 | W9 | #78, #79 — test UIs → **Phase 2 launches** | **940Q test pool ✅** |
| 10 | W10 | #89, #81 — classifier | Continue |
| 11 | W11 | #82, #83 — error UIs → **Phase 3 launches** | Continue |
| 12 | W12 | #90, #84 — smart plan | Continue |
| 13 | W13 | #85, #86 — resurface + refresher → **Phase 4 launches** | Continue |

**13 weekends → full product (~3 months)**

---

## Content Gates

| Launch | Questions needed | Pool | Notes |
|---|---|---|---|
| Phase 1 | 200 diagnostic (d3–d4) + 600 drill (Algebra + AdvMath) | practice | Both needed together |
| Phase 2 | 940 test-pool questions | test | All 8 domains |
| Full product | ~3,390 drill questions | practice | All 66 skills × 50 |

**Start generating today.** Content is the most likely bottleneck — not code.
