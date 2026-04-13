# 16 — Question Pool Strategy

---

## Two Separate Pools

Questions are tagged at generation time. The pools must never be mixed from the student's perspective.

| Pool | Tag | Purpose | Rule |
|---|---|---|---|
| Drill pool | `pool: practice` | Adaptive drills, diagnostic, micro-lessons | Can be seen many times across sessions |
| Test pool | `pool: test` | Full practice tests only | Never shown in drills — preserves freshness |
| Shared | `pool: both` | Use sparingly | Only for low-stakes warm-up content |

A question seen in drill mode is **contaminated** for that student if later used in a practice test. The separation is absolute.

---

## Pool Size Targets

### Why ≥5 Per Skill is Not Enough

A serious prep student (1100–1350 aiming for 1400+) over a 12-week cycle:

| Session type | Volume | Questions per weak skill |
|---|---|---|
| Full practice tests | 1/week × 12 = 12 tests | ~18 (1.5 per test × 12) |
| Focused drill sessions | 3/week × 10 weeks = 30 sessions | ~80 (8-10 per session) |
| Quick refreshers | Ad hoc | ~10 |
| **Total per weak skill** | | **~100 exposures** |

A student will identify 8–15 weak skills and work them repeatedly. With a 21-day non-repeat window (don't show the same question twice within 3 weeks), the pool must hold at least **40 unique questions per skill** to stay fresh for an active student.

### Drill Pool Target Per Skill

| Difficulty | Standard skill | Floor skill |
|---|---|---|
| d1–d2 | 3–4 each | **10–12 each** (micro-lesson reserve) |
| d3–d4 | 6–8 each | 6–8 each |
| d5–d6 | 8–10 each | 8–10 each |
| d7 | 3–4 | 3–4 |
| **Total** | **~50** | **~60** |

Floor skills need more d1–d2 questions because that bucket is reserved exclusively for foundations micro-lessons and must not be shared with general drill sessions.

### Test Pool Target

10 full practice tests × 98 questions = **940 questions**

| Domain | Per test | 10 tests |
|---|---|---|
| Math — Algebra | 14 | 140 |
| Math — Advanced Math | 14 | 140 |
| Math — PS & Data Analysis | 6 | 60 |
| Math — Geometry & Trig | 6 | 60 |
| R&W — Information & Ideas | 14 | 140 |
| R&W — Craft & Structure | 15 | 150 |
| R&W — Expression of Ideas | 11 | 110 |
| R&W — Standard English | 14 | 140 |
| **Total** | **98** | **~940** |

### Grand Total

| Pool | Questions |
|---|---|
| Diagnostic pool (subset of drill pool) | ~200 |
| Drill pool (66 skills × ~50) | ~3,390 |
| Test pool (10 tests × 98) | ~940 |
| **Grand total** | **~4,330** |

---

## Generation Priority Order

Current state: ~200–400 approved questions. Generation is the critical path — no phase can launch without its pool threshold.

```
Priority 1 — Diagnostic pool
  Target: 200 questions
  Spec:   d3–d4 only · 2–3 per skill · pool: practice
  Gate:   Phase 1 (Diagnostic Test) cannot launch without this

Priority 2 — Drill pool, Algebra + Advanced Math first
  Target: 1,000 questions (~42 skills covered at ~24/skill)
  Spec:   Full d1–d7 spread · pool: practice
  Gate:   Phase 2 (Adaptive Drills) needs critical mass here

Priority 3 — Drill pool, remaining skills
  Target: 3,390 total
  Spec:   Full d1–d7 spread · pool: practice

Priority 4 — Test pool
  Target: 940 questions
  Spec:   Mirrors real SAT domain distribution · pool: test
  Gate:   Phase 3 (Full Practice Tests)
```

---

## Spread Dashboard Updates Needed

The current spread dashboard (`/admin/spread.html`) shows a single unified pool target. It needs to be updated to reflect the two-pool model:

- [ ] Add pool filter: **Drill Pool | Test Pool | All**
- [ ] Show diagnostic progress separately (200 question target at d3–d4)
- [ ] Show floor skill d1–d2 bucket depth (micro-lesson reserve)
- [ ] Update section targets to reflect drill pool (not test-question count)

---

## Generation Run Modes

The generation pipeline should support a `--mode` flag:

| Mode | Difficulty | Pool tag | Per-run target |
|---|---|---|---|
| `DIAGNOSTIC` | d3–d4 only | `practice` | 2–3 per uncovered skill |
| `DRILL` | Full d1–d7 spread, deficit-weighted | `practice` | Per-skill gap fill |
| `TEST` | Mirrors SAT distribution | `test` | Domain-proportional |

Default mode: `DRILL`. `DIAGNOSTIC` mode runs first until the 200-question diagnostic threshold is met.
