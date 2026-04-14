# 17 — Execution Plan

---

## Two Parallel Tracks

Every sprint runs two tracks simultaneously. They never block each other.

| Track | When | What |
|---|---|---|
| **Build track** | Weekends | Spring Boot APIs, React UI, DB migrations |
| **Content track** | Weekday evenings | Question generation → review → approve |

Question generation is **always running in the background**. The content track gates Phase 1, 2, and 3 launches independently of code completion.

---

## Critical Path

The single chain that everything depends on:

```
#59 Prereq graph in taxonomy
  → #87 dependency_type added
    → #62 GenerateStage mode flag
      → #63 Generate 200 diagnostic questions
        → #65 Diagnostic session API
          → #67 Diagnostic UI
            ★ LAUNCH: Phase 1 — Student can take diagnostic
              → #69 Prerequisite check API
                → #70 Rolling difficulty API
                  → #73 Drill session UI
                    ★ LAUNCH: Phase 2 — Student can drill weak skills
                      → #76 Full practice test API
                        ★ LAUNCH: Phase 3 — Student can take a full test
```

---

## Phase 0 — Infrastructure

**Deliverable:** Pipeline is ready to generate the right questions for the right pool. Admin can track both pools on the dashboard.

**No student-facing changes.**

### Sprint 1 (Weekend 1)

These three can be done together — all taxonomy JSON changes:

| Issue | Task | Depends on |
|---|---|---|
| #59 | Add prerequisite graph to `sat_taxonomy.json` | — |
| #60 | Add `poolTarget` field per skill | — |
| #87 | Add `dependency_type` (HARD/SOFT) to prerequisite links | #59 |

### Sprint 2 (Weekend 2)

| Issue | Task | Depends on |
|---|---|---|
| #62 | `GenerateStage` mode flag: DIAGNOSTIC / DRILL / TEST | #59, #60 |
| #61 | Spread dashboard: two-pool view (drill vs test) | #60 |

### Content track — starts immediately, runs throughout

| Issue | Task | Target |
|---|---|---|
| #63 | Generate 200 diagnostic questions (d3–d4, all 66 skills) | Before Phase 1 launch |
| #75 | Generate drill pool — Algebra + Advanced Math (1,200 questions) | Before Phase 2 launch |
| #80 | Generate test pool — 940 questions, pool: test | Before Phase 3 launch |

**Gate:** Phase 1 cannot launch until #63 is complete (200 diagnostic questions approved).

---

## Phase 1 — Diagnostic Test

**Deliverable:** A new student signs up, takes a 35-question diagnostic, and sees a skill map showing exactly where they are strong, developing, or weak.

**This is the first student-facing feature. Everything before this is internal.**

### Sprint 3 (Weekend 3)

| Issue | Task | Depends on |
|---|---|---|
| #64 | DB: `user_skill_mastery` Flyway migration | Phase 0 done |
| #88 | Mastery score calculation service (recency-weighted) | #64 |

### Sprint 4 (Weekend 4)

| Issue | Task | Depends on |
|---|---|---|
| #65 | API: diagnostic session (start, answer, complete) | #64 |
| #66 | API: skill map endpoint `GET /users/{id}/skill-map` | #64, #65 |

### Sprint 5 (Weekend 5)

| Issue | Task | Depends on |
|---|---|---|
| #67 | UI: diagnostic test screen | #65 |
| #68 | UI: skill map screen | #66 |

```
★ MILESTONE — Phase 1 Launch
  Student flow: Sign up → Diagnostic (35Q) → Skill Map
  Content gate: #63 must have 200 approved diagnostic questions
```

---

## Phase 2 — Adaptive Drills

**Deliverable:** Student can drill any weak skill from their skill map. The engine checks prerequisites, blocks or warns based on HARD/SOFT type, and triggers foundations micro-lessons for floor skill gaps. Mastery updates after every session.

### Sprint 6 (Weekend 6)

| Issue | Task | Depends on |
|---|---|---|
| #72 | DB: add `errorType` column to `session_answer` | Phase 1 done |
| #69 | API: prerequisite check before drill start | #59, #87 (Phase 0) |

### Sprint 7 (Weekend 7)

| Issue | Task | Depends on |
|---|---|---|
| #70 | API: rolling 4-question difficulty adjustment | #69 |
| #71 | API: foundations micro-lesson session type | #69 |

### Sprint 8 (Weekend 8)

| Issue | Task | Depends on |
|---|---|---|
| #73 | UI: adaptive drill session screen | #69, #70 |
| #74 | UI: foundations micro-lesson screen | #71 |

```
★ MILESTONE — Phase 2 Launch
  Student flow: Skill Map → Pick weak skill → Prerequisite check
                → Drill session (adaptive difficulty)
                → Foundations micro-lesson (if floor gap)
                → Mastery updates on skill map
  Content gate: #75 must have ~600 drill questions approved
                (Algebra + Advanced Math at minimum)
```

---

## Phase 3 — Full Practice Tests

**Deliverable:** Student can take a timed 98-question practice test that mirrors the real SAT (adaptive module 2). Score report shows domain band breakdown and skill-level performance.

### Sprint 9 (Weekend 9)

| Issue | Task | Depends on |
|---|---|---|
| #76 | API: full practice test session (98Q, timed, adaptive module 2) | Phase 2 done |
| #77 | API: score report (domain bands, skill breakdown) | #76 |

### Sprint 10 (Weekend 10)

| Issue | Task | Depends on |
|---|---|---|
| #78 | UI: timed exam mode | #76 |
| #79 | UI: score report screen | #77 |

```
★ MILESTONE — Phase 3 Launch
  Student flow: Skill Map → "Ready for a full test" →
                98Q timed test → Score report → Updated skill map
  Content gate: #80 must have ~940 test-pool questions approved
  Note: Full test is positioned as a progress checkpoint,
        not the entry point — student reaches it via the skill map
```

---

## Phase 4 — Error Intelligence

**Deliverable:** Every wrong answer is classified by error type (CONCEPT / APPLICATION / SETUP / CARELESS). The dominant error type for each skill appears on the skill map. Trap explanations appear on wrong answers.

### Sprint 11 (Weekend 11)

| Issue | Task | Depends on |
|---|---|---|
| #89 | Build `MistakeClassifierService` (trapCategory + time → errorType) | #72 (Phase 2) |
| #81 | Classify wrong answers and store `errorType` | #89 |

### Sprint 12 (Weekend 12)

| Issue | Task | Depends on |
|---|---|---|
| #82 | Show dominant error type on skill map | #81 |
| #83 | Show trap explanation in drill feedback panel | #81 |

```
★ MILESTONE — Phase 4 Launch
  Student flow: Drill wrong answer → See "Common Trap" warning
                Skill Map → Each skill shows error badge
                (CONCEPT / APPLICATION / SETUP / CARELESS)
```

---

## Phase 5 — Smart Recommendations

**Deliverable:** The platform tells the student what to work on — no more deciding for themselves. Weekly drill plan auto-generated. Mastered skills resurface automatically. Topic refresher shown after drill.

### Sprint 13 (Weekend 13)

| Issue | Task | Depends on |
|---|---|---|
| #90 | Implement weekly drill plan priority formula | Phase 4 mastery data |
| #84 | Auto-generate weekly drill plan from skill map | #90 |

### Sprint 14 (Weekend 14)

| Issue | Task | Depends on |
|---|---|---|
| #85 | Spaced repetition: resurface mastered skills after 7–14 days | #84 |
| #86 | Topic Refresher screen after drill session | Phase 2 drill data |

```
★ MILESTONE — Phase 5 Launch (Full Product)
  Student flow: Log in → See "Your plan for this week" (3–4 skills)
                → Drill → Mastered skills resurface automatically
                → After drill: Topic Refresher for gap skills
```

---

## Full Dependency Map

```
PHASE 0                          PHASE 1              PHASE 2                    PHASE 3
#59 prereq graph ──────────────────────────────────► #69 prereq check API
#60 poolTarget   ──► #62 mode ──► #63 content gate ► #65 diagnostic API ──► #70 drill difficulty ──► #76 test API
#87 dep_type ───────────────────────────────────────► #69                  ──► #71 foundations API ──► #77 score
#61 dashboard                    #64 mastery DB ────► #88 mastery score    ──► #73 drill UI        ──► #78 exam UI
                                                   ──► #65                 ──► #74 foundations UI  ──► #79 score UI
                                                   ──► #66 skill map API
                                                   ──► #67 diagnostic UI
                                                   ──► #68 skill map UI
                                                   ──► #72 errorType col

PHASE 4                          PHASE 5
#72 ──► #89 classifier ──► #81 classify answers ──► #90 priority formula ──► #84 weekly plan ──► #85 spaced rep
                        ──► #82 skill map UI    ──► #86 topic refresher
                        ──► #83 trap UI
```

---

## Parallel Work Summary Per Sprint

| Sprint | Weekend | Build track | Content track |
|---|---|---|---|
| 1 | W1 | #59, #60, #87 (taxonomy) | Start diagnostic generation |
| 2 | W2 | #62 (pipeline), #61 (dashboard) | Continue generation |
| 3 | W3 | #64 (DB), #88 (mastery calc) | Continue generation |
| 4 | W4 | #65, #66 (APIs) | Continue generation |
| 5 | W5 | #67, #68 (UI) — **Phase 1 launch** | 200Q gate must be hit |
| 6 | W6 | #72 (DB), #69 (prereq API) | Start drill pool generation |
| 7 | W7 | #70, #71 (APIs) | Continue drill generation |
| 8 | W8 | #73, #74 (UI) — **Phase 2 launch** | 600Q gate must be hit |
| 9 | W9 | #76, #77 (APIs) | Start test pool generation |
| 10 | W10 | #78, #79 (UI) — **Phase 3 launch** | 940Q gate must be hit |
| 11 | W11 | #89, #81 (classifier) | Continue pool top-up |
| 12 | W12 | #82, #83 (UI) — **Phase 4 launch** | Continue |
| 13 | W13 | #90, #84 (plan formula + API) | Continue |
| 14 | W14 | #85, #86 (UI) — **Phase 5 launch** | Continue |

**14 weekends from now to full product.** At 1 weekend per sprint ≈ 3.5 months.

---

## Content Gate Summary

| Gate | Questions needed | Pool | Status |
|---|---|---|---|
| Phase 1 launch | 200 (d3–d4, all 66 skills) | practice | 🔴 Not started |
| Phase 2 launch | 600 (Algebra + AdvMath drill) | practice | 🔴 Not started |
| Phase 3 launch | 940 (all domains, full tests) | test | 🔴 Not started |
| Full product | ~3,390 (all 66 skills, 50/skill) | practice | 🔴 Long-term |

Start generating **today** — the content track is independent of all code work and is the most likely bottleneck for Phase 1 and 2 launches.
