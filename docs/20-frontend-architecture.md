# 20 — Frontend Architecture

---

## Overview

The frontend is a **React 19 + Vite SPA** served as static files by Spring Boot. It communicates with the backend exclusively via REST API calls. All math rendering (KaTeX), diagram rendering (SVG + Chart.js), and animation playback (custom renderer.js) happen client-side.

---

## Technology Stack

| Library | Version | Purpose |
|---------|---------|---------|
| React | 19.2.4 | UI framework |
| React Router | 7.14.0 | Client-side routing |
| Axios | 1.14.0 | HTTP client |
| KaTeX | 0.16.45 | LaTeX math rendering |
| lucide-react | 1.8.0 | Icons |
| renderer.js | custom | SVG diagrams + Chart.js + animations |
| Sentry | 8.55.0 | Error tracking |

---

## Application Structure

```mermaid
flowchart TD
    A[main.jsx\nReact root mount] --> B[App.jsx\nRoutes + AuthContext]
    B --> C[RequireAuth\nredirects to /login if no session]
    B --> D[/login\nlogin.html Spring-served]

    C --> E[AppShell\nNavbar + Sidebar layout]
    E --> F[/\nHomePage]
    E --> G[/dashboard\nDashboardPage]
    E --> H[/practice\nPracticeSetupPage]
    E --> I[/session/:id\nPracticeSession flow]
    E --> J[/session/:id/summary\nSummaryPage]
    E --> K[/session/:id/review/:idx\nReviewPage]
    E --> L[/history\nHistoryPage]
    E --> M[/skill/:key\nSkillPage]
```

---

## Page Inventory

| Page | Route | Purpose |
|------|-------|---------|
| `HomePage` | `/` | Landing / quick start |
| `DashboardPage` | `/dashboard` | Stats, domain accuracy, recent sessions |
| `PracticeSetupPage` | `/practice` | Configure session (section, domain, difficulty) |
| `PracticePage` | `/session/:id` | Live question answering with QuestionCard + FeedbackPanel |
| `SummaryPage` | `/session/:id/summary` | End-of-session results, accuracy by skill |
| `ReviewPage` | `/session/:id/review/:idx` | Per-question review after session |
| `HistoryPage` | `/history` | All past sessions list |
| `SkillPage` | `/skill/:key` | Deep-dive on one skill |
| `DashboardPage` | `/dashboard` | Progress overview |

---

## Component Hierarchy — Practice Flow

```mermaid
flowchart TD
    A[PracticePage\nuses useSession hook] --> B[AppShell\nNavbar + Sidebar]
    A --> C[ProgressBar\nX of Y questions]
    A --> D[Toolbar\nTimer + Mark button]
    A --> E[QuestionCard\nquestion prop + onSubmit]

    E --> F[MathText\nquestion stem]
    E --> G[DiagramPanel\ndiagram JSONB]
    E --> H[MCQ Buttons A-D\nor SPR text input]
    E --> I[Submit button]

    A --> J{feedback != null?}
    J -->|Yes — answered| K[FeedbackPanel\nfeedback + question]

    K --> L[Result banner\nCorrect / Wrong]
    K --> M[MathText\nexplanationShort]
    K --> N[Study This Skill button\nopens SkillDrawer]
    K --> O[Accordion Group]

    O --> P[📋 Solution\nStepNavigator + AnimationPanel]
    O --> Q[🔍 Find My Gap\nFindMyGap lazy-load]
    O --> R[💬 Why Each Option?\nChoiceExplanations]
    O --> S[💡 Core Concept\nCoreConcept]
    O --> T[⇄ Alternative Approach\nAltApproach]

    P --> U[AnimationPanel\nsynced mode]
    P --> V[StepNavigator\nPrev/Next + dots]
    V --> W[window.animGoTo\nuid + stepIndex]
    W --> U
```

---

## KaTeX Rendering — Architecture

### Two Rendering Paths

```mermaid
flowchart TD
    subgraph PATH1["Path 1 — MathText Component (primary)"]
        A[text prop passed to MathText] --> B[applyKatex function]
        B --> C[Split by regex:\n\\[...\\] display\n\\(...\\) inline\n$ ... $ smart filter]
        C --> D{Segment type}
        D -->|plain text| E[HTML escape\nconvert newlines to br]
        D -->|math segment| F[katex.renderToString\ndisplayMode based on delimiter\nthrowOnError: false]
        E --> G[Concatenate HTML string]
        F --> G
        G --> H[dangerouslySetInnerHTML\nReact injects pre-rendered HTML]
    end

    subgraph PATH2["Path 2 — useKaTeX Hook (secondary)"]
        I[ref to DOM element] --> J[useEffect fires]
        J --> K[setTimeout 30ms\nwait for paint]
        K --> L{window.renderMathInElement\nloaded?}
        L -->|Yes| M[renderMathInElement el\ndelimiters \\( \\[ only]
        L -->|No| N[Queue in window._pendingKatex\nprocess when KaTeX loads]
    end
```

### MathText — Dollar Sign Smart Filter

The `isMathContent(inner)` function prevents currency amounts like `$50` from being rendered as math:

```mermaid
flowchart LR
    A["inner = '50'"] --> B{isMathContent}
    B -->|has LaTeX command \\frac| C[IS MATH → render]
    B -->|has operator + - = <| C
    B -->|single non-numeric token like x| C
    B -->|plain number '50'| D[NOT MATH → skip\nrender as plain text $50]
```

### Supported Delimiters

| Delimiter | Mode | Path |
|-----------|------|------|
| `\[...\]` | Display (block) | Both Path 1 and Path 2 |
| `\(...\)` | Inline | Both Path 1 and Path 2 |
| `$...$` | Inline | Path 1 only (with smart filter) |

### KaTeX Options

```javascript
katex.renderToString(expr, {
  displayMode: isDisplay,   // true for \[...\], false for \(...\)
  throwOnError: false,      // broken math → escaped text fallback, never crashes
  trust: false              // no raw HTML injection
})
```

---

## Diagram Rendering — Architecture

### renderer.js Dispatch Flow

```mermaid
flowchart TD
    A[DiagramPanel receives diagramJson] --> B[Parse JSON]
    B --> C{diagramType field}

    C -->|svg_programmatic| D[window.buildSVG cfg]
    D --> E{shape field}
    E -->|triangle| F[buildTriangle\nvertices + angle markers\n+ side labels]
    E -->|circle| G[buildCircle\nradius + chord + arc\n+ sector shading]
    E -->|coordinate_plane| H[buildCoordinatePlane\naxes + grid + functions\n+ points + inequalities]
    E -->|normal_curve| I[buildNormalCurve\nGaussian + shaded regions]
    E -->|venn_diagram| J[buildVenn\noverlapping circles + labels]
    E -->|3d_shape| K[build3DShape\nprism/pyramid/cylinder\nisometric projection]
    E -->|parallel_transversal| L[buildParallelTransversal\nparallel lines + angles]
    E -->|composite| M[build each sub-shape\ncompose into one SVG]

    C -->|chartjs| N[window.renderChart canvasId cfg]
    N --> O{chartType}
    O -->|scatter| P[Chart.js Scatter\n+ optional least-squares line]
    O -->|bar| Q[Chart.js Bar]
    O -->|histogram| R[Chart.js Bar\nno gaps between bars]
    O -->|line| S[Chart.js Line]
    O -->|pie| T[Chart.js Pie/Doughnut]
    O -->|boxplot| U[Custom SVG boxplot\nQ1/Q2/Q3/whiskers]
    O -->|dotplot| V[Custom SVG dotplot\nstacked dots]
```

### Coordinate System Transformation

```mermaid
flowchart LR
    A["Math space\nOrigin: center\nY: up\nCartesian standard"] --> B["transform=translate\ndx dy"]
    B --> C["SVG space\nOrigin: top-left\nY: down\npixels"]
```

All geometry shapes use this transform. Math coordinates passed in JSON are converted to SVG pixel space automatically by `autoCenterTransform()`.

### SVG Utility Functions (renderer.js)

| Function | Purpose |
|----------|---------|
| `svgWrap(w, h, inner)` | Creates `<svg viewBox="0 0 w h">` wrapper |
| `autoCenterTransform(points, w, h)` | Computes translate to center shape in canvas |
| `svgText(x, y, text, opts)` | Creates `<text>` with styling |
| `arrowHead(x1,y1,x2,y2,color)` | Polygon arrowhead at line end |
| `rightAngleSquare(vx,vy,ax,ay,bx,by)` | Right-angle square marker |
| `clampLabel(x, y, w, h, padding)` | Keeps label inside canvas bounds |
| `midpoint(p1, p2)` | Average of two [x,y] points |
| `distance(p1, p2)` | Euclidean distance |

### Chart.js Cleanup Rule

**Critical:** Chart.js cannot reuse a canvas that already has a chart instance. Before rendering a new chart:

```javascript
// Always destroy existing instance before re-render
const existing = Chart.getChart(canvasEl)
if (existing) existing.destroy()
// Then create new instance
new Chart(canvasEl, config)
```

This is handled inside `renderChart()` in renderer.js.

---

## Animation System — Architecture

### Full Animation Flow

```mermaid
sequenceDiagram
    participant Student
    participant FeedbackPanel
    participant AnimationPanel
    participant renderer.js
    participant StepNavigator

    Student->>FeedbackPanel: Submits wrong answer
    FeedbackPanel->>FeedbackPanel: solution accordion auto-opens
    FeedbackPanel->>AnimationPanel: mount with animationJson + synced=true
    AnimationPanel->>renderer.js: window.renderAnimation(cfg, el, {synced:true})
    renderer.js->>renderer.js: generate uid = 'ap_xxxxxxx'
    renderer.js->>renderer.js: _animBBox — compute tight bounding box
    renderer.js->>renderer.js: render SVG container
    renderer.js->>renderer.js: _animRenderFrame(uid, 0, false) — show frame 0
    renderer.js->>AnimationPanel: return uid
    AnimationPanel->>FeedbackPanel: onReady(uid)
    FeedbackPanel->>StepNavigator: pass animUid + animFrames

    Student->>StepNavigator: clicks Next
    StepNavigator->>StepNavigator: setCurrent(idx + 1)
    StepNavigator->>renderer.js: window.animGoTo(uid, idx+1)
    renderer.js->>renderer.js: _animRenderFrame(uid, idx+1, animate=true)
    renderer.js->>renderer.js: detect new elements\nei >= prevFrame.elements.length
    renderer.js->>renderer.js: apply .anim-draw or .anim-fade class
    renderer.js->>renderer.js: stagger delay: newElIdx × 75ms
    renderer.js->>Student: elements animate in
```

### Frame Rendering — New Element Detection

```mermaid
flowchart LR
    A[Frame N requested] --> B[Get frame N elements\nlength = 5]
    B --> C[Get frame N-1 elements\nlength = 3]
    C --> D{For each element i}
    D -->|i < 3 prev count| E[Existing element\nNo animation\nRender static]
    D -->|i >= 3 new| F[New element\nApply animation]
    F --> G{element type}
    G -->|polygon, line, circle, arc, rect| H[.anim-draw\nstroke-dashoffset 3000→0\n0.5s cubic-bezier]
    G -->|dot, sector, right_angle, text, side_label| I[.anim-fade\nopacity 0→1 + translateY 3px→0\n0.35s cubic-bezier]
    H --> J[animationDelay = newElIdx × 75ms]
    I --> J
```

### Animation CSS Keyframes

```mermaid
block-beta
    columns 2

    A["anim-draw\n(lines, polygons, circles)"]:1
    B["anim-fade\n(fills, dots, text)"]:1

    C["stroke-dasharray: 3000\nstroke-dashoffset: 3000 → 0\nDuration: 0.5s\nEasing: cubic-bezier(0.22,0.61,0.36,1)"]:1
    D["opacity: 0 → 1\ntransform: translateY(3px → 0)\nDuration: 0.35s\nEasing: cubic-bezier(0.22,0.61,0.36,1)"]:1
```

### Synced vs Standalone Mode

| Mode | Controls | KaTeX overlays | Use case |
|------|----------|----------------|----------|
| `synced=true` | None (hidden) | Skipped (formula in step text) | FeedbackPanel — synced with StepNavigator |
| `synced=false` (default) | Prev/Next + dots built-in | Shown as positioned overlays | Standalone animation player |

### Global Animation Registry

```javascript
window._animPlayers = {
  'ap_abc123': {
    cfg: { width, height, frames },
    currentIdx: 2,
    svgEl: <SVGElement>,
    ovEl: <div>,     // overlay container for katex labels
    synced: true
  }
}
```

`window.animGoTo(uid, idx)` looks up the player by uid and calls `_animRenderFrame()`. This global registry is how the decoupled StepNavigator controls the AnimationPanel without prop drilling.

---

## FeedbackPanel — Accordion Structure

```mermaid
flowchart TD
    A[FeedbackPanel mounts] --> B[Result Banner\nGreen ✓ or Red ✗]
    B --> C[Short explanation\nMathText]
    C --> D[Study This Skill button\nopens SkillDrawer overlay]
    D --> E[Accordion Group]

    E --> F{📋 Solution}
    F -->|Auto-opens| G{hasAnimation?}
    G -->|Yes| H[Split pane:\nAnimationPanel left\nStepNavigator right]
    G -->|No| I[StepNavigator only\nfull width]

    E --> J{🔍 Find My Gap}
    J -->|Wrong answers only\nLazy loads on open| K[API: POST /api/gap/analyze\nquestionId + studentAnswer]
    K --> L[GapCard pills + active card\ntrigger + title + body + example + takeaway]

    E --> M{💬 Why Each Option?}
    M -->|MCQ only\nchoiceExplanations exists| N[Letters A-D with\ncorrect green / wrong red\nMathText per choice]

    E --> O{💡 Core Concept}
    O --> P[title + summary + keyFormula\nMathText rendering]

    E --> Q{⇄ Alternative Approach}
    Q --> R[title + steps[]\nSame step format as Solution]
```

### Keyboard Navigation

```mermaid
flowchart LR
    A[keydown event on document] --> B{key}
    B -->|Enter or Space| C{Active element\nis input or textarea?}
    C -->|Yes| D[Ignore — student typing]
    C -->|No| E[Call onNext callback\nAdvance to next question]
```

---

## SkillDrawer — Skill Content Display

```mermaid
flowchart TD
    A[Student clicks 📚 Study This Skill] --> B[SkillDrawer slides in]
    B --> C[GET /api/skill/:skillKey/content]
    C --> D[Spring returns skill-content JSON\nfrom classpath resource]
    D --> E[SkillDrawer renders sections]

    E --> F[Overview text\nMathText]
    E --> G[Concept Diagram\nRaw SVG string injected]
    E --> H[Key Formulas grid\nMathText per formula]
    E --> I[Quick Example\nProblem + steps with math]
    E --> J[Common Mistakes\nmistake/fix pairs]
    E --> K[Quick Tip\ncallout box]
```

### skill-content JSON Schema (existing format)

```json
{
  "skillKey": "special_right_triangles",
  "domain": "geometry_trigonometry",
  "label": "Special Right Triangles",
  "overview": "Text description...",

  "conceptDiagram": {
    "caption": "30-60-90 and 45-45-90 side ratios",
    "svg": "<svg xmlns='...'> raw SVG string </svg>"
  },

  "keyFormulas": [
    {
      "name": "45-45-90 sides",
      "latex": "1 : 1 : \\sqrt{2} \\quad (\\text{hyp} = \\text{leg} \\times \\sqrt{2})"
    }
  ],

  "workedExamples": [
    {
      "problem": "The hypotenuse is 10. Find both legs.",
      "steps": [
        {
          "title": "Apply the 1:√3:2 ratio",
          "content": "Scale factor = 10/2 = 5",
          "math": "\\text{short leg} = 5, \\text{long leg} = 5\\sqrt{3}"
        }
      ]
    }
  ],

  "commonMistakes": [
    {
      "mistake": "Mixing up which side is opposite 30° vs 60°",
      "fix": "Short leg is ALWAYS opposite the smallest angle (30°)"
    }
  ],

  "quickTip": "Find the scale factor first by matching hypotenuse to 2x."
}
```

**44 skill-content files exist** in `src/main/resources/skill-content/`. Served via `SkillContentController` at `GET /api/skill/{skillKey}/content`. Security: only `[a-z0-9_]{1,60}` keys accepted — path traversal protection.

---

## API Communication Layer

```mermaid
flowchart LR
    A[React component] --> B[api/client.js\nAxios instance]
    B --> C[baseURL: /api\nwithCredentials: true]
    C --> D[Spring Boot\nREST endpoints]

    B --> E{401 response}
    E --> F[window.location = /login\nauto-redirect]
```

### Key API Endpoints (current)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/dashboard` | Dashboard stats + domain accuracy |
| POST | `/api/sessions` | Create new session |
| GET | `/api/sessions/:id/next` | Get next question in session |
| POST | `/api/sessions/:id/answers` | Submit answer + get feedback |
| GET | `/api/sessions/:id/answers` | Get all answers for session (review) |
| GET | `/api/sessions/:id` | Get session details |
| POST | `/api/gap/analyze` | Find My Gap — Claude gap analysis |
| GET | `/api/skill/:key/content` | Skill content JSON for SkillDrawer |

### Planned API Endpoints (adaptive engine)

| Method | Path | Issue | Purpose |
|--------|------|-------|---------|
| POST | `/api/sessions/diagnostic` | #65 | Start two-stage diagnostic |
| GET | `/api/skill-map` | #66 | Get skill map with confidence levels |
| POST | `/api/sessions/drill` | #69 | Start drill with prereq check |
| GET | `/api/sessions/difficulty` | #70 | Rolling 4Q difficulty adjustment |
| POST | `/api/sessions/foundations` | #71 | Start foundations micro-lesson |

---

## Authentication Flow

```mermaid
sequenceDiagram
    participant Browser
    participant Spring
    participant Google

    Browser->>Spring: GET /login
    Spring->>Browser: login.html (static)
    Browser->>Spring: Click "Sign in with Google"
    Spring->>Google: OAuth2 redirect
    Google->>Spring: Callback with auth code
    Spring->>Google: Exchange for user info
    Spring->>Spring: OAuth2SuccessHandler\nCreate or update user in DB\nSet HttpSession
    Spring->>Browser: Redirect to /dashboard
    Browser->>Spring: All API calls with session cookie
    Spring->>Spring: Extract userId from HttpSession
```

**Dev login** (`DevLoginController`) bypasses OAuth for local development.

---

## DashboardPage — Data Flow

```mermaid
flowchart TD
    A[DashboardPage mounts] --> B[GET /api/dashboard]
    B --> C[DashboardResponse POJO]

    C --> D[Stat Cards row]
    D --> D1[Sessions completed]
    D --> D2[Questions answered]
    D --> D3[Accuracy % + trend badge]
    D --> D4[Avg time per question]

    C --> E[Domain Accuracy bars]
    E --> E1[For each domain:\nprogress bar + accuracy %\nGreen ≥70% Yellow 50-69% Red <50%]

    C --> F[CTA Card]
    F --> F1{Any domain < 70%?}
    F1 -->|Yes| F2[Practice your weakest area\ndomain name + accuracy]
    F1 -->|No| F3[Practice Exams\ngeneric prompt]

    C --> G[Recent Sessions table]
    G --> G1[Section + date + count + accuracy pill\nReview link → /session/id/summary]
```

### Trend Badge Logic

```javascript
// Compare second half of trend to first half
const mid = Math.floor(trend.length / 2)
const firstHalf = trend.slice(0, mid).reduce((a,b)=>a+b,0) / mid
const secondHalf = trend.slice(mid).reduce((a,b)=>a+b,0) / (trend.length - mid)
const delta = secondHalf - firstHalf

if (delta > 2)  return '↑ Improving'
if (delta < -2) return '↓ Declining'
return '→ Steady'
```

---

## SummaryPage — Dual Mode

```mermaid
flowchart TD
    A[SummaryPage mounts] --> B{router state\nhas history?}

    B -->|Yes — direct from PracticePage| C[Use in-memory history\nNo API call needed]
    B -->|No — loaded by URL| D[GET /api/sessions/:id\nGET /api/sessions/:id/answers]

    C --> E[Compute metrics]
    D --> E

    E --> F[Score circle\nlarge % display]
    E --> G[Correct count / total]
    E --> H[Total time + avg time per Q]
    E --> I[Performance by skill\ngrouped + sorted by accuracy]
    E --> J{API mode?}
    J -->|Yes| K[Question grid\nnumbered circles\nGreen=correct Red=wrong\nClick → review that question]
    J -->|No| L[No grid\njust skill breakdown]
```

---

## React Hooks

| Hook | File | Purpose |
|------|------|---------|
| `useSession` | `hooks/useSession.js` | Session lifecycle (create, next Q, submit) |
| `usePracticeSession` | `hooks/usePracticeSession.js` | Practice page state machine |
| `useTimer` | `hooks/useTimer.js` | Per-question timer (counts up, freezes on submit) |
| `useKaTeX` | `hooks/useKaTeX.js` | Auto-render KaTeX in existing DOM elements |
| `useAuth` (context) | `context/AuthContext.jsx` | Current user + auth state |

---

## Build & Deployment

```mermaid
flowchart LR
    A[npm run build\nin frontend/] --> B[Vite builds\nbundled JS + CSS]
    B --> C[Output to\nsrc/main/resources/static/app/]
    C --> D[mvn package\nSpring Boot packages\nstatic files into JAR]
    D --> E[sat-engine.jar\n83.4 MB]
    E --> F[Deploy to Railway\nJava runtime]
    F --> G[SpaRoutingController\nserves index.html for\nall non-API routes]
```

**Dev mode:** `npm run dev` in `frontend/` runs Vite dev server on port 5173 with proxy to Spring Boot on port 8080.

**Skip frontend build** (CI/Docker): `mvn package -Dskip.frontend=true`

---

## Error Handling

```mermaid
flowchart LR
    A[React component error] --> B[ErrorBoundary\nwraps all pages]
    B --> C[Sentry.captureException\nlogged to Sentry dashboard]
    B --> D[Fallback UI shown\nnot blank white screen]

    E[API 401] --> F[Axios interceptor\nredirect to /login]
    G[API 4xx/5xx] --> H[GlobalExceptionHandler\nSpring returns structured error JSON]
    H --> I[Component shows\nerror message to student]
```
