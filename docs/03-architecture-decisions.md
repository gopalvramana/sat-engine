# 03 — Architecture Decisions

> All Architecture Decision Records (ADRs) for the SAT Prep Platform.

---

## Rendering Architecture

### ADR-004 — Math Notation: LaTeX in PostgreSQL

**Decision:** All mathematical expressions stored as LaTeX plain text in PostgreSQL text columns.
- Inline math: `\( expression \)`
- Display/block math: `\[ expression \]`

**Rejected:** Unicode superscripts (² ³), HTML super/sub tags, MathML, images of equations.

**Reason:** LaTeX is the industry standard. KaTeX renders it perfectly. Searchable and editable in the DB. Unicode causes black box rendering bugs (proven problem in ReportLab PDF generation — never use Unicode superscripts).

**Status:** ✅ DECIDED — Validated in math-test.html

---

### ADR-005 — Diagram Architecture: Three Types

**Decision:** Three diagram types handled differently:

| Type | Storage | Rendering | Used For |
|------|---------|-----------|----------|
| `svg_programmatic` | JSONB config in `diagrams.svg_config` | JavaScript reads config, generates SVG in browser | Triangles, circles, shapes, geometry |
| `chartjs` | JSONB config in `diagrams.chart_config` | Chart.js reads config, renders canvas chart | Line graphs, scatter plots, bar charts |
| `static_image` | URL string in `diagrams.image_url` | Simple `<img>` tag | Complex diagrams that cannot be programmatic |

90% of diagrams use the first two types. No image files needed for 90% of cases.

**Rejected:** All static PNG images, all SVG as raw strings in DB, server-side SVG generation.

**Reason:** Programmatic SVG from JSON is mathematically correct by construction — directly solves Acely's impossible geometry problem. No storage costs. Vector quality. Config stored in DB, rendered client-side. New shapes = one new JavaScript function.

**Status:** ✅ DECIDED — Validated in svg-test.html and chartjs-test.html

---

### ADR-006 — SVG Renderer: JavaScript Dispatcher Pattern

**Decision:** `buildSVG(config)` dispatcher function reads `shape` type from JSONB and calls the specific draw function for that shape.

```javascript
function buildSVG(config) {
  switch(config.shape) {
    case 'right_triangle':   return drawRightTriangle(config);
    case 'circle':           return drawCircle(config);
    case 'coordinate_plane': return drawCoordinatePlane(config);
    // add more shapes here
  }
}
```

**Validated shapes:** right_triangle, isoceles_triangle, circle, rectangle, number_line, coordinate_plane, parallel_transversal, altitude_triangle

**Physics shapes to add:** vector_arrow, free_body_diagram, inclined_plane, spring, pendulum, circuit_simple, ray_diagram_lens, bohr_model, sine_wave

**Status:** ✅ DECIDED — Validated in svg-test.html

---

### ADR-007 — Rendering Initialisation Order

**Decision:** Strict order required:
1. DOM loads
2. Chart.js initialises (`DOMContentLoaded`)
3. SVG renders (`DOMContentLoaded`)
4. KaTeX auto-render fires **last** (`onload` callback)

KaTeX must run last to catch all dynamically injected content including diagram containers.

**Status:** ✅ DECIDED — Validated in combined-test.html

---

## Database Architecture

### ADR-008 — Core Schema: Two Tables

**Decision:** `questions` table and `diagrams` table. `questions.diagram_id` is a nullable UUID FK to `diagrams`.

Key fields in `questions`:
- `id` UUID PK
- `external_id` varchar(30) UNIQUE (e.g. MATH-ALG-001)
- `section` varchar(20) — math | reading_writing
- `domain` varchar(60)
- `difficulty` smallint (1–7) CHECK constraint
- `question_type` varchar(20) — mcq | spr
- `question_stem` text (LaTeX supported)
- `option_a/b/c/d` text nullable
- `correct_answer` varchar(20)
- `explanation` text (LaTeX supported)
- `diagram_id` UUID FK nullable → diagrams
- `status` VARCHAR(20) DEFAULT 'generated' — lifecycle: generated → reviewed → enriched → approved / rejected (see Question Status Lifecycle in 06-question-bank.md)

**Status:** ✅ DECIDED

---

### ADR-009 — JSONB for Diagram Configs

**Decision:** `svg_config` and `chart_config` stored as PostgreSQL JSONB columns. Accessed via Hibernate `@JdbcTypeCode(SqlTypes.JSON)` mapping to `JsonNode`.

**Example SVG config (right triangle):**
```json
{
  "shape": "right_triangle",
  "width": 220,
  "height": 190,
  "vertices": {
    "A": {"x": 20, "y": 170},
    "B": {"x": 190, "y": 170},
    "C": {"x": 190, "y": 40}
  },
  "sides": [
    {"from": "A", "to": "B", "label": "12", "labelOffset": {"x": 0, "y": 15}},
    {"from": "A", "to": "C", "label": "13", "highlight": true, "highlightColor": "#2563eb"}
  ],
  "rightAngleAt": "B",
  "angles": [{"at": "A", "label": "θ", "offset": {"x": 30, "y": -8}}]
}
```

**Status:** ✅ DECIDED

---

### ADR-010 — External ID Format

**Decision:** `{SECTION}-{DOMAIN}-{SEQ}`

| Component | Values |
|-----------|--------|
| Section | `MATH` or `RW` |
| Domain | `ALG`, `ADV`, `PS`, `GEO`, `INF`, `CRF`, `EXP`, `ENG` |
| Sequence | 3-digit zero-padded per domain: 001, 002, 003... |

Examples: `MATH-ALG-001`, `RW-CRF-012`, `MATH-GEO-047`

UUID remains the primary key. External ID is for humans only.

**Status:** ✅ DECIDED

---

### ADR-011 — Storage Estimates

| Content | Size |
|---------|------|
| 5,000 questions | ~16 MB |
| 2,500 diagrams | ~3 MB |
| AI cache (15,000 rows) | ~12 MB |
| Static content total | **~32 MB** |
| + 100 students usage | ~47 MB |
| + 500 students usage | ~107 MB |
| + 1,000 students usage | ~182 MB |

Supabase free tier (500MB) covers ~4,000 students. Storage is not a concern.

**Status:** ✅ DECIDED

---

### ADR-012 — AI Response Caching

**Decision:** Cache all three AI tab responses per question in `questions_ai_cache` table.

Schema:
```sql
question_id   UUID FK
tab_type      VARCHAR  -- solution | concept | prerequisites
content       TEXT
model         VARCHAR
generated_at  TIMESTAMPTZ
hit_count     INTEGER
```

First student to view a question pays the generation cost. Every subsequent student gets the cached response instantly at zero cost.

Cache hit rate at scale: 90%+ for popular questions.

**Status:** ✅ DECIDED

---

## Infrastructure Architecture

### ADR-013 — Hosting: Railway

**Decision:** Railway.app. Deploy by pushing to GitHub. Auto-builds Maven. Auto SSL. Custom domain.

```toml
# railway.toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "java -Xms256m -Xmx400m -XX:+UseG1GC -jar target/sat-engine.jar"
healthcheckPath = "/actuator/health"
```

**Status:** ✅ DECIDED

---

### ADR-014 — Environment Configuration

```yaml
# application-prod.yml
spring:
  datasource:
    url: ${SPRING_DATASOURCE_URL}
    username: ${SPRING_DATASOURCE_USERNAME}
    password: ${SPRING_DATASOURCE_PASSWORD}
  jpa:
    hibernate:
      ddl-auto: validate
  # No Thymeleaf — pure REST API, React frontend

server:
  port: ${PORT:8080}
```

Railway environment variables:
- `SPRING_DATASOURCE_URL`
- `SPRING_DATASOURCE_USERNAME`
- `SPRING_DATASOURCE_PASSWORD`
- `ANTHROPIC_API_KEY`
- `STRIPE_SECRET_KEY`
- `SPRING_PROFILES_ACTIVE=prod`

**Status:** ✅ DECIDED

---

### ADR-015 — JVM Memory Tuning

**Decision:** For 512MB Railway instance:
```
java -Xms256m -Xmx400m -XX:+UseG1GC -XX:MaxGCPauseMillis=200
```

For 1GB instance:
```
java -Xms512m -Xmx800m -XX:+UseG1GC
```

**Status:** ✅ DECIDED

---

### ADR-016 — Local Development

**Decision:** Docker Compose with `pgvector/pgvector:pg16`. Spring Boot localhost:8080. Flyway auto-runs on startup.

```yaml
# docker-compose.yml
services:
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: sat_engine_db
      POSTGRES_USER: sat_user
      POSTGRES_PASSWORD: localdev123
    ports:
      - "5432:5432"
```

**Status:** ✅ DECIDED
