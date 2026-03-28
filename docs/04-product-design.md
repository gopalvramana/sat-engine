# 04 — Product Design Decisions

---

## Core Design Principles

1. **Exam mode has zero AI** — simulates the real SAT, builds genuine skill
2. **Review mode has full AI** — deep learning after submission
3. **Templates are data-driven** — zero hardcoded question content
4. **Questions teach, not just test** — every wrong answer is a teaching moment

---

## ADR-017 — Exam Mode vs Review Mode Separation

**Decision:** Two completely distinct modes.

| | Exam Mode | Review Mode |
|--|-----------|-------------|
| AI Panel | ❌ Not available | ✅ Full 3-tab panel |
| Timer | ✅ Running | ❌ No timer |
| Correct answer visible | ❌ Hidden | ✅ Always shown |
| Purpose | Simulate real SAT | Learn from mistakes |
| API cost | $0 | ~$0.31 per review session |

**Reason:** The real SAT has no AI. Students who practice with AI available build dependency not skill. Practice scores become inflated and don't predict real test performance. Keeping AI in review mode also makes the cost model work — exam mode costs $0 in API calls.

**Status:** ✅ DECIDED

---

## ADR-018 — Full SAT Test Structure

**Decision:** Replicate the exact real Digital SAT structure.

```
Full SAT = 98 questions

Reading & Writing:
  Module 1: 27 questions  (32 min)
  Module 2: 27 questions  (32 min)
  Total: 54 questions

Math:
  Module 1: 22 questions  (35 min)
  Module 2: 22 questions  (35 min)
  Total: 44 questions

Total time: ~2 hours 14 minutes
```

**Status:** ✅ DECIDED

---

## ADR-019 — Adaptive Branching Logic

**Decision:** Module 1 score determines Module 2 difficulty.

```
Module 1 score ≥ 75% correct → Hard Module 2
                               (higher score ceiling, 700–800 range)

Module 1 score < 75% correct → Easy Module 2
                               (lower score ceiling, 400–600 range)
```

This matches College Board's actual algorithm. Hard Module 2 is where top scores come from. Students targeting 1400+ must practice getting into and succeeding in Hard Module 2.

**Status:** ✅ DECIDED

---

## ADR-020 — Data-Driven Template Architecture

**Decision:** Zero hardcoded question content in Thymeleaf templates. All content comes from the Spring Boot model attribute.

```html
<!-- Template receives data, knows nothing about questions -->
<div class="question-stem" th:utext="${question.questionStem}"></div>

<div th:if="${question.diagram != null}">
  <!-- svg_programmatic: JS reads data-config and draws -->
  <div th:if="${question.diagram.diagramType == 'svg_programmatic'}"
       class="svg-diagram"
       th:attr="data-config=${question.diagram.svgConfig}">
  </div>
  <!-- chartjs: Chart.js reads data-config and renders -->
  <canvas th:if="${question.diagram.diagramType == 'chartjs'}"
          class="chart-diagram"
          th:attr="data-config=${question.diagram.chartConfig}">
  </canvas>
</div>
```

Adding 1,000 questions requires zero template changes.

**Status:** ✅ DECIDED — Proven in api-test.html

---

## ADR-021 — Client-Side Answer Checking

**Decision:** Answer checking is done entirely in JavaScript using `data-` attributes. No server round-trip needed.

```html
<!-- Correct answer stored in hidden data attribute -->
<div id="question-meta"
     th:attr="data-correct=${question.correctAnswer},
              data-explanation=${question.explanation}"
     style="display:none">
</div>
```

Answer is recorded to the server separately for analytics — this is decoupled from the feedback display. Feedback is instant with zero latency.

**Status:** ✅ DECIDED

---

## ADR-022 — Score Report Design

**Decision:** Score report shows:
- Overall scaled score per section (200–800)
- Domain breakdown — % correct per domain
- Difficulty spread — correct vs incorrect by difficulty level
- Time analytics — time spent per question
- Comparison to previous test (if exists)
- Top 3 weak domains with recommendation

**Reason:** Students need actionable data not just a number. Domain breakdown tells them what to study next. Time analytics shows where they rush or linger (feature unique to MentoMind — we add it too).

**Status:** ✅ DECIDED

---

## Application Routes

| Route | Mode | Auth Required | Description |
|-------|------|---------------|-------------|
| `/` | — | No | Redirect to /dashboard or /landing |
| `/questions` | — | Yes | Question bank browser (admin) |
| `/test/new` | — | Yes | Start a new practice test |
| `/test/{id}/exam` | Exam | Yes | Timed test interface — no AI |
| `/test/{id}/review` | Review | Yes | Post-test review with AI panel |
| `/test/{id}/score` | — | Yes | Score report page |
| `/dashboard` | — | Yes | Student dashboard |
| `/api/questions/{extId}` | — | Yes | JSON endpoint |
| `/api/chat/{questionId}` | — | Yes | Tutor chat endpoint |
| `/api/ai/{questionId}/{tab}` | — | Yes | AI tab generation |
| `/webhooks/stripe` | — | No | Stripe webhook receiver |

---

## UI Design Decisions

### Colour System
- Math badge: `bg-blue-600 text-white`
- R&W badge: `bg-teal-600 text-white`
- Difficulty easy (1–2): green
- Difficulty medium (3–4): amber
- Difficulty hard (5–7): red
- Correct answer feedback: `bg-green-50 border-green-200`
- Incorrect answer feedback: `bg-red-50 border-red-200`

### Check Answer Button States
- Default: `bg-blue-600 text-white hover:bg-blue-700`
- After answering: `bg-slate-300 cursor-not-allowed` (disabled)
- Never reloads the page

### Passage Display (R&W questions)
- `bg-slate-50` with `border-l-4 border-teal-400`
- Source attribution in small italic text above passage
- Passage always shown before question stem
