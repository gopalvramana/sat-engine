# 02 — Technology Stack

> All decisions are final for the prototype and launch phase. Revisit only if a specific technical problem demands it.

---

## Full Stack Decision Table

| Layer | Decision | Version | Why Chosen | Alternatives Rejected |
|-------|----------|---------|------------|----------------------|
| **Backend** | Spring Boot | 3.x — Java 21 | 20 years Java expertise. No learning tax. Production-grade from day one. | Node.js, Python FastAPI, Go |
| **Language** | Java 21 | LTS | Virtual threads for IO-bound AI calls. Modern records and pattern matching. | Kotlin, Scala |
| **Build** | Maven | Standard | Familiar, reliable, standard in Java ecosystem. | Gradle |
| **ORM** | Spring Data JPA + Hibernate | Included | Standard Spring Boot approach. No extra learning required. | jOOQ, JDBI, MyBatis |
| **Migrations** | Flyway | Bundled | Version-controlled schema. Integrated with Spring Boot. Simple. | Liquibase, manual SQL |
| **Frontend** | Thymeleaf + HTMX | Server-side | Same Spring Boot project. No npm. No build step. No CORS. No separate deployment. | React + Vite, Angular, Vue |
| **CSS** | Tailwind CSS | CDN — no build | No build step needed. Utility-first. Responsive by default. | Bootstrap, custom CSS, Material UI |
| **Math Rendering** | KaTeX | 0.16.9 CDN | 3–5x faster than MathJax. Industry standard (Khan Academy uses it). Auto-render handles all LaTeX automatically. | MathJax, custom renderer |
| **Charts** | Chart.js | 4.4.0 CDN | Simple JSON config API. CDN ready. No build step. Handles all SAT graph types. | D3.js, Recharts, Highcharts |
| **AI Provider** | Anthropic Claude | Haiku 4.5 primary | Best explanation quality for validation phase. Spring AI abstraction means easy provider switching later. | OpenAI GPT-4o, Gemini, open source |
| **AI Framework** | Spring AI | Latest | Native Spring Boot integration. Provider-agnostic. Same code works with any model. | LangChain4j, raw HTTP calls |
| **Database** | PostgreSQL | 16 via pgvector image | JSONB for diagram configs. PGVector for future AI embeddings. Most capable open source DB. | MySQL, MongoDB, SQLite |
| **DB Hosting** | Supabase | Free → Pro | 500MB free covers ~4,000 students. $25/month Pro for scale. No server management. | RDS, self-hosted, PlanetScale |
| **App Hosting** | Railway | Hobby → Pro | Deploy from GitHub push. Auto-builds Maven. Auto SSL. Zero DevOps. $5–20/month. | AWS, Heroku, DigitalOcean, Render |
| **Image CDN** | Cloudinary | Free tier | 25GB free. Auto-optimise. Simple API. Only needed for static diagram images (5% of diagrams). | S3, local files, Bunny CDN |
| **Email** | SendGrid | Free tier | 100 emails/day free. Reliable delivery. Simple API. | Mailchimp, SES, Postmark |
| **Payments** | Stripe | Standard | Best developer experience. Webhooks reliable. Used by thousands of SaaS products. | Razorpay (add later for India), PayPal |
| **Domain/DNS** | Cloudflare | Free tier | Free DDoS protection. CDN for static assets. Free SSL. Analytics included. | Namecheap DNS, Route53 |

---

## Monthly Cost at Each Stage

| Stage | Students | Railway | Supabase | Other | Total | Break-even |
|-------|----------|---------|----------|-------|-------|------------|
| Development | 0 | $0 | $0 | $1.25 (domain) | **$1.25** | — |
| Beta Launch | 0–50 | $5 | $0 | $1.25 | **$6.25** | 1 student |
| Early Growth | 50–200 | $20 | $0 | $1.25 | **$21** | 2 students |
| Growing | 200–500 | $20 | $25 | $11 | **$56** | 4 students |
| Scale | 500–1,000 | $40 | $25 | $35 | **$100** | 7 students |

---

## Key Architecture Principles

### No npm. No build step.
Tailwind from CDN. KaTeX from CDN. Chart.js from CDN. One Spring Boot project. One deployment. Zero frontend infrastructure.

### IO-bound not CPU-bound
Most server time is spent waiting for Claude API responses. This means a small Railway instance handles hundreds of concurrent users comfortably. Don't over-provision.

### JVM Memory (Production)
```
java -Xms256m -Xmx400m -XX:+UseG1GC -XX:MaxGCPauseMillis=200 -jar sat-engine.jar
```
Leaves 112MB for OS overhead on a 512MB Railway instance.

### Local Development
Docker Compose with `pgvector/pgvector:pg16` image. Spring Boot on localhost:8080. Flyway auto-runs migrations on startup.

---

## AI Model Strategy

### Phase 1 — Validation (Now → Month 6)
Use **Claude Haiku 4.5** for everything. Validate product quality with the best affordable model first.

### Phase 2 — Cost Optimisation (Month 6+)
Route by difficulty:
- Difficulty 1–3 + Prerequisites tab → **Groq/Llama 3.3 70B** ($0.79/MTok output — 6x cheaper)
- Difficulty 4–5 → **Claude Haiku 4.5**
- Difficulty 6–7 + Solution tab → **Claude Sonnet 4.6**

### Why Not Open Source From Day One
Quality is the product's core value proposition. Acely's failure is low-quality AI explanations. Never sacrifice explanation quality to save $20/month in early stages. Prove quality first. Optimise cost second.

### The Bigger Cost Lever: Caching
Cache all three AI tab responses per question in DB. At 1,000 students: 90%+ cache hit rate. Caching reduces costs by 90% at scale — far more impactful than any model switching.
