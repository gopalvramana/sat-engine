# Exception Handling & Logging Guide

This is your quick-reference when something goes wrong. It tells you:
- what every log line means and where it comes from
- what exception maps to which HTTP status
- how to trace a request end-to-end
- how to find the right file to fix a problem

---

## 1. Log Format

Every log line follows this pattern:

```
HH:mm:ss.SSS LEVEL [reqId] Logger - message
```

**Example:**
```
14:32:01.112 INFO  [a3f8c21b] c.s.d.s.SessionService - answer recorded session=abc123 question=def456 correct=true timeSecs=47
```

| Part | Meaning |
|---|---|
| `HH:mm:ss.SSS` | Time (milliseconds precision) |
| `LEVEL` | `DEBUG` / `INFO` / `WARN` / `ERROR` |
| `[reqId]` | 8-char unique ID for this HTTP request — same ID appears on every line for that request. `[sys]` means it came from a background thread, not an HTTP request |
| `Logger` | Abbreviated class name (e.g. `c.s.d.s.SessionService` = `com.satengine.domain.session.SessionService`) |

---

## 2. Log Levels — What Each Means

| Level | When it's used | What to do when you see it |
|---|---|---|
| `DEBUG` | Normal expected states: auth checks, next-question picks, expected 404s/409s | Nothing — informational only |
| `INFO` | Business events: session created, answer recorded, user login, request entry/exit | Nothing — monitor for volume |
| `WARN` | Degraded but recovered: gap analysis retry, JSON parse fail with fallback, malformed userId | Investigate if it happens repeatedly |
| `ERROR` | Something broke that should not break: unhandled exception, serialization failure, Claude failed all attempts | Fix required — always has a stack trace |

---

## 3. Request Tracing — Every Request Has a reqId

`RequestLoggingFilter` stamps every incoming HTTP request with a random 8-char `reqId` and puts it into MDC (Mapped Diagnostic Context). Every log line written during that request — across controller, service, repository — carries the same `reqId`.

**How to trace a single request:**
1. Find the entry line: `→ POST /api/sessions/abc/answers user=uuid reqId=a3f8c21b`
2. Grep all logs for that reqId: `grep a3f8c21b app.log`
3. You'll see every log line from entry to exit for that one request.

**Entry log (RequestLoggingFilter):**
```
INFO  [a3f8c21b] c.s.c.RequestLoggingFilter - → POST /api/sessions/{id}/answers user=<uuid> reqId=a3f8c21b
```

**Exit log (RequestLoggingFilter):**
```
INFO  [a3f8c21b] c.s.c.RequestLoggingFilter - ← POST /api/sessions/{id}/answers 200 142ms reqId=a3f8c21b
```

If the exit log shows a 4xx or 5xx, the corresponding exception handler log will have fired between entry and exit — search by reqId.

**Static assets are skipped** — `.js`, `.css`, `.html`, `.ico`, `.png`, and anything under `/assets/` never appear in logs.

---

## 4. Exception Hierarchy

```
RuntimeException (Java built-in)
└── ResourceNotFoundException     → HTTP 404   (entity does not exist)
└── DuplicateAnswerException      → HTTP 409   (student answered same question twice)
└── InvalidRequestException       → HTTP 400   (bad input data)

MethodArgumentNotValidException   → HTTP 400   (Bean Validation — @NotNull, @NotBlank, etc.)
MethodArgumentTypeMismatchException → HTTP 400 (wrong type in path/query param — e.g. "abc" for a UUID)
RuntimeException (untyped)        → HTTP 500   (programming error — should not happen)
Exception (untyped checked)       → HTTP 500   (unexpected checked error)
```

All of these are caught and mapped in `GlobalExceptionHandler`.

### Exception response body

Every error response returns:
```json
{ "error": "human-readable message" }
```

500 errors always return the generic message `"An unexpected error occurred"` — the real detail is in the server log.

---

## 5. GlobalExceptionHandler — Complete Handler Map

**File:** `src/main/java/com/satengine/config/GlobalExceptionHandler.java`

| Handler method | Exception caught | HTTP | Log level | Log message |
|---|---|---|---|---|
| `handleNotFound` | `ResourceNotFoundException` | 404 | `DEBUG` | `not found: <message> [METHOD /path]` |
| `handleDuplicateAnswer` | `DuplicateAnswerException` | 409 | `DEBUG` | `duplicate answer: <message> [METHOD /path]` |
| `handleInvalidRequest` | `InvalidRequestException` | 400 | `DEBUG` | `invalid request: <message> [METHOD /path]` |
| `handleTypeMismatch` | `MethodArgumentTypeMismatchException` | 400 | `DEBUG` | `type mismatch: Invalid value for param '<name>': <value> [METHOD /path]` |
| `handleValidationException` | `MethodArgumentNotValidException` | 400 | `DEBUG` | `validation failed: <field>: <message> [METHOD /path]` |
| `handleRuntimeException` | `RuntimeException` | 500 | `ERROR` | `Unhandled RuntimeException on METHOD /path: <message>` + stack trace |
| `handleGenericException` | `Exception` | 500 | `ERROR` | `Unhandled Exception on METHOD /path: <message>` + stack trace |

> **Rule:** 400/404/409 are `DEBUG` — they are expected user errors. 500 is always `ERROR` with full stack trace.

---

## 6. Where Every Exception Is Thrown

### SessionService — `src/main/java/com/satengine/domain/session/SessionService.java`

| Method | Exception | Condition | Maps to |
|---|---|---|---|
| `createSession` | `InvalidRequestException` | `domainBandCounts` JSON serialization fails (Jackson error) | 400 |
| `getNextQuestion` | `ResourceNotFoundException` | `sessionId` not in DB | 404 |
| `getNextQuestionByBandQuota` | *(none thrown)* | `domainBandCounts` JSON parse fails → logs ERROR + returns `Optional.empty()` | 204 (empty) |
| `submitAnswer` | `ResourceNotFoundException` | `sessionId` not in DB | 404 |
| `submitAnswer` | `InvalidRequestException` | `studentAnswer` is null or blank | 400 |
| `submitAnswer` | `DuplicateAnswerException` | Question already answered in this session | 409 |
| `submitAnswer` | `ResourceNotFoundException` | `questionId` has no answer record in DB | 404 |
| `submitAnswer` | `ResourceNotFoundException` | `questionId` not in DB (second lookup for explanation) | 404 |
| `getSessionStatus` | `ResourceNotFoundException` | `sessionId` not in DB | 404 |
| `computeTotal` (private) | *(none thrown)* | JSON parse fails → logs WARN + returns 0 | silent fallback |

### GapAnalysisService — `src/main/java/com/satengine/api/gap/GapAnalysisService.java`

| Method | Exception | Condition | Maps to |
|---|---|---|---|
| `analyze` | `ResourceNotFoundException` | `questionId` not in DB | 404 |
| `analyze` | `ResourceNotFoundException` | `questionId` has no answer record | 404 |
| `analyze` — Claude call | *(none thrown)* | Claude fails both attempts → logs ERROR + returns `FALLBACK_GAP` JSON | 200 (fallback) |
| `buildPrompt` — steps parse | *(none thrown)* | `explanationSteps` JSON is malformed → logs WARN + uses raw text | silent fallback |

### QuestionService — `src/main/java/com/satengine/domain/question/QuestionService.java`

| Method | Exception | Condition | Maps to |
|---|---|---|---|
| `getQuestion` | `ResourceNotFoundException` | `questionId` not in DB | 404 |

### AdminQuestionService — `src/main/java/com/satengine/api/admin/AdminQuestionService.java`

| Method | Exception | Condition | Maps to |
|---|---|---|---|
| `findOrThrow` (private) | `ResourceNotFoundException` | Question not found by ID | 404 |
| `patchFields` | `InvalidRequestException` | Field name not in `PATCHABLE_FIELDS` set | 400 |

### DashboardController — `src/main/java/com/satengine/api/dashboard/DashboardController.java`

| Location | Exception | Condition | Response |
|---|---|---|---|
| UUID parse | `IllegalArgumentException` (caught locally) | `userId` in HTTP session is not a valid UUID | 401 (logs WARN) |
| Missing session | *(checked inline)* | `userId` attribute absent from HTTP session | 401 (logs DEBUG) |

### SkillContentController — `src/main/java/com/satengine/api/skill/SkillContentController.java`

| Location | Exception | Condition | Response |
|---|---|---|---|
| InputStream read | `IOException` (caught locally) | Classpath resource read fails | 500 (logs ERROR with file path) |
| Bad `skillKey` format | *(checked inline)* | Key doesn't match `[a-z0-9_]{1,60}` | 400 (no log) |
| File not found on classpath | *(checked inline)* | Resource is null | 404 (no log) |

---

## 7. All Log Call Sites by Class

### RequestLoggingFilter
```
INFO  → METHOD /path user=<uuid|anon> reqId=<8chars>      ← every API request entry
INFO  ← METHOD /path <status> <Xms> reqId=<8chars>        ← every API request exit
```

### GlobalExceptionHandler
```
DEBUG not found: <msg> [METHOD /path]                      ← 404
DEBUG duplicate answer: <msg> [METHOD /path]               ← 409
DEBUG invalid request: <msg> [METHOD /path]                ← 400 (InvalidRequestException)
DEBUG type mismatch: Invalid value for param '<n>': <v>    ← 400 (wrong type in path param)
DEBUG validation failed: <field>: <message>                ← 400 (Bean Validation)
ERROR Unhandled RuntimeException on METHOD /path: <msg>    ← 500 (+ stack trace)
ERROR Unhandled Exception on METHOD /path: <msg>           ← 500 (+ stack trace)
```

### DashboardController
```
DEBUG dashboard — no session                               ← no userId in HTTP session → 401
WARN  dashboard — malformed userId in session: <value>     ← userId is not a valid UUID → 401
INFO  dashboard requested userId=<uuid>                    ← successful dashboard fetch
```

### AuthController
```
DEBUG auth check — no session                              ← GET /api/auth/me with no session
DEBUG auth check userId=<uuid>                             ← GET /api/auth/me success
```

### DevLoginController
```
INFO  Dev login: <email> session=<sessionId>               ← dev login used (only non-prod)
```

### OAuth2SuccessHandler
```
INFO  OAuth2 login: <email> (<uuid>)                       ← Google OAuth login success
```

### UserService
```
INFO  user login email=<email>                             ← existing user logged in
INFO  user created email=<email>                           ← new user auto-created on first OAuth
```

### SessionController
```
INFO  session created id=<uuid> userId=<uuid> total=<n> section=<section>
DEBUG next question requested session=<uuid>
INFO  answer submitted session=<uuid> question=<uuid> correct=<bool>
```

### SessionService
```
INFO  creating session userId=<uuid> section=<section> totalQuestions=<n>
ERROR Failed to serialize domainBandCounts userId=<uuid> error=<msg>         ← + stack trace
INFO  dashboard computed userId=<uuid> sessions=<n> questions=<n> accuracy=<n>
DEBUG picking next question session=<uuid> answered=<n> domainBandCounts=<present|absent>
INFO  session exhausted session=<uuid> answered=<n>                          ← no more questions → 204
ERROR Failed to parse domainBandCounts for session=<uuid> — falling back to empty. error=<msg>
DEBUG no question found for slot domain=<domain> band=<band> (diff=<min>-<max>)
INFO  answer recorded session=<uuid> question=<uuid> answer=<10chars> correct=<bool> timeSecs=<n>
WARN  Failed to parse domainBandCountsJson for total computation: <msg>
```

### GapAnalysisController
```
INFO  gap analysis requested questionId=<uuid> studentAnswer=<10chars>
```

### GapAnalysisService
```
INFO  gap analysis claude call start questionId=<uuid> attempt=<n>/<max>
INFO  gap analysis claude call done questionId=<uuid> durationMs=<n>
WARN  gap analysis attempt <n>/<max> failed questionId=<uuid> error=<msg>
ERROR gap analysis failed after <n> attempts questionId=<uuid> — returning fallback. error=<msg>   ← + stack trace
WARN  Could not parse explanationSteps JSON for questionId=<uuid> — using raw text. error=<msg>
```

### SkillContentController
```
ERROR Failed to read skill content file /skill-content/<key>.json error=<msg>   ← + stack trace
```

---

## 8. Frontend Error Handling

### Centralized Logger — `frontend/src/lib/logger.js`

```javascript
log.debug(msg, data)   // suppressed in production builds
log.info(msg, data)
log.warn(msg, data)
log.error(msg, data)
```

Console output format:
```
[HH:MM:SS.mmm] [debug] message  { key: value }
```

### API Client — `frontend/src/api/client.js`

Every fetch call logs:
```
→ API  { method, url }                     ← request start
← API  { method, url, status, ms }         ← success
← API error { method, url, status, body, ms }  ← any non-2xx or network error
```

The client **throws** on non-2xx. Callers must catch.

### ErrorBoundary — `frontend/src/components/ErrorBoundary/ErrorBoundary.jsx`

Wraps the entire app in `main.jsx`. Catches any uncaught React render error:
```
[error] React render error  { error: <message>, componentStack: ... }
```
Shows a fallback UI with "Back to Dashboard" button instead of a blank screen.

### usePracticeSession — `frontend/src/hooks/usePracticeSession.js`

| Log | When |
|---|---|
| `[debug] state →` | Every state machine transition (loading → question → feedback) |
| `[debug] question loaded` | Successfully fetched next question |
| `[info] answer result` | Correct or incorrect |
| `[info] session exhausted` | No more questions (204) |
| `[error] load question failed` | API error on GET /next |
| `[error] submit answer failed` | API error on POST /answers |

### AuthContext — `frontend/src/context/AuthContext.jsx`

```
[debug] auth check start
[debug] login status  { userId, email }   ← or { loggedIn: false }
[debug] logout
[error] auth check error  { error }
```

### DashboardPage / PracticeSetupPage

```
[debug] dashboard fetch start
[info]  dashboard loaded  { sessionsCompleted, questionsAnswered, accuracyPct }
[error] dashboard fetch failed  { error }

[info]  starting session  { section, grandTotal, domainBandCounts }
[info]  session created  { sessionId }
[error] session create failed  { error }       ← shows inline error in UI (not alert)
```

---

## 9. How to Diagnose Common Problems

### "Session not found" 404 on the practice page

1. Look for: `DEBUG not found: Session not found: <uuid> [GET /api/sessions/<uuid>/next]`
2. The session UUID in the URL doesn't exist in DB.
3. Check: was the session created? Search logs for `INFO session created id=<uuid>`.
4. If it was never created, look for the `POST /api/sessions` request — did it return 201?

### "Answer recorded" never appears after student submits

1. Find the reqId for the `POST /api/sessions/{id}/answers` call.
2. If `DEBUG duplicate answer` appears → student already answered that question.
3. If `DEBUG not found` for `Answer for question` → the question has no answer record in `question_answers` table — pipeline data issue.
4. If `DEBUG invalid request: studentAnswer must not be blank` → frontend sent null/empty answer.

### Gap analysis always returns fallback cards

1. Look for: `ERROR gap analysis failed after 2 attempts questionId=<uuid>`.
2. Check if `ResourceNotFoundException` fired before the loop (question or answer not in DB).
3. If both attempts failed: check `WARN gap analysis attempt 1/2 failed` for the root cause — likely Claude API timeout or rate limit.

### Dashboard shows 0 stats even though answers exist

1. Look for `INFO dashboard computed userId=<uuid> sessions=0 questions=0`.
2. If `questions=0`: the `session_answers` query may not be finding rows for this `userId`. Check that sessions have `user_id` set.
3. If `sessions=0`: sessions exist but status ≠ `completed` (known issue #44 — sessions never transition to completed).

### 500 on any request

1. Find: `ERROR Unhandled RuntimeException on METHOD /path: <message>` with reqId.
2. The full stack trace is on the lines immediately following — look for the top application class in the trace (first line starting with `com.satengine`).
3. That class + line number is where to fix.

### Frontend shows blank screen

1. Open browser console.
2. Look for `[error] React render error` from ErrorBoundary.
3. The `componentStack` in the log data shows which component threw.

### API call succeeds on backend but frontend shows error

1. Check browser console for `← API error` line — it includes `status` and `body`.
2. Cross-reference the `status` with Section 5 above to identify which exception was thrown.
3. If status is 500: `body` will say `"An unexpected error occurred"` — go to server logs with the reqId.

---

## 10. Log Level Configuration

**File:** `src/main/resources/logback-spring.xml`

```xml
<logger name="com.satengine" level="DEBUG"/>   <!-- all app code: DEBUG and above -->
<root level="INFO"/>                            <!-- Spring internals: INFO and above -->
```

**Suppressed to WARN (too noisy at INFO):**
- `org.springframework.web.servlet.DispatcherServlet`
- `org.springframework.security`
- `org.hibernate.SQL`
- `org.apache.catalina`
- `org.springframework.boot.web`

To temporarily see Hibernate SQL (to debug a query):
```xml
<logger name="org.hibernate.SQL" level="DEBUG"/>
```

To quiet down app DEBUG in production, change:
```xml
<logger name="com.satengine" level="INFO"/>
```

---

## 11. Adding New Exception Handling — Checklist

When adding a new service method:

```
[ ] Use ResourceNotFoundException for any .orElseThrow() on DB lookups
[ ] Use InvalidRequestException for bad input that passes bean validation
[ ] Use DuplicateAnswerException only for the answer-twice scenario
[ ] Never use bare RuntimeException or IllegalArgumentException in app code
[ ] Never write catch(Exception e) { /* ignore */ } — always log at WARN/ERROR
[ ] If falling back silently (e.g. bad JSON), log WARN with the relevant ID and error message
[ ] If it's a real failure (data corruption, serialization error), log ERROR + throw
[ ] Add @Slf4j to every new class that logs
```

When adding a new endpoint:
```
[ ] The controller only needs entry/exit logging if it adds context beyond what RequestLoggingFilter provides
[ ] Let exceptions propagate to GlobalExceptionHandler — don't wrap in try-catch in controllers
[ ] Exception to the rule: parse operations (UUID.fromString, etc.) that map to 401/403 should be caught locally
```
