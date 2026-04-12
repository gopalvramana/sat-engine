# Observability Guide

How to know what SatEngine is doing in production — and be alerted before users tell you.

---

## The Three Pillars

| Pillar | Tool | What it gives you | Cost |
|---|---|---|---|
| **Errors** | Sentry | Every 500 / JS crash lands in your inbox with a full stack trace | Free (5k errors/mo) |
| **Uptime** | UptimeRobot | SMS/email the moment the site goes down | Free (5-min checks) |
| **Health** | Spring Boot Actuator | `/actuator/health` — Railway health checks + UptimeRobot pings | Free (built-in) |

That's the complete stack for your current scale. No Prometheus. No Grafana. No Datadog.
Add those when you have 1000+ users and need to answer "what is the p95 response time by endpoint".

---

## 1. Sentry — Error Tracking

### What it does
Every unhandled exception that reaches `GlobalExceptionHandler` with HTTP 500 is automatically sent to Sentry. Each event includes:
- Full Java stack trace
- The `reqId` and request path from MDC
- The log lines that fired before the error (breadcrumbs)
- Environment (production / staging / local)

On the frontend, every uncaught JS error and every React render crash (via `ErrorBoundary`) is captured with the React component stack.

### One-time setup (10 minutes)
1. Create a free account at **sentry.io**
2. Create two projects: **satengine-backend** (Java) and **satengine-frontend** (React)
3. Copy the DSN from each project → Settings → Client Keys (DSN)

### Railway environment variables to add
```
SENTRY_DSN          = https://xxxxx@oyyy.ingest.sentry.io/zzzzz   ← backend DSN
SENTRY_ENVIRONMENT  = production

VITE_SENTRY_DSN     = https://aaaaa@oyyy.ingest.sentry.io/bbbbb   ← frontend DSN
VITE_APP_ENV        = production
```

> **Local dev**: leave these unset. Both backend and frontend Sentry init are no-ops when the DSN is absent — nothing breaks.

### What fires automatically (no extra code needed)
| Event | Where captured |
|---|---|
| Any unhandled `RuntimeException` → HTTP 500 | `GlobalExceptionHandler.handleRuntimeException` |
| Any unhandled `Exception` → HTTP 500 | `GlobalExceptionHandler.handleGenericException` |
| React component render crash | `ErrorBoundary.componentDidCatch` → `Sentry.captureException` |
| Uncaught JS promise rejection | Sentry automatic |
| Console `error()` calls | Sentry breadcrumbs (context on next error) |

### What does NOT fire (intentional)
- HTTP 400, 404, 409 — these are user errors, not bugs. They log at DEBUG.
- Gap analysis Claude failures — these return a fallback, not a 500. If you want to track fallback rate, see Section 4.

### Alerts
In Sentry → Alerts → Create Alert Rule:
- **Condition**: "Number of events in 1 hour is more than 5"
- **Action**: Email me
- This catches error spikes without spamming you on one-off errors.

---

## 2. UptimeRobot — Uptime Monitoring

### What it does
Pings your health endpoint every 5 minutes. If it gets no response (or a non-200), it emails/SMSes you immediately.

### One-time setup (5 minutes)
1. Create a free account at **uptimerobot.com**
2. Add Monitor → HTTP(s)
3. URL: `https://your-railway-domain.up.railway.app/actuator/health`
4. Friendly name: "SatEngine Health"
5. Alert contact: your email
6. Check interval: 5 minutes (free tier default)

That's it. You'll get an email within 5 minutes of any outage.

---

## 3. Spring Boot Actuator — Health Endpoint

### Endpoint
```
GET /actuator/health
```

**Response when healthy:**
```json
{ "status": "UP" }
```

**Response when DB is unreachable:**
```json
{ "status": "DOWN" }
```

`show-details: never` is set intentionally — this prevents leaking DB URLs or credentials if the endpoint is ever publicly crawled.

### Configure Railway health check
In Railway → your service → Settings → Health Check:
- **Path**: `/actuator/health`
- **Interval**: 30s
- **Timeout**: 10s
- **Start period**: 60s (gives Spring Boot time to start)

Railway will restart the container automatically if health checks fail 3 times in a row. Without this, a crashed app sits dead until you notice.

### Also exposed
```
GET /actuator/info
```
Returns build info if you configure it. Currently empty — add `info.*` keys to `application.yml` if needed.

### What is NOT exposed (security)
These are explicitly excluded by `management.endpoints.web.exposure.include=health,info`:
- `/actuator/env` — would leak all environment variables including DB passwords
- `/actuator/beans` — internal Spring wiring
- `/actuator/heapdump` — full JVM heap (massive security risk)
- `/actuator/loggers` — allows changing log levels at runtime

---

## 4. Tracking the Gap Analysis Fallback Rate

The gap analysis feature silently falls back to generic cards when Claude fails. You won't see this in Sentry (it's not a 500) but it matters for quality.

To make it visible, add a counter to `GapAnalysisService.analyze()`:

```java
// In GapAnalysisService — after the retry loop fails:
log.error("gap analysis failed after {} attempts questionId={} — returning fallback", ...);
// Add this if you want Sentry visibility on fallback rate:
Sentry.captureMessage("gap-analysis-fallback questionId=" + questionId, SentryLevel.WARNING);
```

Alternatively, search Railway logs:
```
grep "returning fallback" app.log | wc -l
```

---

## 5. Railway Logs — Quick Access

Railway streams all stdout logs. For ad-hoc debugging:

1. Railway dashboard → your service → **Logs** tab
2. Filter by reqId: paste the 8-char ID from a Sentry error event into the search box
3. You'll see the full request trace: `→ entry` → service logs → exception → `← exit`

This is the bridge between Sentry (which tells you *what* broke) and Railway logs (which tell you *the sequence of events* that led to it).

---

## 6. What to Watch in the First Month

Once you have real students:

| Signal | How to check | What it means |
|---|---|---|
| Sentry error count > 0 | Sentry dashboard | Something broke — check the stack trace |
| UptimeRobot "DOWN" alert | Email | Server crashed or Railway restart happening |
| `gap analysis failed` in logs | Railway log search | Claude API issue — check Anthropic status |
| `session exhausted` count | Railway log search | Students running out of questions — grow the question bank |
| HTTP 409 rate rising | Railway log search | Duplicate answer submissions — likely a frontend retry bug |

---

## 7. What Comes Next (When You Have 200+ Users)

The current stack covers everything up to ~200 active users. At that point, add:

| What | Tool | Why |
|---|---|---|
| Structured log search | BetterStack Logtail (free 1GB/mo) | Grep across days of logs without Railway's 24h limit |
| Response time tracking | Sentry Performance (enable `traces-sample-rate: 0.1`) | Find slow endpoints before users complain |
| Business metrics | Custom Micrometer counters + Grafana Cloud free tier | Sessions started/day, accuracy distribution, gap card views |
| Database query monitoring | `pg_stat_statements` on Neon | Catch N+1 queries before they hurt |

---

## 8. Quick Reference — Environment Variables Needed on Railway

| Variable | Value | Purpose |
|---|---|---|
| `SENTRY_DSN` | `https://...@....ingest.sentry.io/...` | Backend error capture |
| `SENTRY_ENVIRONMENT` | `production` | Labels events in Sentry dashboard |
| `VITE_SENTRY_DSN` | `https://...@....ingest.sentry.io/...` | Frontend error capture |
| `VITE_APP_ENV` | `production` | Labels frontend events |

All four are optional — the app runs fine without them. Sentry is a silent no-op when DSN is absent.
