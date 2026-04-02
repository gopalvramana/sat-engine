# 13 — Screen Layouts & UX Decisions

> Research basis: Bluebook (official), Khan Academy, UWorld, Princeton Review, Kaplan, PrepScholar.
> Last updated: April 2026.

---

## The One Design Principle That Overrides Everything

Every competitor shows a question + an answer. We show a question + an answer + **three structured pedagogical perspectives** (Solution, Core Concept, Alternative Approach).

That 3-tab panel is the product. Every layout decision should make it easy to reach and pleasant to read.

---

## What the Research Confirmed

| Pattern | Decision |
|---------|----------|
| Bluebook is the reference UI students know | Mirror its conventions — don't fight muscle memory |
| Tutor Mode (immediate feedback) is the dominant study mode | Default to immediate feedback after submission |
| UWorld's "explain every wrong answer" is considered best-in-class | Our 3-tab system is our equivalent differentiator |
| SPR = plain text input, not bubble grid | Text box only |
| R&W = passage left, question right split | Two-column for R&W, full-width for Math |
| Question review panel is expected | Include in Exam Mode; skip in Practice Mode v1 |
| Timer: section-level, hideable | Timer per session, not per question |
| Mobile: Khan Academy stacks single column | Same approach for mobile |

---

## Phase 1 — `practice.html` (Plain JS, current stack)

Scope: one question at a time, immediate feedback, no exam simulation.
Goal: validate rendering + 3-tab UX before building React.

### Screen 1 — Session Setup

```
┌─────────────────────────────────────────────┐
│  SATEngine Practice                   [logo] │
├─────────────────────────────────────────────┤
│                                             │
│  What do you want to practice?             │
│                                             │
│  Section   [● Math]  [  Reading & Writing] │
│                                             │
│  Domain    [All ▾]                         │
│  Skill     [All ▾]                         │
│  Difficulty [All ▾]                        │
│                                             │
│  Questions  [10 ▾]                         │
│                                             │
│         [ Start Practice → ]               │
│                                             │
└─────────────────────────────────────────────┘
```

**Decisions:**
- No login required for Phase 1
- Domain + Skill dropdowns populated from approved questions in DB
- Default: Math, All domains, All skills, 10 questions
- "Start Practice" fetches the question set from `/api/practice/session`

---

### Screen 2 — Math Question (MCQ)

```
┌─────────────────────────────────────────────────────────────────┐
│  Question 3 of 10   ████████░░░░░░░░░░░░  Algebra · Difficulty 4│
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  A factory produces widgets at a constant rate. In the first   │
│  3 hours, the factory produces 450 widgets.                    │
│                                                                 │
│  [diagram if present — inline, centered]                       │
│                                                                 │
│  At this rate, how many widgets will be produced in 8 hours?  │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ○  A   1,200                                                   │
│  ○  B   1,350                                                   │
│  ○  C   1,400                                                   │
│  ○  D   1,500                                                   │
│                                                                 │
│                               [ Submit Answer ]                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Decisions:**
- Progress bar at top (not timer — Phase 1 is untimed)
- Domain + difficulty shown as context chips, not prominent
- Diagram renders inline between question context and question stem
- Submit button disabled until an option is selected
- No answer eliminator in Phase 1 (add in React)
- No "Skip" in Phase 1

---

### Screen 3 — Math Question (SPR)

```
┌─────────────────────────────────────────────────────────────────┐
│  Question 5 of 10   ████████████░░░░░░░  Geometry · Difficulty 2│
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  A trapezoid has parallel sides of length 8 and 14, and the   │
│  perpendicular distance between them is 6.                     │
│                                                                 │
│  [trapezoid diagram — inline]                                  │
│                                                                 │
│  What is the area of the trapezoid?                           │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Your answer:  [ _____________ ]                               │
│                                                                 │
│  (Enter a number. Fractions like 3/4 and decimals are OK.)    │
│                                                                 │
│                               [ Submit Answer ]                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Decisions:**
- Single text input, hint text shows accepted formats
- Validate client-side: must be numeric/fraction before enabling Submit
- Correct if value falls within sprMin ≤ input ≤ sprMax

---

### Screen 4 — R&W Question

```
┌───────────────────────────────────┬─────────────────────────────┐
│  PASSAGE                          │  Question 7 of 10           │
│                                   │  Reading & Writing          │
│  [passage text — scrollable]      ├─────────────────────────────┤
│                                   │                             │
│                                   │  [question stem]            │
│                                   │                             │
│                                   │  ○  A  [option text]        │
│                                   │  ○  B  [option text]        │
│                                   │  ○  C  [option text]        │
│                                   │  ○  D  [option text]        │
│                                   │                             │
│                                   │      [ Submit Answer ]      │
└───────────────────────────────────┴─────────────────────────────┘
```

**Decisions:**
- 50/50 split: passage left, question right
- Passage is scrollable independently
- On mobile: stacks vertically (passage above, question below)
- Standard English questions (no passage, just a sentence with ___): full-width, same as Math layout

---

### Screen 5 — Answer Feedback (after submission)

```
┌─────────────────────────────────────────────────────────────────┐
│  Question 3 of 10   ████████░░░░░░░░░░░░  Algebra · Difficulty 4│
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [question stem — same as before, now read-only]               │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ✓  A   1,200   ← Correct                                      │ ← green highlight
│  ✗  B   1,350                                                   │ ← red strike (if chosen wrong)
│     C   1,400                                                   │
│     D   1,500                                                   │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│  [Solution] [Core Concept] [Alternative Approach]              │ ← 3-tab panel, starts OPEN
│                                                                 │
│  ▼ Solution                                                     │
│  ─────────────────────────────────────────────────────────────  │
│  Step 1: Find the rate                                          │
│  450 widgets ÷ 3 hours = 150 widgets/hour                      │
│                                                                 │
│  Step 2: Apply to 8 hours                                      │
│  150 × 8 = 1,200                                               │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                  [ Next Question → ]           │
└─────────────────────────────────────────────────────────────────┘
```

**Decisions:**
- Correct answer always shown in green (even if student got it right — reinforces)
- Student's wrong answer shown with a red indicator
- 3-tab panel opens automatically on the Solution tab after submission
- Tabs are the accordion pattern already built in validate2.js — reuse it
- `explanationShort` shown as a one-line summary above the tabs
- "Next Question" is the only action — no going back
- For SPR: show "Your answer: 66 ✓ Correct" or "Your answer: 72 ✗ Correct answer: 66"

---

### Screen 6 — Session Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                    Session Complete!                            │
│                                                                 │
│              7 / 10  correct   70%                             │
│              ████████████████░░░░░░                            │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│  By domain:                                                     │
│  Algebra          ████████████  4/5   80%  ✓                  │
│  Problem Solving  ████░░░░░░░░  2/4   50%  needs work         │
│  Geometry         ████████░░░░  1/1  100%  ✓                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [ Review Answers ]       [ Practice Again ]                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Decisions:**
- Score shown as fraction + percentage + progress bar
- Domain breakdown only (not skill-level yet — save for React app)
- "Review Answers" pages back through all questions in read-only mode with explanations shown
- "Practice Again" returns to Session Setup with same filters pre-selected
- No account/save in Phase 1 — session lives in memory only

---

## Phase 2 — React App (after practice.html is validated)

Additional screens and features not in Phase 1:

### Additional Screens
- **Dashboard** — skill mastery heatmap, recent sessions, score trajectory, recommended focus areas
- **Full-length Adaptive Test** — Module 1 (22 Math + 27 R&W) → Module 2 (adaptive difficulty based on Module 1 score)
- **Error Review** — filtered view of all questions answered incorrectly, grouped by skill
- **Progress over time** — score trend chart, time-per-question analysis (borrowed from MentoMind's idea)
- **Account / Login** — email + Google OAuth

### Additional UX Features
- **Exam Mode toggle** — hide explanations until full session complete, enforce timer
- **Answer eliminator** — cross-out choices (Bluebook convention)
- **Mark for review** — flag + question grid navigator
- **Draggable divider** — for R&W split screen (Bluebook standard)
- **Desmos calculator** — floating panel for Math, toggled from toolbar
- **Formula reference sheet** — one-tap access in Math
- **Streak / mastery system** — skill-level indicators (Familiar → Proficient → Mastered) per Khan Academy model

### Layout Changes from Phase 1
- Fixed toolbar at top: `[Logo] [Progress/Module] [Timer] [Calculator] [Reference]`
- Fixed bottom bar: `[← Prev] [Question N of M ▾] [Flag] [Next →]`  clicking N of M opens question grid panel
- 3-tab explanation panel becomes a side-drawer on desktop (slides in from right) rather than inline — keeps question visible while reading explanation

---

## API Endpoints Required (TODO #5)

Before building either phase, the following backend endpoints are needed:

| Endpoint | Purpose | Notes |
|----------|---------|-------|
| `GET /api/practice/session?domain=&skill=&difficulty=&count=` | Fetch N questions for a session | Returns questions WITHOUT correctAnswer, explanationSteps, trapExplanation |
| `POST /api/practice/submit` | Submit an answer, get feedback | Body: `{questionId, answer}`. Response: `{correct, correctAnswer, explanationShort, explanationSteps, coreConcept, alternativeApproach}` |
| `GET /api/practice/filters` | Get available domain/skill options | Returns only domains/skills that have ≥1 approved question |
| `POST /api/practice/session/complete` | Save session results | Body: `{questions[], answers[], score}`. Phase 1: optional. Phase 2: required for progress tracking. |

**Critical:** `/api/practice/session` must NOT return `correctAnswer`, `explanationSteps`, `coreConcept`, `alternativeApproach`, or `trapExplanation` in the initial payload. These are only returned by `/api/practice/submit` after the student has answered.

---

## Mobile Layout (both phases)

At viewport < 768px, all layouts collapse to single column:

- **Math question:** question stem → diagram → answer choices → submit (vertical stack)
- **R&W question:** passage (collapsible, 40% height) → question → choices (vertical stack)
- **Feedback:** question (collapsed) → result → 3-tab panel → next button
- **3-tab panel on mobile:** full-width, accordion style (same as validate2.html)
- Bottom navigation bar replaces top bar on mobile

---

## What We Are NOT Building (deliberate omissions)

| Feature | Why skipped |
|---------|-------------|
| Per-question timer | Not in any study/practice mode (only exam mode) |
| Bubble grid for SPR | Eliminated in digital SAT — text box only |
| Video explanations per question | High production cost, low priority vs 3-tab quality |
| Gamification (streaks, badges) | Not our audience — serious NRI/DASA students, not casual users |
| Social / leaderboards | Phase 3 at earliest |
| ACT support | Out of scope for v1 |
