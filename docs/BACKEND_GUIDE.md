# Aptify — Backend Code Guide
> Java Spring Boot. Every file explained. Every pattern named. Written so a non-Java developer can follow it.

---

## How Spring Boot Works (30-second primer)

Spring Boot is a Java framework that starts a web server and automatically wires your classes together. You annotate a class with `@Service`, `@Controller`, or `@Repository` and Spring finds it, creates one instance, and injects it wherever it's needed. You almost never write `new SomeClass()` — Spring does it for you. This pattern is called **Dependency Injection**.

---

## Project Structure

```
src/main/java/com/satengine/
│
├── SatEngineApplication.java       ← starts everything
│
├── config/                         ← cross-cutting rules (security, errors, routing)
│   ├── SecurityConfig.java
│   ├── OAuth2SuccessHandler.java
│   ├── GlobalExceptionHandler.java
│   └── SpaRoutingController.java
│
├── domain/                         ← core business data + logic
│   ├── question/                   ← Question entity + CRUD + queries
│   ├── session/                    ← Session + SessionAnswer entities + practice logic
│   └── user/                       ← User entity + login logic
│
├── api/                            ← endpoints that don't fit one domain
│   ├── auth/                       ← /api/auth/me, /dev/login
│   ├── dashboard/                  ← /api/dashboard
│   └── gap/                        ← /api/gaps/analyze (AI gap analysis)
│
├── dto/                            ← data shapes that go in/out of the API
│
└── pipeline/                       ← offline question generation (not student-facing)
    ├── PipelineRunner.java
    ├── GenerateStage.java
    ├── AgentReviewStage.java
    ├── EnrichStage.java
    └── claude/
        ├── ClaudeClient.java
        └── PromptLibrary.java
```

---

## Pattern 1: Layered Architecture

Every feature follows the same 4-layer stack. Once you understand it for one feature, you understand it for all.

```
HTTP Request
     ↓
Controller      ← receives the request, validates input, returns response
     ↓
Service         ← all business logic lives here
     ↓
Repository      ← talks to the database
     ↓
Entity/Table    ← the actual data shape
```

**Example — student submits an answer:**
```
POST /api/sessions/{id}/answers
     ↓
SessionController.submitAnswer()     ← reads sessionId from URL, answer from body
     ↓
SessionService.submitAnswer()        ← checks answer, saves result, calculates isCorrect
     ↓
SessionAnswerRepository.save()       ← writes one row to session_answers table
     ↓
session_answers table                ← { session_id, question_id, student_answer, is_correct }
```

The rule: **Controllers are thin. Services are where the thinking happens.**

---

## Pattern 2: Entities and JPA (Java ↔ Database)

An `@Entity` class is a Java representation of a database table. Each field maps to a column. Spring's JPA layer automatically converts between Java objects and SQL rows.

**Example — `Session.java`:**
```java
@Entity                           // ← tells Spring "this maps to a DB table"
@Table(name = "sessions")         // ← which table
@Getter @Setter                   // ← Lombok: auto-generates getters/setters
@Builder                          // ← Lombok: lets you do Session.builder().userId(x).build()
public class Session {

    @Id
    @GeneratedValue                // ← DB auto-generates the UUID
    private UUID id;

    @Column(name = "user_id")
    private UUID userId;           // ← NOT a JOIN — deliberately stored as UUID, not a User object

    @Column(name = "status")
    private String status;         // "active" | "completed"

    @PrePersist                    // ← runs automatically before first save to DB
    protected void onCreate() {
        if (startedAt == null) startedAt = OffsetDateTime.now();
    }
}
```

**Why userId is UUID, not User?**
Sessions reference users by UUID instead of `@ManyToOne User user`. This is an intentional architectural choice: it avoids Hibernate lazy-loading traps and keeps session queries fast. When you need user data you fetch it separately.

**JSONB fields — storing structured data in one column:**
```java
@JdbcTypeCode(SqlTypes.JSON)
@Column(name = "explanation_steps", columnDefinition = "jsonb")
private String explanationSteps;   // stored as JSON string, parsed in frontend
```
Fields like `explanationSteps`, `coreConcept`, `animation`, `choiceExplanations` are complex nested objects stored as PostgreSQL JSONB. The backend treats them as strings and doesn't parse them — the frontend does the parsing with `JSON.parse()`.

---

## Pattern 3: Repository — Database Queries

A `Repository` interface extends `JpaRepository` and gets free CRUD methods for nothing. You then add custom queries as needed.

**Free methods you get without writing anything:**
```java
// These all work just by extending JpaRepository<Session, UUID>
sessionRepository.findById(id)           // SELECT * WHERE id = ?
sessionRepository.save(session)          // INSERT or UPDATE
sessionRepository.findAll()              // SELECT *
sessionRepository.deleteById(id)         // DELETE WHERE id = ?
```

**Two ways to write custom queries:**

**Method name convention** — Spring reads the method name and generates SQL automatically:
```java
// Spring reads this method name and generates:
// SELECT * FROM sessions WHERE user_id = ? ORDER BY started_at DESC
List<Session> findByUserIdOrderByStartedAtDesc(UUID userId);
```

**@Query annotation** — for complex SQL that can't be expressed as a method name:
```java
@Query("""
    SELECT COUNT(s) FROM Session s
    WHERE s.userId = :userId AND s.status = 'completed'
    """)
long countCompletedByUser(@Param("userId") UUID userId);
```

**Native SQL queries** — when you need PostgreSQL-specific features (like RANDOM()):
```java
@Query(value = """
    SELECT * FROM questions
    WHERE status = 'approved' AND domain = :domain
    ORDER BY RANDOM() LIMIT 1
    """, nativeQuery = true)             // ← nativeQuery=true means raw SQL, not JPQL
Optional<Question> findNextQuestionByDomain(...);
```

---

## Pattern 4: Service — Business Logic

Services are `@Service` classes that contain all thinking. They call repositories, apply rules, and return results to controllers.

**Key example — `SessionService.submitAnswer()`:**
```java
@Transactional                         // ← if anything fails, the whole DB write rolls back
public AnswerFeedback submitAnswer(UUID sessionId, SubmitAnswerRequest req) {

    // 1. Verify session exists (throws RuntimeException if not — caught by GlobalExceptionHandler)
    sessionRepository.findById(sessionId)
            .orElseThrow(() -> new RuntimeException("Session not found: " + sessionId));

    // 2. Prevent double-answering the same question
    sessionAnswerRepository.findBySessionIdAndQuestionId(sessionId, req.questionId())
            .ifPresent(a -> { throw new RuntimeException("Already answered..."); });

    // 3. Check answer against the answer table (correct answer is NOT in Question entity)
    QuestionAnswer answer = questionAnswerRepository.findByQuestionId(req.questionId())
            .orElseThrow(...);
    boolean isCorrect = answer.getCorrectAnswer().equalsIgnoreCase(req.studentAnswer().trim());

    // 4. Save the student's answer
    SessionAnswer sessionAnswer = SessionAnswer.builder()
            .sessionId(sessionId)
            .questionId(req.questionId())
            .studentAnswer(req.studentAnswer())
            .isCorrect(isCorrect)
            .build();
    sessionAnswerRepository.save(sessionAnswer);

    // 5. Return feedback (now safe to reveal correct answer)
    return new AnswerFeedback(req.questionId(), isCorrect, answer.getCorrectAnswer(), ...);
}
```

**`@Transactional` — what it means:**
Wraps the method in a database transaction. If any line throws an exception, all DB writes in that method are rolled back. Use it on any method that writes to the DB. `@Transactional(readOnly = true)` for queries — slightly faster.

---

## Pattern 5: Controller — HTTP Endpoints

Controllers are `@RestController` classes that map HTTP requests to service calls.

```java
@RestController
@RequestMapping("/api/sessions")        // ← all methods in this class start with /api/sessions
@RequiredArgsConstructor                // ← Lombok: constructor injection of all final fields
public class SessionController {

    private final SessionService sessionService;

    @PostMapping                        // ← POST /api/sessions
    public ResponseEntity<SessionResponse> createSession(
            @Valid @RequestBody CreateSessionRequest request,   // ← body parsed from JSON
            HttpSession httpSession                              // ← Spring injects HTTP session
    ) {
        UUID userId = resolveUserId(httpSession);               // ← read from cookie session
        Session session = sessionService.createSession(userId, request);
        return ResponseEntity.status(201).body(...);            // ← HTTP 201 Created
    }

    @GetMapping("/{id}/next")           // ← GET /api/sessions/{id}/next
    public ResponseEntity<QuestionResponse> getNextQuestion(
            @PathVariable UUID id       // ← {id} from URL becomes this Java variable
    ) {
        return sessionService.getNextQuestion(id)
                .map(ResponseEntity::ok)                        // ← 200 with body if question found
                .orElse(ResponseEntity.noContent().build());    // ← 204 No Content when exhausted
    }
}
```

**HTTP status codes used:**
- `200 OK` — success with response body
- `201 Created` — resource was created
- `204 No Content` — success but no body (session exhausted)
- `401 Unauthorized` — not logged in
- `404 Not Found` — resource doesn't exist
- `409 Conflict` — already answered this question
- `500 Internal Server Error` — something broke

---

## Pattern 6: DTOs — Data Transfer Objects

DTOs are simple data containers that define exactly what goes in and out of the API. They are **not** entities — they don't map to DB tables.

**Why separate from entities?**
The `Question` entity has 35+ fields including the correct answer. The `QuestionResponse` DTO sent to the frontend has ~15 fields and deliberately **excludes** the correct answer. This separation is the security model.

```java
// CreateSessionRequest — what the frontend sends
public record CreateSessionRequest(
        @NotBlank String sessionType,       // @NotBlank = validated automatically
        String section,
        Map<String, Map<String, Integer>> domainBandCounts
) {}

// SessionResponse — what we send back
public record SessionResponse(
        UUID id,
        String sessionType,
        String section,
        String status,
        OffsetDateTime startedAt,
        int questionsAnswered,
        int correctCount,
        int totalQuestions
) {}
```

`record` is a Java feature that auto-generates `equals()`, `hashCode()`, `toString()`, and constructor. Perfect for DTOs.

---

## Pattern 7: Error Handling — GlobalExceptionHandler

Instead of try-catching in every controller, one central class handles all errors.

```java
@RestControllerAdvice                  // ← intercepts exceptions from any @RestController
public class GlobalExceptionHandler {

    @ExceptionHandler(RuntimeException.class)
    public ResponseEntity<Map<String, String>> handleRuntimeException(RuntimeException ex) {
        String message = ex.getMessage().toLowerCase();

        if (message.contains("not found")) {
            return ResponseEntity.status(404).body(Map.of("error", ex.getMessage()));
        }
        if (message.contains("already answered")) {
            return ResponseEntity.status(409).body(Map.of("error", ex.getMessage()));
        }
        // Unhandled → 500
        return ResponseEntity.status(500).body(Map.of("error", "An unexpected error occurred"));
    }
}
```

**How it works in practice:**
Service throws `new RuntimeException("Session not found: " + id)`. GlobalExceptionHandler intercepts it, sees "not found" in the message, and returns `{ "error": "Session not found: abc" }` with HTTP 404. The controller never needs a try-catch.

---

## Pattern 8: Security

`SecurityConfig.java` controls who can access what.

```java
@Configuration
@EnableWebSecurity
public class SecurityConfig {
    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
            .csrf(AbstractHttpConfigurer::disable)          // ← disabled: REST API, session cookies, same-origin only
            .authorizeHttpRequests(auth -> auth
                    .anyRequest().permitAll()                // ← all URLs open for now (Phase 2 will restrict)
            )
            .logout(logout -> logout
                    .logoutUrl("/api/auth/logout")
                    .invalidateHttpSession(true)
                    .deleteCookies("JSESSIONID")
                    .logoutSuccessUrl("/login")
            );

        // Only wire Google OAuth if credentials are configured (not needed on local dev)
        if (clientRegistrationRepository != null) {
            http.oauth2Login(oauth2 -> oauth2
                    .loginPage("/login")
                    .successHandler(oauth2SuccessHandler)   // ← our custom handler
            );
        }
        return http.build();
    }
}
```

**The auth flow:**
1. User clicks "Sign in with Google" → Google → `OAuth2SuccessHandler.onAuthenticationSuccess()`
2. Handler calls `UserService.findOrCreate(email, name, picture)` → creates/updates user in DB
3. Handler stores `userId` in `HttpSession` → Spring sets `JSESSIONID` cookie in browser
4. Every subsequent request → browser sends cookie → Spring retrieves session → controller reads `userId`

**On local dev:** `DevLoginController` (only active on `local` Spring profile) does steps 2+3 without Google, calling `POST /dev/login`.

---

## Pattern 9: Lombok Annotations

Lombok generates boilerplate Java code at compile time. You'll see these annotations everywhere:

| Annotation | What it generates |
|-----------|------------------|
| `@Getter` | `getFieldName()` for every field |
| `@Setter` | `setFieldName()` for every field |
| `@Builder` | `Session.builder().status("active").build()` pattern |
| `@NoArgsConstructor` | `new Session()` — required by JPA |
| `@AllArgsConstructor` | constructor with all fields |
| `@RequiredArgsConstructor` | constructor with all `final` fields — used for dependency injection |
| `@Slf4j` | creates `log.info(...)`, `log.error(...)` etc |

---

## Pattern 10: The Pipeline — ApplicationRunner

The pipeline (question generation) runs in the same Spring Boot JAR as the web server but in a different mode.

```java
@Component
public class PipelineRunner implements ApplicationRunner {
    @Override
    public void run(ApplicationArguments args) {
        if (!args.containsOption("job")) return;   // ← normal web server mode: skip everything

        switch (job) {
            case "generate"     -> runGenerate(args);
            case "agent-review" -> runAgentReview(args);
            case "enrich"       -> runEnrich(args);
        }
        System.exit(0);                             // ← exit after pipeline job completes
    }
}
```

**How to run it:**
```bash
java -jar sat-engine.jar --job=generate --domain=algebra --count=10
# ↑ same JAR, different mode. Normal web server doesn't start when --job is passed.
```

**Pipeline stages and what each does:**

| Stage | Claude Model | Input | Output |
|-------|-------------|-------|--------|
| `GenerateStage` | Haiku (cheap, fast) | domain + skill + difficulty | raw question JSON |
| `AgentReviewStage` | Haiku | question | 9-check QA pass/fail |
| `EnrichStage` | Opus (expensive, smart) | reviewed question | explanation steps + core concept |
| `EnrichChoiceExplanationsStage` | Opus | enriched question | per-choice explanations |
| `EnrichAnimationStage` | Opus | geometry question | SVG animation frames |
| `RenderNormalizeStage` | (no Claude) | any question | fix LaTeX formatting |
| `VisualCheckStage` | (no Claude) | geometry question | validate diagram JSON |

Each stage reads from the DB, processes, and writes back. Status transitions: `generated → reviewed → enriched → approved`.

---

## Database Migration Pattern (Flyway)

Every DB change is a versioned SQL file. Flyway runs them in order on startup.

```
db/migration/
  V1__initial_schema.sql       ← creates all tables
  V2__widen_solved_answer.sql  ← ALTER TABLE
  ...
  V42__backfill_sessions_to_dev_user.sql
```

**The rules:**
1. Never edit an existing migration file — Flyway checksums them
2. Always create a new file: `V{n+1}__description.sql`
3. File name format: `V{version}__{description}.sql` (two underscores)

---

## SPA Routing — Making React Router Work

React Router handles URLs like `/app/session/abc123` on the frontend. But when you refresh the page, the browser asks Spring Boot for `/app/session/abc123` — which doesn't exist as a Java endpoint. This controller fixes that:

```java
@Controller
public class SpaRoutingController {

    // Serve index.html for all /app/* paths — React Router takes over from there
    @GetMapping("/app/{p1:[^\\.]*}")
    public String appPath() { return "forward:/app/index.html"; }

    @GetMapping("/app/{p1:[^\\.]*}/{p2:[^\\.]*}")
    public String appSubPath() { return "forward:/app/index.html"; }

    @GetMapping("/app/{p1:[^\\.]*}/{p2:[^\\.]*}/{p3:[^\\.]*}")
    public String appSubSubPath() { return "forward:/app/index.html"; }
}
```

The regex `[^\\.]` means "path segment with no dot" — this prevents it from matching file requests like `index-abc123.js` which need to be served as actual files.

---

## API Reference — All Endpoints

### Auth
| Method | URL | What it does |
|--------|-----|-------------|
| `GET` | `/api/auth/me` | Returns logged-in user or 401 |
| `POST` | `/api/auth/logout` | Clears session, redirects to /login |
| `POST` | `/dev/login` | Local dev only — logs in as dev@satengine.local |

### Sessions
| Method | URL | What it does |
|--------|-----|-------------|
| `POST` | `/api/sessions` | Create new practice session |
| `GET` | `/api/sessions/{id}` | Get session status (count, score) |
| `GET` | `/api/sessions/{id}/next` | Get next question (204 when exhausted) |
| `POST` | `/api/sessions/{id}/answers` | Submit answer, get feedback |

### Dashboard
| Method | URL | What it does |
|--------|-----|-------------|
| `GET` | `/api/dashboard` | Stats + recent sessions for logged-in user |

### Questions
| Method | URL | What it does |
|--------|-----|-------------|
| `GET` | `/api/questions/count` | Question counts per domain/band (for setup page) |

### Gap Analysis
| Method | URL | What it does |
|--------|-----|-------------|
| `POST` | `/api/gaps/analyze` | Live Claude call to analyze why student got it wrong |

---

## Key Files Quick Reference

| You want to... | Look in... |
|---------------|-----------|
| Change who can access what URL | `config/SecurityConfig.java` |
| Change what happens after Google login | `config/OAuth2SuccessHandler.java` |
| Change how errors are returned | `config/GlobalExceptionHandler.java` |
| Add a new API endpoint | Create/edit a Controller in `api/` or `domain/` |
| Change question selection logic | `domain/session/SessionService.getNextQuestion()` |
| Change how dashboard stats are calculated | `domain/session/SessionService.getDashboard()` |
| Add a new DB column | New migration file `V{n}__description.sql` |
| Change the question generation prompt | `pipeline/claude/PromptLibrary.java` |
| Run a pipeline job | `java -jar sat-engine.jar --job=generate ...` |
| Add a new DB query | Add method to the relevant `Repository` interface |
