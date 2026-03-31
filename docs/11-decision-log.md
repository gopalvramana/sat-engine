# 11 — Complete Decision Log

> All 41 decisions in one place. For full detail on each decision see the relevant section document.

---

## How to Use This Log

- **Add** a new row every time a significant decision is made
- **Update Status** as decisions are implemented or revised
- **Never delete** — if a decision changes, add a new row with the updated decision and mark the old one as REVISED

---

## Status Key
- ✅ DECIDED — Final, implemented or ready to implement
- 🔄 IN PROGRESS — Decision made, implementation underway
- ⬜ PENDING — Not yet decided
- 🔁 REVISED — Was decided, now changed (see newer row)

---

## All Decisions

| ADR | Decision | Chosen | Section | Status |
|-----|----------|--------|---------|--------|
| 001 | What we are building | AI tutoring platform — not a test bank with chatbot | Vision | ✅ |
| 002 | Target student | Any 1100–1350 SAT student. Indian-American community as warm launch channel only | Vision | ✅ |
| 003 | Core differentiator | 3-tab structured AI panel (Solution, Concept, Prerequisites) — separate live API calls | Vision | ✅ |
| 004 | Math notation format | LaTeX in PostgreSQL text columns. `\( \)` inline, `\[ \]` display | Architecture | ✅ |
| 005 | Diagram architecture | Three types: svg_programmatic, chartjs, static_image | Architecture | ✅ |
| 006 | SVG renderer pattern | JavaScript dispatcher buildSVG(config) with per-shape functions | Architecture | ✅ |
| 007 | Rendering init order | Chart.js → SVG → KaTeX (KaTeX fires last on onload) | Architecture | ✅ |
| 008 | DB core schema | questions + diagrams tables, nullable diagram_id FK | Architecture | ✅ |
| 009 | Diagram config storage | JSONB columns svg_config and chart_config in diagrams table | Architecture | ✅ |
| 010 | External ID format | {SECTION}-{DOMAIN}-{SEQ} e.g. MATH-ALG-001 | Architecture | ✅ |
| 011 | Storage estimate | ~32MB for 5,000 questions. Supabase free tier covers ~4,000 students | Architecture | ✅ |
| 012 | AI response caching | questions_ai_cache table. First student generates, everyone else gets cache | Architecture | ✅ |
| 013 | App hosting | Railway.app. GitHub push deploys. Auto SSL. $5–20/month | Infrastructure | ✅ |
| 014 | Monthly cost model | $6.25 (launch) → $21 (100 students) → $56 (500 students) | Infrastructure | ✅ |
| 015 | JVM memory | -Xms256m -Xmx400m -XX:+UseG1GC for 512MB Railway instance | Infrastructure | ✅ |
| 016 | Local development | Docker Compose, pgvector/pgvector:pg16, localhost:8080 | Infrastructure | ✅ |
| 017 | Exam vs review modes | Exam = no AI + timer. Review = full AI + no timer. Strict separation. | Product | ✅ |
| 018 | SAT test structure | 98 questions: 54 R&W (27+27) + 44 Math (22+22) | Product | ✅ |
| 019 | Adaptive branching | ≥75% Module 1 → Hard Module 2. <75% → Easy Module 2 | Product | ✅ |
| 020 | Template architecture | Zero hardcoded content. All from Spring Boot model. Data-driven. | Product | ✅ |
| 021 | Answer checking | Client-side JavaScript with data attributes. No server round-trip. | Product | ✅ |
| 022 | Score report | Scaled score + domain breakdown + time analytics + difficulty spread | Product | ✅ |
| 023 | AI panel architecture | 3 tabs, lazy loaded, cached per question, streams via SSE | AI | ✅ |
| 024 | AI model selection | Haiku 4.5 for all now. Route by difficulty post-launch. | AI | ✅ |
| 025 | AI cost model | ~$0.31/review. ~$0.50/student/month at scale. 97% gross margin. | AI | ✅ |
| 026 | Interactive AI build order | Error Autopsy → Socratic Hints → Tutor Chat → Debate Mode → What-If | AI | 🔄 |
| 027 | Open source model policy | Add only after launch when usage data justifies effort | AI | ✅ |
| 028 | Launch question count | 500–600 reviewed questions. ~5–6 full tests. | Content | ✅ |
| 029 | Human review policy | Every question reviewed before going live. No exceptions. | Content | ✅ |
| 030 | Question generation workflow | generate_questions.py daily evenings. review_questions.html for review. | Content | ✅ |
| 031 | Domain distribution | Math 300 (ALG 105, ADV 105, PS 45, GEO 45). R&W 200 (INF 52, CRF 56, EXP 40, ENG 52). | Content | ✅ |
| 032 | Question JSON format | Schema matching DB for direct import. Includes externalId, reviewed flag, diagram object. | Content | ✅ |
| 033 | Pricing | $14.99/month. $119.99/year. First test free, no credit card. | Business | ✅ |
| 034 | H1B monetisation | Indian Pvt Ltd company, family director. Free phase now, monetise after setup. | Business | 🔄 |
| 035 | Free tier design | One full test, no credit card, no AI panel. Second test requires subscription. | Business | ✅ |
| 036 | Competitive positioning | "Teaches WHY not just WHAT." Target students burned by circular AI. | Business | ✅ |
| 037 | Distribution strategy | r/SAT + r/ApplyingToCollege primary. Indian communities as warm launch channel. No paid ads at launch. | Business | ✅ |
| 038 | Parallel tracks | Weekends = build. Evenings = questions. Never blocking each other. | Roadmap | ✅ |
| 039 | Launch scope | No mobile, ACT, AP, admin UI, study plan, advanced analytics at launch. | Roadmap | ✅ |
| 040 | Documentation tools | Notion (product + business). GitHub docs/ (technical ADRs). | Tools | ✅ |
| 041 | ADR format | Standard template: Decision, Rejected, Reason, Status for every choice. | Tools | ✅ |
| 042 | Trap Analysis → Alternative Approach | Remove Trap Analysis panel; replace with collapsible "Alternative Approach" showing a second method to solve each Math question | Pipeline / UI | ✅ |
| 043 | renderer.js deployment | Copy real file into static resources — do not use symlink. Maven does not follow symlinks when packaging JARs. | Infrastructure | ✅ |
| 044 | Math figure library (student-facing) | Evaluate Mafs (React) or JSXGraph when switching to React frontend. Current custom SVG renderer stays for admin pipeline. | Architecture | ⬜ PENDING — POC at React switch |
| 045 | Student-facing MVP stack | Build practice.html in current zero-build stack (plain JS + renderer.js + KaTeX + Chart.js) reusing existing renderer. Switch to React only when student UX complexity justifies it (200+ questions, real users, dashboards). | Architecture | 🔄 |
| 046 | Production readiness of current stack | Spring Boot + PostgreSQL + KaTeX + Chart.js are all production-grade. No stack replacement needed at scale — add load balancer, read replica, CDN as usage grows. | Infrastructure | ✅ |

---

## One-Time Data Fixes Applied

Flyway migrations that corrected bad data from earlier pipeline runs.
These are done and do not need to be repeated.

| Migration | What it fixed | Root cause |
|-----------|--------------|------------|
| V9 | Rejected RW-ALG-001 (miscategorised as algebra) | `pickSection()` was random when `--domain` given without `--section` |
| V10 | Rejected RW-ALG-002 to RW-ALG-005 (same root cause) | Same as above — fixed in `GenerateStage.sectionForDomain()` |
| V11 | MATH-ALG-017 option B: 9.67 → 9 | AI arithmetic error |
| V12 | MATH-ADV-006 option D: wrong distractor | Unrealistic distractor |
| V14 | MATH-PS-006 options: wrapped bare `\frac{}` in `\( \)` | AI omitted LaTeX delimiters in option fields — prompt hardened in V14 |

---

## Weekend TODOs (2026-04-05/06)

| # | Task | Notes |
|---|------|-------|
| 1 | **Normalize `\n` in DB** | `fixLatexEscapes()` bug stored literal `\n` (two chars) instead of actual newlines in text fields. Write a Java-based Flyway migration (V15) to replace all `\n` (backslash+n) in `question_stem`, `option_*`, `explanation_short`, `explanation_steps` with actual newline char. Then simplify `processText()` — remove the lookahead hack entirely. |
| 2 | **Build `practice.html`** | Student-facing practice page. Zero-build stack (plain JS). Reuse `renderer.js` + KaTeX + Chart.js. One question at a time, accept answer, show explanation. Reads from `/api/questions` (approved pool). |
| 3 | **Re-enrich math questions for `alternativeApproach`** | Run SQL to reset approved math questions to `reviewed`, then `--job=enrich`. Re-approve in validate.html. |
| 4 | **AI pipeline production hardening** | Add rate-limit retry logic (exponential backoff) to `ClaudeClient`. Add per-job timeout. Log token usage per question. These are needed before running large batches. |

---

## Decisions Pending

These need to be made before or during Month 2:

| # | Decision Needed | By When |
|---|----------------|---------|
| — | Indian company CA — find and engage | This week |
| — | US immigration lawyer consult on H1B revenue | Before launch |
| — | Domain name selection | Month 1, Week 2 |
| — | Stripe account setup (personal or company) | Month 2, Week 7 |
| — | SendGrid account setup | Month 2, Week 8 |
| — | Mafs vs JSXGraph POC | At React frontend switch (trigger: 200+ questions, real student users) |

---

## Template for New Decisions

When you make a new decision, add it here and in the relevant section document:

```
| ADR-042 | [Decision topic] | [What was chosen] | [Section] | 🔄 IN PROGRESS |
```

And document it fully:

**ADR-042 — [Title]**

**Decision:** What was decided.

**Rejected:** What alternatives were considered and not chosen.

**Reason:** Why this option was chosen over the alternatives.

**Status:** ✅ DECIDED / 🔄 IN PROGRESS
