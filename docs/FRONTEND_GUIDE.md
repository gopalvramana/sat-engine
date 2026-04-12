# Aptify — Frontend Code Guide
> React + Vite. Every file explained. Every pattern named. Written so you can navigate the codebase confidently.

---

## How the Frontend Works (30-second primer)

The frontend is a React Single Page Application (SPA) built with Vite. In development, Vite runs on port 5173 and proxies `/api` requests to Spring Boot on port 8080. In production, Spring Boot serves the built React app as static files from `/app/`.

React renders components (functions that return HTML-like JSX). When data changes, React re-renders only the components that depend on it. State is data that lives inside a component and causes a re-render when it changes.

---

## Project Structure

```
frontend/src/
│
├── main.jsx                    ← entry point: mounts React, sets up Router + Auth
├── App.jsx                     ← defines all routes
├── api/
│   └── client.js               ← ALL API calls go through here
│
├── context/
│   └── AuthContext.jsx         ← logged-in user available everywhere
│
├── hooks/
│   ├── usePracticeSession.js   ← brain of the practice screen (state machine)
│   ├── useTimer.js             ← per-question timer
│   └── useKaTeX.js             ← LaTeX math rendering
│
├── pages/                      ← full-screen route components
│   ├── DashboardPage.jsx
│   ├── PracticeSetupPage.jsx
│   ├── PracticePage.jsx
│   └── SummaryPage.jsx
│
└── components/                 ← reusable UI pieces
    ├── AppShell/
    ├── Sidebar/
    ├── QuestionCard/
    ├── FeedbackPanel/
    ├── ExplanationSteps/
    ├── AnimationPanel/
    ├── ChoiceExplanations/
    ├── CoreConcept/
    ├── FindMyGap/
    ├── DiagramPanel/
    ├── MathText/
    ├── ProgressBar/
    └── Toolbar/
```

---

## Pattern 1: Entry Point and Router Setup

**`main.jsx`** — mounts the React app with all global providers:
```jsx
createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter basename="/app">   {/* all routes relative to /app */}
      <AuthProvider>                  {/* makes user available everywhere */}
        <App />
      </AuthProvider>
    </BrowserRouter>
  </StrictMode>
)
```

`basename="/app"` means the app lives at `localhost:8080/app/`. The path `/` in React Router means `localhost:8080/app/`. This matches how Spring Boot serves the frontend.

**`App.jsx`** — the route table. Two groups: shell-wrapped and full-screen:
```jsx
export default function App() {
  return (
    <Routes>
      {/* Shell-wrapped: sidebar is visible */}
      <Route element={<AppShell />}>
        <Route index element={<DashboardPage />} />      {/* /app/ */}
        <Route path="practice" element={<PracticeSetupPage />} />  {/* /app/practice */}
      </Route>

      {/* Full-screen: no sidebar, focused practice mode */}
      <Route path="session/:sessionId" element={<PracticePage />} />
      <Route path="session/:sessionId/summary" element={<SummaryPage />} />
    </Routes>
  )
}
```

The `element={<AppShell />}` trick is the **Layout Route pattern** — AppShell renders as a wrapper, and its child routes render inside it via `<Outlet />`.

---

## Pattern 2: Context — Sharing State Globally

React Context solves "I need this data in many components but don't want to pass it as props through every level."

**`AuthContext.jsx`** — the logged-in user, available in any component:
```jsx
const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(undefined)
  // undefined = still loading, null = not logged in, object = logged in

  useEffect(() => {
    // On every page load, check if the user is logged in
    fetch('/api/auth/me', { credentials: 'include' })
      .then(r => r.ok ? r.json() : null)
      .then(data => setUser(data))
      .catch(() => setUser(null))
  }, [])   // empty array = run once on mount

  return (
    <AuthContext.Provider value={{ user, setUser, logout }}>
      {children}   {/* every component inside AuthProvider can read this */}
    </AuthContext.Provider>
  )
}

// Any component calls this to get the user
export function useAuth() {
  return useContext(AuthContext)
}
```

**Using it in any component:**
```jsx
function Sidebar() {
  const { user, logout } = useAuth()
  return <div>{user?.name}</div>
}
```

**The three user states:**
```
user === undefined  → still loading (show spinner)
user === null       → not logged in (show sign in button)
user === { id, email, name, picture } → logged in
```

---

## Pattern 3: Custom Hooks — Extracting Logic from Components

A custom hook is a function that starts with `use` and can call other hooks. It keeps components clean by moving complex logic out.

### `usePracticeSession.js` — The Most Important Hook

This is the brain of the entire practice experience. It manages a 3-phase state machine:

```
loading → question → feedback → loading → question → ...
                                              ↓ (no more questions)
                                    navigate to /summary
```

**Key concepts used inside this hook:**

**`useState` — reactive data that causes re-renders:**
```jsx
const [livePhase, setLivePhase] = useState('loading')
// When setLivePhase('question') is called, the component re-renders
```

**`useRef` — data that persists across renders WITHOUT causing re-renders:**
```jsx
const historyRef = useRef([])
// historyRef.current is always the latest value
// Used for history because loadNext() is a callback that would otherwise
// "see" a stale copy of history from when it was created (stale closure problem)
```

**Why both `historyRef` and `history` state?**
```jsx
const historyRef = useRef([])   // ← used INSIDE callbacks (always fresh)
const [history, setHistory] = useState([])  // ← used in JSX (triggers re-renders)

function appendHistory(item) {
  const next = [...historyRef.current, item]
  historyRef.current = next  // ← update ref immediately (no re-render)
  setHistory(next)            // ← update state (triggers re-render)
}
```
This solves the **stale closure** problem: `loadNext` is created with `useCallback` and captures variables at creation time. If it captured `history` directly, it would always see the empty initial value. By reading `historyRef.current`, it always gets the current value.

**`useCallback` — stable function reference:**
```jsx
const loadNext = useCallback(async () => {
  // this function is only recreated when [sessionId, navigate] change
  // without useCallback, a new function object would be created every render
}, [sessionId, navigate])
```

**The full state machine:**
```jsx
// Phase: loading
setLivePhase('loading')
const q = await api.getNextQuestion(sessionId)

if (!q) {
  // Session exhausted → navigate to summary, pass history via router state
  navigate(`/session/${sessionId}/summary`, {
    state: { sessionInfo: info, history: historyRef.current },
    replace: true,
  })
} else {
  setLiveQuestion(q)
  setLivePhase('question')  // show question to student
  timer.start()
}

// Phase: question → feedback (after submit)
const fb = await api.submitAnswer(sessionId, liveQuestion.id, answer)
appendHistory({ question: liveQuestion, feedback: fb, studentAnswer: answer })
setLiveFeedback(fb)
setLivePhase('feedback')    // show feedback panel

// Review mode: student clicks Back
// reviewIndex !== null → show past question from history array
// isReviewing derived value: const isReviewing = reviewIndex !== null
```

---

## Pattern 4: Pages — Route-Level Components

Pages are components that correspond to a URL. They fetch their own data and compose smaller components.

### `DashboardPage.jsx`
```jsx
export default function DashboardPage() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/api/dashboard')
      .then(r => r.ok ? r.json() : null)
      .then(json => { setData(json); setLoading(false) })
  }, [])  // fetch once on mount

  // Helper: show '…' while loading, '—' if no data, value otherwise
  const fmt = (val, suffix = '') =>
    loading ? '…' : val == null ? '—' : `${val}${suffix}`

  return (
    <div>
      <span>{fmt(data?.accuracyPct, '%')}</span>
      {/* data?.accuracyPct is optional chaining: safe if data is null */}
    </div>
  )
}
```

### `PracticeSetupPage.jsx`
This page builds a session configuration before creating one. Key patterns:

**Controlled component with stepper:**
```jsx
const [bandCounts, setBandCounts] = useState({
  algebra: { easy: 0, medium: 0, hard: 0 },
  // ...
})

function adjust(domain, band, delta) {
  setBandCounts(prev => {
    const current = prev[domain]?.[band] ?? 0
    const avail   = counts[domain]?.[band] ?? 0  // can't exceed available
    const next    = Math.max(0, Math.min(avail, current + delta))  // clamp 0 to avail
    return { ...prev, [domain]: { ...prev[domain], [band]: next } }  // immutable update
  })
}
```

**Immutable state updates** — React state must never be mutated directly. Always return a new object:
```jsx
// WRONG — mutates existing state
prev[domain][band] = next

// RIGHT — creates new objects at every level
return { ...prev, [domain]: { ...prev[domain], [band]: next } }
```

### `PracticePage.jsx`
The practice screen. Uses `usePracticeSession` hook and renders conditionally by phase:
```jsx
const { sessionId } = useParams()  // reads :sessionId from URL
const { phase, question, feedback, ... } = usePracticeSession(sessionId)

useEffect(() => { loadNext() }, [])  // load first question on mount

return (
  <div>
    {phase === 'loading' && <Spinner />}
    {phase === 'question' && <QuestionCard ... />}
    {phase === 'feedback' && <FeedbackPanel ... />}
  </div>
)
```

### `SummaryPage.jsx`
Reads data from **React Router state** (no API call needed):
```jsx
const location = useLocation()
const history = location.state?.history ?? []
const sessionInfo = location.state?.sessionInfo ?? null
```
`usePracticeSession.loadNext()` navigates here with `navigate('/summary', { state: { history, sessionInfo } })`. The data travels in memory via the router, not the URL. This is the **router state pattern** — used for passing data between pages without an API call.

---

## Pattern 5: Component Architecture

### AppShell — Layout Route Pattern
```jsx
// AppShell.jsx
export default function AppShell() {
  return (
    <div className={styles.shell}>
      <Sidebar />
      <main className={styles.main}>
        <Outlet />   {/* ← child route renders here */}
      </main>
    </div>
  )
}
```
`<Outlet />` is where React Router renders the matched child route. When the URL is `/app/practice`, the `<PracticeSetupPage>` renders inside AppShell's `<Outlet />`.

### Sidebar — NavLink Active State Pattern
```jsx
const NAV_ITEMS = [
  { path: '/',         label: 'Dashboard',  Icon: LayoutDashboard, exact: true },
  { path: '/practice', label: 'Practice',   Icon: PenLine },
  { path: null,        label: 'Coming Soon', Icon: BookMarked, soon: true },
]

{NAV_ITEMS.map(item => (
  item.soon ? (
    <div className={styles.itemDisabled}>...</div>
  ) : (
    <NavLink
      to={item.path}
      end={item.exact}   // "end" means only active on exact match (important for '/')
      className={({ isActive }) =>
        `${styles.item} ${isActive ? styles.itemActive : ''}`
      }
    >
      <item.Icon size={16} />   {/* Icon is a Lucide React component stored in data */}
      <span>{item.label}</span>
    </NavLink>
  )
))}
```

**Data-driven nav items** — nav is defined as an array of objects, not hardcoded JSX. Adding a new nav item = adding one line to the array.

**`item.Icon` as a component** — storing the component itself (not JSX) in the data array lets you render it like `<item.Icon size={16} />`.

### FeedbackPanel — Compound Component Pattern

FeedbackPanel has several sub-components defined in the same file:
```jsx
// All defined in FeedbackPanel.jsx but not exported — internal only
function ChoiceWhyBody({ expl, options, correctAnswer, studentAnswer }) { ... }
function CoreConceptBody({ cc }) { ... }
function AltApproachBody({ alt }) { ... }
function StepNavigator({ steps, animUid, animFrames }) { ... }
function AccordionItem({ icon, label, children }) { ... }

// The main exported component composes them
export default function FeedbackPanel({ feedback, question, ... }) {
  return (
    <div>
      <AccordionItem icon="📋" label="Solution" defaultOpen>
        <StepNavigator steps={steps} />
      </AccordionItem>
      {hasChoiceEx && (
        <AccordionItem icon="💬" label="Why each option?">
          <ChoiceWhyBody ... />
        </AccordionItem>
      )}
    </div>
  )
}
```

**Lazy loading with accordion:**
```jsx
const [gapTriggered, setGapTriggered] = useState(false)

<AccordionItem
  icon="🔍"
  label="Find My Gap"
  onOpen={() => setGapTriggered(true)}   // ← only fires when student opens it
>
  {gapTriggered
    ? <FindMyGap questionId={question.id} studentAnswer={studentAnswer} />
    : <p>Open to identify the gap...</p>
  }
</AccordionItem>
```
`FindMyGap` makes a live Claude API call. Wrapping it in `gapTriggered` means the API call only happens when the student actually opens that accordion — not on every question load.

---

## Pattern 6: API Client — Centralized Fetch

All API calls live in `api/client.js`. No component ever calls `fetch` directly except `DashboardPage` (which we should migrate) and `AuthContext`.

```javascript
// The base request function handles all HTTP methods
async function request(method, url, body) {
  const res = await fetch(url, {
    method,
    headers: body ? { 'Content-Type': 'application/json' } : {},
    body: body ? JSON.stringify(body) : undefined,
  })
  if (res.status === 204) return null      // No Content → null
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`${method} ${url} → ${res.status}: ${text}`)
  }
  return res.json()
}

// Every API call is a named function
export function createSession(sessionType, section, domainBandCounts) {
  return request('POST', '/api/sessions', { sessionType, section, domainBandCounts })
}

export function getNextQuestion(id) {
  return request('GET', `/api/sessions/${id}/next`)
}
```

**Why centralize?** If the API URL changes, you change it in one place. If you need to add an auth header, you add it in `request()` and it applies everywhere. Components don't need to know about HTTP — they just call named functions.

---

## Pattern 7: CSS Modules — Scoped Styles

Every component has its own `.module.css` file. Class names are scoped to that component — no global name conflicts.

```jsx
// In QuestionCard.jsx
import styles from './QuestionCard.module.css'

// Usage — 'card' only applies to this component's CSS
<div className={styles.card}>

// Conditional classes — combining module classes
<div className={`${styles.item} ${isActive ? styles.itemActive : ''}`}>
```

```css
/* QuestionCard.module.css */
.card {
  background: #fff;
  border-radius: 12px;
}

/* At build time, this becomes .QuestionCard_card__abc123 — guaranteed unique */
```

---

## Pattern 8: Conditional Rendering

React renders JSX conditionally using JavaScript expressions:

```jsx
// Short-circuit: only renders FeedbackPanel if phase is 'feedback' AND feedback exists
{phase === 'feedback' && feedback && <FeedbackPanel ... />}

// Ternary: one or the other
{loading ? <Spinner /> : <DataTable data={data} />}

// Optional chaining: safe access on possibly-null objects
{user?.picture && <img src={user.picture} />}

// Nullish coalescing: fallback value if null/undefined
const name = user?.name ?? 'Student'
```

---

## Pattern 9: useEffect Patterns

`useEffect` runs side effects (API calls, subscriptions) after render. The dependency array controls when it re-runs:

```jsx
// Run once on mount (empty array = no dependencies = never re-runs)
useEffect(() => {
  fetchDashboardData()
}, [])

// Run when sessionId changes (e.g. navigating to a different session)
useEffect(() => {
  fetchSessionData(sessionId)
}, [sessionId])

// Run every render (no array) — rarely correct, usually a bug
useEffect(() => {
  doSomething()
})
```

---

## Component Map — What Each Component Does

| Component | File | Purpose |
|-----------|------|---------|
| `AppShell` | `AppShell/AppShell.jsx` | Layout wrapper: sidebar + `<Outlet>` for child routes |
| `Sidebar` | `Sidebar/Sidebar.jsx` | Left nav: logo, nav items (NavLink), user widget |
| `QuestionCard` | `QuestionCard/QuestionCard.jsx` | Renders question stem + MCQ choices or SPR input. Calls `onSubmit` with student's answer |
| `FeedbackPanel` | `FeedbackPanel/FeedbackPanel.jsx` | Post-answer panel: result banner + accordion group (Solution, Why each option, Core Concept, Alt Approach, Find My Gap) |
| `ExplanationSteps` | `ExplanationSteps/ExplanationSteps.jsx` | Step-by-step solution renderer (used inside FeedbackPanel) |
| `AnimationPanel` | `AnimationPanel/AnimationPanel.jsx` | Plays SVG animation frames for geometry questions. Syncs with StepNavigator via `window.animGoTo` |
| `DiagramPanel` | `DiagramPanel/DiagramPanel.jsx` | Renders static SVG or Chart.js diagrams from question's `diagramJson` |
| `MathText` | `MathText/MathText.jsx` | Renders LaTeX math using KaTeX. Wraps any text that might contain `\(...\)` or `\[...\]` |
| `FindMyGap` | `FindMyGap/FindMyGap.jsx` | Makes live POST to `/api/gaps/analyze`. Only mounts when student opens the accordion |
| `ChoiceExplanations` | `ChoiceExplanations/ChoiceExplanations.jsx` | Shows why each MCQ option is right or wrong |
| `CoreConcept` | `CoreConcept/CoreConcept.jsx` | Shows the underlying math concept: title, summary, key formula |
| `ProgressBar` | `ProgressBar/ProgressBar.jsx` | Top bar on practice screen: Q current/total, back button, end session button |
| `Toolbar` | `Toolbar/Toolbar.jsx` | Calculator toggle (only shown when `calculatorOk = true`) |
| `SkillDrawer` | `SkillDrawer/SkillDrawer.jsx` | Slide-in drawer showing study content for a skill. Opens when student clicks "Study this skill" |

---

## Data Flow — How a Question Gets to the Screen

```
1. PracticePage mounts
   └─ useEffect calls loadNext()

2. loadNext() → api.getNextQuestion(sessionId) → GET /api/sessions/{id}/next
   └─ Spring Boot → SessionService → QuestionRepository → PostgreSQL
   └─ Returns QuestionResponse (no correct answer)

3. loadNext() calls setLiveQuestion(q) and setLivePhase('question')
   └─ React re-renders PracticePage
   └─ QuestionCard renders with the question

4. Student clicks an answer
   └─ QuestionCard calls onSubmit(answer)
   └─ PracticePage passes to usePracticeSession.submitAnswer(answer)

5. submitAnswer() → api.submitAnswer(sessionId, questionId, answer) → POST /api/sessions/{id}/answers
   └─ Spring Boot → SessionService → checks answer → saves SessionAnswer row
   └─ Returns AnswerFeedback { isCorrect, correctAnswer, explanationShort, explanationSteps }

6. submitAnswer() calls setLiveFeedback(fb) and setLivePhase('feedback')
   └─ React re-renders PracticePage
   └─ FeedbackPanel renders with the feedback
```

---

## Quick Reference — "Where do I look if X is broken?"

| Symptom | Look here |
|---------|-----------|
| Blank screen on load | `main.jsx` → `App.jsx` routes → browser console errors |
| Not logged in / user is null | `AuthContext.jsx` → check Network tab for `/api/auth/me` |
| Practice not starting | `PracticeSetupPage.jsx` → `handleStart()` → `api/client.js createSession()` |
| Question not loading | `usePracticeSession.js` → `loadNext()` → Network tab for `/api/sessions/{id}/next` |
| Answer not submitting | `usePracticeSession.js` → `submitAnswer()` → Network tab |
| Dashboard showing `—` | `DashboardPage.jsx` → check Network tab for `/api/dashboard` |
| Math not rendering | `MathText/MathText.jsx` → check KaTeX is loaded |
| Animation not playing | `AnimationPanel/AnimationPanel.jsx` |
| Sidebar active state wrong | `Sidebar/Sidebar.jsx` → check NavLink `end` prop |
| Styles not applying | Check you imported `styles from './Component.module.css'` and used `className={styles.name}` |

---

## Patterns Summary Table

| Pattern | Where used | What it solves |
|---------|-----------|---------------|
| Context + Provider | `AuthContext.jsx` | Global state without prop drilling |
| Custom Hook | `usePracticeSession.js`, `useTimer.js` | Extract complex stateful logic from components |
| Layout Route + Outlet | `AppShell.jsx` + `App.jsx` | Shared layout (sidebar) across multiple routes |
| Router State | `SummaryPage.jsx` | Pass data between pages without an API call |
| Data-driven UI | `Sidebar.jsx` NAV_ITEMS | Add UI elements by editing an array, not JSX |
| Lazy loading | `FeedbackPanel.jsx` FindMyGap | Defer expensive operations until needed |
| Centralized API client | `api/client.js` | Single place for all API calls |
| CSS Modules | Every component | Scoped styles, no class name conflicts |
| useRef for callbacks | `usePracticeSession.js` historyRef | Avoid stale closure in async callbacks |
| Immutable state updates | `PracticeSetupPage.jsx` | React requires new objects, not mutations |
| Optional chaining (?.) | Throughout | Safe access on possibly-null values |
