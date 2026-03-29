# 08 — Build Roadmap

---

## Core Principle

> Practice mode first. Test mode later. Students learn through repetition by topic — not by simulating exams they haven't prepared for.

---

## Two Parallel Tracks

| Track | When | What | Time |
|-------|------|------|------|
| **Track 1: Build** | Weekends | React + Spring Boot development | 4–5 hrs/weekend |
| **Track 2: Questions** | Weekday evenings | Generate → agent review → validate → load | 45–60 min/evening |

These never block each other. By the time the app is built, the question bank is ready and waiting.

---

## Month 1 — Practice Mode

**Goal: Students can practice by topic, see immediate feedback, and use the AI panel**

| Week | Development Focus | Question Target | End State |
|------|------------------|----------------|-----------|
| Week 1 | ✅ Done — Spring Boot scaffold, Flyway V1+V2+V3, Java pipeline (GenerateStage / AgentReviewStage / EnrichStage), Admin API, validate.html served from Spring Boot | 0 approved | Running API, DB ready, full pipeline ready |
| Week 2 | React app (Vite), topic browser UI, question display with KaTeX + SVG + Chart.js | 100 approved | Can browse topics and read questions |
| Week 3 | Practice session API (start, submit answer, immediate feedback), session flow in React | 150 approved | Can answer questions and see if correct |
| Week 4 | AI Learning Panel (3 tabs: Solution / Core Concept / Prerequisites) wired to Claude API | 200 approved | Full practice loop with AI explanations |

**Month 1 deliverable:** Students can pick a math topic, work through questions by difficulty, get immediate right/wrong feedback, and open the AI panel to understand why. No auth, no payment yet.

### Practice Mode — How It Works

```
Topic Browser
  └── Algebra (32 questions)
        ├── Difficulty 1–2  → 8 questions  (Easy)
        ├── Difficulty 3–4  → 14 questions (Medium)
        └── Difficulty 5–7  → 10 questions (Hard)

Student picks topic → works questions in difficulty order →
  correct: ✓ + option to continue or open AI panel
  wrong:   ✗ + correct answer shown + AI panel auto-opens
```

### Practice Mode API Endpoints (Week 3)

```
POST /api/sessions               { mode: "practice", section, domain }
GET  /api/sessions/:id/question  → next question (ordered by difficulty)
POST /api/sessions/:id/answers   { questionId, answer } → { correct, correctAnswer }
GET  /api/review/:questionId     → explanation, coreConcept, prerequisites (for AI panel)
GET  /api/progress/me            → questions answered, correct rate per domain
```

---

## Month 2 — Auth + Payment + Polish

**Goal: The product students will pay for**

| Week | Development Focus | Question Target | End State |
|------|------------------|----------------|-----------|
| Week 5 | User auth: register, login, JWT, protected routes, React auth context | 250 approved | User accounts working |
| Week 6 | Stripe payment, webhooks, subscription enforcement, free tier (first 10 questions free) | 300 approved | Can charge money |
| Week 7 | Progress dashboard: questions answered, accuracy per topic, difficulty curve | 350 approved | Students see their growth |
| Week 8 | Polish: mobile responsiveness, loading states, error handling, email (welcome + streak) | 400 approved | Production-ready practice mode |

**Month 2 deliverable:** A product you can charge for. Practice mode + AI panel + user accounts + Stripe.

---

## Month 3 — Test Mode + Launch

**Goal: Full SAT simulation, 500+ questions, first real users**

| Week | Development Focus | Question Target | End State |
|------|------------------|----------------|-----------|
| Week 9 | Test mode: 98-question adaptive test, timer, module branching, no AI during test | 500 approved | Can take a full timed SAT |
| Week 10 | Score report: scaled score estimate, domain breakdown, question-by-question review | 550 approved | Meaningful score feedback |
| Week 11 | Landing page, SEO basics, authentic story copy, Railway + custom domain | 600 approved | Public-facing website live |
| Week 12 | Soft launch: r/SAT post, Indian parent communities, personal network | 650 approved | First real users |

**Month 3 deliverable:** Live product. Practice + Test modes. AI panel. Payment. First users.

---

## Weekly Routine — Sustainable Pace

### Saturday
```
8:00 AM  Read this roadmap + last week's decisions (15 min)
8:15 AM  Development work (3–4 hours)
12:00 PM Done
```

### Sunday
```
2:00 PM  Development work (2 hours)
4:00 PM  Done
```

### Monday–Friday evenings
```
7:00 PM  java -jar sat-engine.jar --job=generate --count=20  (15 min unattended)
7:15 PM  java -jar sat-engine.jar --job=agent-review          (runs in background)
7:30 PM  java -jar sat-engine.jar --job=enrich                (runs in background)
7:45 PM  Open http://localhost:8080/admin/validate.html → review enriched questions (20 min)
8:00 PM  Done — ~15 approved questions live in DB
```

**Total weekly effort:** ~9–11 hours. Sustainable alongside full-time consulting.

---

## Tech Stack (Updated)

| Layer | Technology |
|-------|-----------|
| Frontend | React (Vite), TailwindCSS, KaTeX, Chart.js |
| Backend | Spring Boot 3.x (pure REST API, no Thymeleaf) |
| Database | PostgreSQL (Supabase) + pgvector |
| Auth | JWT (Spring Security) |
| Payment | Stripe |
| AI | Claude API (claude-haiku-4-5 for generation, claude-opus-4-6 for AI panel) |
| Hosting | Railway (API), Vercel or Netlify (React) |
| Email | SendGrid |
| Diagrams | Programmatic SVG + Chart.js (no Cloudinary needed) |

---

## ADR-038 — Parallel Tracks Decision

**Decision:** Questions and development run completely independently. Questions generated, reviewed, and enriched entirely via Java pipeline stages (--job=generate|agent-review|enrich). Written directly to DB. Human review via validate.html served at /admin/validate.html by Spring Boot. No JSON files, no BatchLoader, no manual SQL.

**Rejected:** Sequential approach (all questions first, then build), outsourcing question creation.

**Reason:** Questions take the most calendar time but least focused effort. Running in parallel means launch day with a full question bank ready — not scrambling to create content after the app is built.

**Status:** ✅ DECIDED

---

## ADR-040 — Practice Mode Before Test Mode

**Decision:** Build practice mode (topic-by-topic, by difficulty) before full adaptive test mode.

**Rejected:** Building the 98-question adaptive test first (original plan).

**Reason:** Practice mode is simpler to build, showcases the AI panel immediately (the core differentiator), and delivers value to students faster. Test mode is a feature students want after they've learned the material — not before. Practice mode also generates more session data which will inform adaptive test calibration later.

**Status:** ✅ DECIDED

---

## ADR-039 — Out of Scope for Launch

**Explicitly NOT building for launch:**

| Feature | Phase |
|---------|-------|
| Mobile native app | Phase 3 (12+ months) |
| ACT support | Phase 2 (after 500 students) |
| AP exam support | Phase 3 |
| Admin question management UI | Phase 2 |
| Personalised study plan | Phase 2 |
| Advanced performance analytics | Phase 2 |
| Social features | Phase 3 |
| Debate Mode | Month 4–5 |
| What-If Explorer | Month 5–6 |
| Parent dashboard | Phase 2 |
| Score guarantee | Month 7–8 (when data supports) |
| Socratic Hints | Month 4 |
| Error Autopsy | Month 4 |

**Status:** ✅ DECIDED

---

## Launch Definition of Done

```
Product:
✓ Practice mode: all 8 domains, questions grouped by topic and difficulty
✓ Immediate feedback after each answer
✓ AI Learning Panel: Solution, Core Concept, Prerequisites tabs
✓ Full 98-question adaptive SAT test (timed, no AI during test)
✓ Score report with domain breakdown
✓ User accounts (register/login)
✓ Stripe payment ($14.99/month)
✓ First 10 questions always free (no card required)
✓ Welcome + score report emails
✓ Mobile responsive (browser)

Content:
✓ 500–650 reviewed questions in DB
✓ All 8 SAT domains covered
✓ Full difficulty range 1–7
✓ Math and R&W sections
✓ 30–40 R&W passages

Infrastructure:
✓ Railway deployment (auto-deploy from GitHub)
✓ Supabase PostgreSQL
✓ Custom domain + SSL
✓ SendGrid for email
✓ Vercel/Netlify for React frontend

Marketing:
✓ Landing page live
✓ Posted in r/SAT
✓ Posted in Indian parent communities
✓ Personal network notified
```

---

## Post-Launch Build Priority (Month 4–6)

Based on what users tell you — but likely in this order:

1. **Error Autopsy** — highest learning value, zero user friction
2. **Socratic Hints** — replaces "show answer" with "earn the answer"
3. **Tutor Chat** — students will ask for this
4. **Weak area recommendations** — "practice more questions like these"
5. **More questions** — always more questions
6. **Debate Mode** — after Autopsy + Hints proven
7. **What-If Explorer** — Math-specific, after Debate Mode

---

## The Sentence to Remember on Hard Days

> "I worked these many years for someone else's profile. Now I will work to fulfil my dreams."

Month 3 will feel hard. Month 5 after launch with few signups will feel harder. This is normal. The products that win are built by people who didn't quit in Month 4.
