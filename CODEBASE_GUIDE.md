# Aptify Codebase Guide
> Written for the founder. Read this before every coding session. Update it when things change.

---

## What this system does (one paragraph)

A student opens the app, logs in with Google, picks a topic + difficulty on the Practice Setup page, and starts a session. The backend picks questions from the DB one at a time. The student answers, gets instant feedback with an explanation. At the end they see a summary. The Dashboard shows their history and stats. Questions were generated offline by a Claude pipeline and stored in PostgreSQL.

---

## The two codebases in this repo

```
sat-engine/
├── src/                    ← Java Spring Boot backend (runs on port 8080)
└── frontend/src/           ← React frontend (Vite dev server on port 5173)
```

In **production**, Spring Boot serves the built React app as static files.  
In **development**, Vite runs separately and proxies `/api` calls to Spring Boot.

---

## Backend map — where to look for what

### Entry point
`src/main/java/com/satengine/SatEngineApplication.java`  
Just starts Spring Boot. Nothing interesting here.

### Configuration (the "rules")
| File | What it controls |
|------|-----------------|
| `config/SecurityConfig.java` | Which URLs need login, which are public, Google OAuth setup |
| `config/OAuth2SuccessHandler.java` | What happens after Google login succeeds — saves user to DB, puts userId in HTTP session |
| `config/SpaRoutingController.java` | Makes React Router work — any `/app/**` URL serves `index.html` |
| `config/GlobalExceptionHandler.java` | Turns Java exceptions into JSON error responses |

### Domain — the core data and business logic
Each folder = one concept. Pattern is always the same: `Entity → Repository → Service → Controller`.

```
domain/
├── user/
│   ├── User.java                  ← maps to `users` DB table
│   ├── UserRepository.java        ← DB queries for users
│   └── UserService.java           ← findOrCreate on login
│
├── question/
│   ├── Question.java              ← maps to `questions` table (big — 30+ fields)
│   ├── QuestionAnswer.java        ← maps to `question_answers` (correct answer, kept separate for security)
│   ├── QuestionRepository.java    ← the complex queries: find next question by domain/band
│   ├── QuestionService.java       ← question fetching logic
│   └── QuestionController.java    ← GET /api/questions/count
│
└── session/
    ├── Session.java               ← maps to `sessions` table
    ├── SessionAnswer.java         ← maps to `session_answers` (one row per student answer)
    ├── SessionRepository.java     ← find sessions by user, count completed
    ├── SessionAnswerRepository.java ← find answers by session or user
    ├── SessionService.java        ← ALL session logic: create, pick next question, submit answer, dashboard stats
    └── SessionController.java     ← POST /api/sessions, GET /api/sessions/{id}, GET /api/sessions/{id}/next, POST /api/sessions/{id}/answers
```

### API layer — endpoints that don't fit neatly into domain
```
api/
├── auth/
│   ├── AuthController.java        ← GET /api/auth/me (who is logged in?)
│   └── DevLoginController.java    ← POST /dev/login (localhost only, bypasses Google)
│
├── dashboard/
│   └── DashboardController.java   ← GET /api/dashboard (stats + recent sessions)
│
└── gap/
    ├── GapAnalysisController.java ← POST /api/gaps/analyze
    └── GapAnalysisService.java    ← calls Claude to explain WHY student got it wrong
```

### DTOs — data shapes going in and out of the API
```
dto/
├── CreateSessionRequest.java      ← body for POST /api/sessions
├── SessionResponse.java           ← response from session endpoints
├── QuestionResponse.java          ← a question sent to the frontend (NO correct answer)
├── SubmitAnswerRequest.java       ← body for POST /api/sessions/{id}/answers
├── AnswerFeedback.java            ← response after submitting — includes correct answer + explanation
└── DashboardResponse.java         ← stats + recent sessions list
```

> **Rule to know:** `QuestionResponse` deliberately omits the correct answer. The answer only comes back in `AnswerFeedback` after the student submits. This is the security model.

### Pipeline — how questions get generated (offline, not student-facing)
```
pipeline/
├── PipelineRunner.java            ← orchestrates the stages in sequence
├── GenerateStage.java             ← calls Claude Haiku to write the question
├── AgentReviewStage.java          ← calls Claude to QA the question (9 checks)
├── EnrichStage.java               ← calls Claude Opus to add explanation steps, core concept
├── EnrichChoiceExplanationsStage  ← adds per-choice wrong-answer explanations
├── EnrichAnimationStage.java      ← adds animation frames for diagram questions
├── RenderNormalizeStage.java      ← cleans up formatting
├── VisualCheckStage.java          ← validates diagram JSON
└── claude/
    ├── ClaudeClient.java          ← HTTP client for Anthropic API
    └── PromptLibrary.java         ← ALL prompts live here (the most important pipeline file)
```

### Database migrations
`src/main/resources/db/migration/V{n}__description.sql`  
Flyway runs these in order on startup. **Never edit an existing migration** — always add a new `V{n+1}__...sql`.  
Current highest: **V42**

---

## Frontend map — where to look for what

### Entry point / routing
```
main.jsx        ← starts React, wraps everything in BrowserRouter (basename="/app") + AuthProvider
App.jsx         ← defines all routes
```

**Routes:**
| URL | Component | Has sidebar? |
|-----|-----------|-------------|
| `/app/` | `DashboardPage` | Yes |
| `/app/practice` | `PracticeSetupPage` | Yes |
| `/app/session/:id` | `PracticePage` | No (full screen) |
| `/app/session/:id/summary` | `SummaryPage` | No (full screen) |

### Pages — what each screen does
```
pages/
├── DashboardPage.jsx       ← fetches /api/dashboard, shows stats + recent sessions
├── PracticeSetupPage.jsx   ← let user pick section/domain/difficulty, calls POST /api/sessions, navigates to session
├── PracticePage.jsx        ← the question/answer loop, uses usePracticeSession hook
└── SummaryPage.jsx         ← reads history from React Router state (no API call needed)
```

### The most important hook
`hooks/usePracticeSession.js` — this is the brain of the practice screen.

It manages a state machine with 3 phases:
```
loading → question → feedback → loading → question → ...
                                              ↓ (no more questions)
                                          navigate to /summary
```
It also handles **review mode** — when student clicks Back to re-read a previous question.

### Components — reusable UI pieces
```
components/
├── AppShell/           ← layout wrapper: sidebar + main content area
├── Sidebar/            ← left nav with logo + nav items
├── QuestionCard/       ← renders question stem + MCQ choices or SPR input
├── FeedbackPanel/      ← shows after answering: correct/wrong + 3-tab panel (Explanation / Core Concept / Gap)
├── ExplanationSteps/   ← step-by-step solution
├── CoreConcept/        ← the underlying concept card
├── FindMyGap/          ← calls /api/gaps/analyze (live Claude call)
├── ChoiceExplanations/ ← why each wrong answer is wrong
├── DiagramPanel/       ← renders SVG / Chart.js diagrams
├── AnimationPanel/     ← step-through animation frames
├── MathText/           ← renders LaTeX via KaTeX
├── ProgressBar/        ← top bar showing Q current/total + back/end buttons
└── Toolbar/            ← calculator toggle
```

### API calls — all in one place
`api/client.js` — every single API call goes through here. If you want to know what the frontend calls, read this file. It's short.

### Auth
`context/AuthContext.jsx` — wraps the whole app. On load it calls `/api/auth/me`. If 401 → user is not logged in. Any component can call `useAuth()` to get `{ user, loading }`.

---

## The database (6 key tables)

```
users               — one row per Google account
questions           — all SAT questions (generated by pipeline)
question_answers    — correct answer for each question (separate table, never sent to frontend until after submit)
sessions            — one row per practice session a student starts
session_questions   — which questions are in a session (ordered)
session_answers     — one row per question the student actually answers
```

**The join you'll write most often:**
```sql
SELECT q.domain, sa.is_correct, sa.time_spent_seconds
FROM session_answers sa
JOIN questions q ON q.id = sa.question_id
JOIN sessions s  ON s.id = sa.session_id
WHERE s.user_id = '...'
```

---

## How to trace a feature end-to-end

### "Student answers a question"
1. Student clicks an answer → `QuestionCard.jsx` calls `onSubmit(answer)`
2. `PracticePage.jsx` passes that to `usePracticeSession.submitAnswer(answer)`
3. Hook calls `api.submitAnswer()` → `POST /api/sessions/{id}/answers`
4. `SessionController.java` → `SessionService.submitAnswer()`
5. Service checks answer against `question_answers` table → saves `SessionAnswer` row
6. Returns `AnswerFeedback` with correct answer + explanation
7. Hook sets phase = `'feedback'`, `FeedbackPanel` renders

### "Dashboard loads"
1. `DashboardPage.jsx` mounts → `fetch('/api/dashboard')`
2. `DashboardController.java` reads `userId` from HTTP session
3. Calls `SessionService.getDashboard(userId)`
4. Service queries `session_answers` + `sessions` tables → builds stats
5. Returns `DashboardResponse` → page renders real numbers

### "Session is created"
1. Student clicks Start on `PracticeSetupPage.jsx`
2. Calls `api.createSession(type, section, domainBandCounts)`
3. `SessionController` → `SessionService.createSession(userId, req)`
4. New row in `sessions` table with `user_id` set
5. Frontend navigates to `/app/session/{id}`

---

## Quick reference — "where do I look if X is broken?"

| Symptom | Look here first |
|---------|----------------|
| Wrong question being shown | `SessionService.getNextQuestion()` + `QuestionRepository` |
| Answer feedback wrong | `SessionService.submitAnswer()` + `question_answers` table |
| Login not working | `SecurityConfig.java` + `OAuth2SuccessHandler.java` |
| Dashboard showing wrong data | `SessionService.getDashboard()` + `DashboardController` |
| Page not loading (white screen) | `App.jsx` routes + `SpaRoutingController.java` |
| Math not rendering | `MathText.jsx` (KaTeX) |
| Diagram not showing | `DiagramPanel.jsx` |
| API call failing | `api/client.js` → check Network tab in browser DevTools |
| DB change needed | Add new `V{n}__description.sql` in `db/migration/` |
| Frontend won't build | `frontend/` — run `npm run build` and read the error |

---

## Things that are deliberately NOT obvious

1. **Correct answers are in a separate table** (`question_answers`) and never returned by `QuestionController` or `QuestionResponse`. They only come back in `AnswerFeedback` after submit.

2. **Sessions have `user_id` but it wasn't always set** — V42 migration backfilled old data to the dev user.

3. **`usePracticeSession` uses both a ref and state for history** — `historyRef` for stale-closure-safe access inside callbacks, `history` state for re-renders.

4. **Dev login only works on `local` Spring profile** — `DevLoginController` has `@Profile("local")`. It doesn't exist in production.

5. **The pipeline runs offline** — triggered manually via admin API, not triggered by students using the app.

---

## Your first exercises (do these to build the map)

1. **Trace the answer submission** — open `usePracticeSession.js`, find `submitAnswer`, follow it to `api/client.js`, then to `SessionController.java`, then to `SessionService.java`. Read each step. 15 minutes.

2. **Read the schema** — open `V1__initial_schema.sql`. Every table, every column. Don't skip it. 10 minutes.

3. **Break something small** — in `DashboardPage.jsx`, change `fetch('/api/dashboard')` to `fetch('/api/dashboard-broken')`. See what happens in the browser. Fix it. This teaches you the error path.

4. **Read `api/client.js`** — it's 50 lines. After reading it you'll know every API call the frontend makes.

5. **Open the DB** — connect to the local Postgres (Docker container `roms-postgres`) and run `SELECT * FROM sessions LIMIT 5`. See the actual data your code is working with.
