# 21 — Deployment Architecture

---

## Overview

SatEngine is a **monolithic Spring Boot + React SPA** deployed on Railway with Supabase as the production database. There is no CI/CD pipeline — deployment is manual via Railway watching the GitHub repository.

---

## Infrastructure Stack

```mermaid
flowchart TD
    subgraph DEV["Local Development"]
        A[Developer Machine\nmacOS] --> B[Local PostgreSQL\nDocker container\nport 5432]
        A --> C[Spring Boot\nprofile: local\nport 8080]
        A --> D[Vite dev server\nport 5173\nproxies /api to :8080]
        A --> E[.env file\nall secrets local]
    end

    subgraph GH["GitHub — gopalvramana/sat-engine"]
        F[main branch\nproduction-ready]
        G[dev branch\nactive development]
        G -->|PR + merge| F
    end

    subgraph PROD["Production — Railway"]
        H[Railway Container\nJava 21 JRE Alpine\nprofile: railway]
        H --> I[Supabase\nPostgreSQL 16 + pgvector\nPrimary DB]
        H --> J[Sentry\nError tracking]
    end

    subgraph MONITOR["Monitoring"]
        K[UptimeRobot\nPings /actuator/health\nevery 5 minutes]
        K --> H
    end

    subgraph NEON["Dev Question Sync"]
        L[Neon\nServerless PostgreSQL\nApproved questions only]
        A -->|NeonSyncService\nSync approved questions| L
    end

    A -->|git push| GH
    GH -->|Railway watches repo\nauto-deploys on push| PROD
```

---

## Branch Strategy

```mermaid
gitGraph
    commit id: "init"
    branch dev
    checkout dev
    commit id: "feature work"
    commit id: "sprint 1"
    commit id: "sprint 2"
    checkout main
    merge dev id: "release"
    checkout dev
    commit id: "sprint 3"
```

| Branch | Purpose | Railway deploys from |
|--------|---------|---------------------|
| `main` | Production-ready code | Yes (configured in Railway) |
| `dev` | Active development | Optional staging deploy |

**No GitHub Actions CI/CD** — no `.github/workflows/` directory. All deployments are triggered by Railway watching the GitHub repository. Tests run locally only.

---

## Deployment Flow — Step by Step

```mermaid
sequenceDiagram
    participant Dev as Developer
    participant Git as GitHub
    participant Railway
    participant Maven
    participant JVM

    Dev->>Git: git push origin main
    Git->>Railway: Webhook — new commit on main
    Railway->>Maven: mvn clean package -DskipTests -Dskip.frontend=true
    Maven->>Maven: Download deps (cached)\nCompile Java 21\nPackage fat JAR
    Maven->>Railway: target/sat-engine.jar (~83 MB)
    Railway->>JVM: java -Dspring.profiles.active=railway -jar app.jar
    JVM->>JVM: Load application-railway.yml\nRead env vars from Railway dashboard
    JVM->>Railway: Flyway runs pending migrations
    JVM->>Railway: App ready on $PORT
    Railway->>Railway: Health check GET /actuator/health
    Railway->>Dev: Deploy complete ✅
```

**Docker build (alternative path):**

```mermaid
flowchart LR
    A[Dockerfile Stage 1\nmaven:3.9-eclipse-temurin-21-alpine] --> B[mvn dependency go-offline\ncache deps layer]
    B --> C[mvn package -DskipTests\n-Dskip.frontend=true]
    C --> D[target/sat-engine.jar]
    D --> E[Dockerfile Stage 2\neclipse-temurin:21-jre-alpine]
    E --> F[COPY jar → app.jar\nEXPOSE 8080\njava -Dspring.profiles.active=railway -jar app.jar]
```

**Why `-Dskip.frontend=true`:** The React frontend is pre-built locally (`npm run build`) and committed to `src/main/resources/static/app/`. Docker and Railway skip the Node/npm/Vite build entirely — saving 5–10 minutes per deploy.

---

## Spring Boot Profiles

```mermaid
flowchart TD
    A[JVM starts] --> B{--spring.profiles.active}
    B -->|local| C[application.yml\n+ application-local.yml]
    B -->|railway| D[application.yml\n+ application-railway.yml]
    B -->|none set| E[application.yml only\nlocalhost defaults]

    C --> F[Secrets from .env file\nloaded by dotenv-java\nat SatEngineApplication startup]
    D --> G[Secrets from Railway\nenvironment variables\ninjected by Railway runtime]
```

### Profile Comparison

| Config | `local` | `railway` |
|--------|---------|-----------|
| Database | `localhost:5432/satengine` | `$DB_URL` (Supabase) |
| DB credentials | `.env` file | Railway dashboard vars |
| Google OAuth2 | Disabled (DevLoginController) | `$GOOGLE_CLIENT_ID` + `$GOOGLE_CLIENT_SECRET` |
| Connection pool max | Default (10) | 3 connections (small container) |
| Connection pool min-idle | Default | 1 |
| Keep-alive | Default | 60s |
| Max lifetime | Default | 300s (5 min) |
| Server port | 8080 | `$PORT` (Railway sets) |
| HTTPS | None (localhost) | Auto-provisioned by Railway |
| X-Forwarded-Proto | Not set | `forward-headers-strategy: framework` |
| Neon sync | Available | Disabled (NEON_SYNC_URL blank) |
| Sentry | Off (DSN blank) | On (`$SENTRY_DSN` set) |
| Frontend | Vite dev server :5173 | Static files from JAR |

---

## All Environment Variables

```mermaid
block-beta
    columns 2

    A["🔴 REQUIRED on Railway"]:2

    B["DB_URL\njdbc:postgresql://supabase-host/satengine"]:1
    C["DB_USERNAME\nPostgreSQL username"]:1

    D["DB_PASSWORD\nPostgreSQL password"]:1
    E["GOOGLE_CLIENT_ID\nOAuth2 app client ID"]:1

    F["GOOGLE_CLIENT_SECRET\nOAuth2 app client secret"]:1
    G["ANTHROPIC_API_KEY\nClaude API key (pipeline + gap analysis)"]:1

    H["🟡 OPTIONAL on Railway"]:2

    I["SENTRY_DSN\nError tracking DSN"]:1
    J["SENTRY_ENVIRONMENT\nlabel: production / staging"]:1

    K["🔵 LOCAL DEV ONLY (in .env)"]:2

    L["NEON_SYNC_URL\njdbc:postgresql://neon-host/neondb"]:1
    M["NEON_SYNC_USERNAME\nNeon DB username"]:1

    N["NEON_SYNC_PASSWORD\nNeon DB password"]:1
    O["PORT\nRailway sets automatically"]:1
```

### `.env.example` (local dev template)

```bash
DB_URL=jdbc:postgresql://localhost:5432/satengine
DB_USERNAME=postgres
DB_PASSWORD=yourpassword

ANTHROPIC_API_KEY=sk-ant-...

# Neon sync (local dev only — sync approved questions to Neon)
NEON_SYNC_URL=jdbc:postgresql://ep-xxxx.us-east-1.aws.neon.tech/neondb?sslmode=require
NEON_SYNC_USERNAME=neondb_owner
NEON_SYNC_PASSWORD=your_neon_password
```

---

## What Each Service Does

### Railway — Application Hosting

```mermaid
flowchart LR
    A[Railway Container\nLinux Alpine\nJava 21 JRE] --> B[Spring Boot :8080]
    B --> C[React SPA\nstatic files served\nfrom /app/]
    B --> D[REST API\n/api/**]
    B --> E[Admin UI\n/admin/**]
    B --> F[Health\n/actuator/health]
    A --> G[Railway Networking\nAuto SSL cert\nCustom domain\nX-Forwarded-Proto]
    A --> H[Railway Env Vars\nAll secrets injected\nat container start]
```

- **Auto-restart:** If `/actuator/health` returns DOWN 3× in a row → container restarts automatically
- **Startup grace:** 60 seconds before health checks begin (Flyway + Spring Boot startup)
- **SSL:** Auto-provisioned — HTTPS enforced for all traffic
- **Port:** Railway sets `$PORT` environment variable; app reads `server.port: ${PORT:8080}`

### Supabase — Production Database

```mermaid
flowchart LR
    A[Supabase\nPostgreSQL 16] --> B[questions table\n+ all JSONB fields]
    A --> C[users table\nOAuth2 users]
    A --> D[sessions + session_answers\nStudent activity]
    A --> E[question_answers\ncorrect answers separated]
    A --> F[question_reviews\nQA results]
    A --> G[pgvector extension\nembedding column\nunused currently]
```

- **What we use:** PostgreSQL database only
- **What we don't use:** Supabase Auth, Realtime, Edge Functions, Storage
- **App handles auth** via Spring Security + Google OAuth2
- **Connection:** HikariCP pool — max 3 connections (Railway free tier limits)
- **Free tier:** 500MB storage (plenty for question bank + student data)
- **Scale path:** $25/month Pro plan

### Neon — Dev Question Sync (local only)

```mermaid
flowchart LR
    subgraph LOCAL["Local Dev"]
        A[Local PostgreSQL\nall questions\ndraft + approved + rejected]
        B[Pipeline generates\n+ enriches + approves\nquestions locally]
        B --> A
    end

    subgraph NEON["Neon Cloud"]
        C[Neon PostgreSQL\napproved questions only\nclean question bank]
    end

    A -->|NeonSyncService\nSync approved only\nbatches of 50\nupsert by external_id| C

    subgraph PROD["Production"]
        D[Railway + Supabase\nuses question bank\nthat was synced]
    end

    C -.->|Optional: import\napproved questions| D
```

**Why Neon exists:** Local dev DB contains everything including rejected/draft questions. Neon holds only the clean approved question bank. This keeps production clean without needing to carefully filter on every query.

**NeonSyncService syncs:**
- `questions` WHERE `status = 'approved'`
- `question_answers` (joined by `external_id`)
- `question_reviews` (joined by `external_id`)
- Upsert on conflict — idempotent, safe to run multiple times

### Sentry — Error Tracking

```mermaid
flowchart LR
    A[Unhandled RuntimeException\nin Spring Boot] --> B[GlobalExceptionHandler\nreturns HTTP 500]
    B --> C[Sentry SDK\nautomatically captures]
    C --> D[Sentry dashboard\nstack trace + breadcrumbs\n+ request path + reqId]

    E[React component error] --> F[ErrorBoundary]
    F --> G[Sentry.captureException]
    G --> D
```

- Spring Boot: all unhandled exceptions at `ERROR` level auto-sent
- React: `@sentry/react` captures component errors via ErrorBoundary
- Breadcrumbs: prior INFO+ logs attached as context to each error
- Environment tag: `SENTRY_ENVIRONMENT=production` separates prod vs staging errors
- Free tier: 5,000 errors/month

### UptimeRobot — Uptime Monitoring

- Pings `GET /actuator/health` every 5 minutes
- Alerts via email/SMS if app goes down
- `show-details: never` in Actuator config — health response is just `{"status":"UP"}` (no credentials leaked)

---

## Observability Stack

```mermaid
flowchart TD
    A[Request arrives] --> B[RequestLoggingFilter\nGenerates reqId\nLogs path + duration]
    B --> C[MDC: reqId=abc123\nAll logs in this request\ncarry this ID]
    C --> D[Application code\nDEBUG logs for satengine.*\nWARN for framework noise]
    D --> E{Error?}
    E -->|RuntimeException| F[GlobalExceptionHandler\nHTTP 500 + structured JSON]
    F --> G[Sentry\nstack trace + reqId\n+ all breadcrumbs]
    E -->|No error| H[Response logged\nwith duration]

    I[/actuator/health] --> J[Returns status: UP/DOWN]
    J --> K[Railway auto-restart on DOWN]
    J --> L[UptimeRobot alert on DOWN]
```

**Log levels (logback-spring.xml):**

| Logger | Level | Reason |
|--------|-------|--------|
| `com.satengine` | DEBUG | Full app visibility |
| `org.springframework.web.servlet.DispatcherServlet` | WARN | Suppress request noise |
| `org.springframework.security` | WARN | Suppress auth noise |
| `org.hibernate.SQL` | WARN | Suppress query noise |
| `org.apache.catalina` | WARN | Suppress Tomcat noise |
| Root | INFO | Everything else |

---

## Frontend Build & Static Serving

```mermaid
flowchart TD
    A[Developer changes\nReact code in frontend/] --> B[npm run build\nin frontend/ directory]
    B --> C[Vite bundles\nJS + CSS + KaTeX fonts]
    C --> D[Output: frontend/dist/]
    D --> E[Committed to git:\nsrc/main/resources/static/app/]
    E --> F[mvn package\nSpring Boot includes\nstatic/ in JAR]
    F --> G[sat-engine.jar\ncontains React app\nas static files]
    G --> H[Railway deploys JAR\nSpring serves /app/**\nSpaRoutingController → index.html]
```

**Dev mode:**
```bash
cd frontend && npm run dev    # Vite on :5173, proxies /api → :8080
cd .. && mvn spring-boot:run  # Spring Boot on :8080
```

**Important:** Every React code change must be followed by `npm run build` and committing the updated `static/app/` files before deploying. Railway does NOT run the frontend build.

---

## Running Pipeline Jobs in Production

Pipeline jobs (`--job=generate`, `--job=enrich`, etc.) can be run on Railway:

```mermaid
flowchart LR
    A[Railway Dashboard\nService → Run Command] --> B[java -jar app.jar\n--job=generate\n--count=20\n--domain=algebra]
    B --> C[SatEngineApplication\ndetects --job flag]
    C --> D[Sets WebApplicationType.NONE\nNo web server starts]
    C --> E[PipelineRunner.run\nexecutes job]
    E --> F[Writes to Supabase\nvia JDBC]
    F --> G[System.exit 0]
```

The web server does NOT start when `--job=` flag is present — the JAR acts as a CLI tool.

---

## Maven Build Configuration

### Key Dependencies

| Dependency | Version | Purpose |
|-----------|---------|---------|
| Spring Boot | 3.2.5 | Web framework |
| Spring Security + OAuth2 Client | bundled | Google authentication |
| Spring Data JPA | bundled | Database ORM |
| PostgreSQL JDBC | bundled | Database driver |
| Flyway Core | bundled | Schema migrations |
| pgvector | 0.1.6 | Vector column type |
| Anthropic Java SDK | 2.18.0 | Claude API |
| Lombok | bundled | Boilerplate reduction |
| dotenv-java | 3.0.0 | `.env` file loading |
| Sentry Spring Boot Jakarta | 7.14.0 | Error tracking |
| SpringDoc OpenAPI | 2.5.0 | Swagger UI at `/swagger-ui.html` |
| Testcontainers PostgreSQL | 1.19.8 | Test DB (spins up real Postgres) |
| OkHttp | bundled (Anthropic) | HTTP client for Claude API |

### Build Plugins

| Plugin | Purpose |
|--------|---------|
| `maven-compiler-plugin` | Java 21 + Lombok annotation processor |
| `spring-boot-maven-plugin` | Package fat JAR with all deps |
| `frontend-maven-plugin` | Install Node 22.13.0, run `npm install` + `npm run build` |

**Skip frontend:** `-Dskip.frontend=true` — used in Docker and Railway builds.

---

## Adding a New Migration — Process

Every Sprint that changes the DB schema must follow this process:

```mermaid
flowchart LR
    A[Need schema change] --> B[Create new file:\nV44__description.sql]
    B --> C[src/main/resources/\ndb/migration/]
    C --> D[Write SQL\nCREATE TABLE / ALTER TABLE\nCREATE INDEX]
    D --> E[Run locally:\nmvn spring-boot:run\nFlyway auto-applies V44]
    E --> F[Verify in local DB]
    F --> G[git commit V44__*.sql]
    G --> H[Deploy to Railway\nFlyway auto-applies V44\non startup]
```

**Current version:** V43 (last migration)
**Next migrations planned:**

| Migration | Sprint | Issue | What |
|-----------|--------|-------|------|
| `V44__add_user_skill_mastery.sql` | Sprint 3 | #64 | `user_skill_mastery` table |
| `V45__add_error_type_to_session_answers.sql` | Sprint 3 | #72 | `error_type` column on `session_answers` |

**Rules:**
- Never modify an existing migration file — Flyway checksums them
- Never delete a migration file
- Always test locally before committing
- Migration filenames: `V{number}__{snake_case_description}.sql`

---

## Security Model

```mermaid
flowchart TD
    A[Request arrives] --> B[Spring Security filter chain]
    B --> C{Path}
    C -->|/actuator/health| D[Permit all\nno auth required]
    C -->|/login, /oauth2/**| E[Permit all\nOAuth2 flow]
    C -->|/admin/**| F[Require auth\nAdmin role]
    C -->|/api/**| G[Require auth\nAny authenticated user]
    C -->|/app/**| H[Permit all\nSPA static files]

    G --> I{HttpSession\nhas userId?}
    I -->|Yes| J[Extract userId\nfrom session]
    I -->|No| K[HTTP 401\nAxios → redirect to /login]

    L[Google OAuth2 callback] --> M[OAuth2SuccessHandler]
    M --> N[Create or update user in DB]
    N --> O[Set userId in HttpSession]
    O --> P[Redirect to /dashboard]
```

**No JWT** — session-based auth via Spring HttpSession. Sessions stored in memory (Railway) — students are logged out on container restart.

---

## Environment Summary Table

| Aspect | Local Dev | Production (Railway) |
|--------|-----------|---------------------|
| Spring Profile | `local` | `railway` |
| Secrets Source | `.env` file | Railway dashboard |
| Database | Docker PostgreSQL :5432 | Supabase PostgreSQL |
| Frontend | Vite dev server :5173 | Static files in JAR |
| OAuth2 | Disabled (DevLoginController) | Google OAuth2 |
| Pipeline jobs | `java -jar ... --job=X` | Railway "Run Command" |
| Neon sync | Available | Disabled |
| SSL | None | Auto (Railway) |
| Health checks | None | `/actuator/health` |
| Error tracking | Off | Sentry |
| Uptime monitoring | None | UptimeRobot |
| DB connections | Default HikariCP | Max 3 (pool tuned) |
| Log level (app) | DEBUG | DEBUG (→ Sentry on ERROR) |
