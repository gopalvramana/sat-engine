# 10 — What Has Been Built and Validated

> Everything in this list is proven working. These are not assumptions.

---

## Validated in Browser

### ✅ KaTeX Math Rendering
**File:** `math-test.html`  
**What was tested:** All SAT, JEE, AP, Physics, and Chemistry math symbols.

Confirmed working:
- Plain text (baseline)
- Inline math `\( ... \)`
- Display math `\[ ... \]`
- Fractions `\frac{}{}`
- Square roots `\sqrt{}`
- Exponents and subscripts `x^{2}`, `H_{2}O`
- Greek letters `\theta`, `\pi`, `\alpha`, `\beta`
- Trigonometry `\sin\theta`, `\cos\theta`
- Complex expressions combining multiple operators
- Answer choices with inline LaTeX
- Explanation re-rendering after Check Answer click

---

### ✅ SVG Programmatic Diagram Rendering
**File:** `svg-test.html`  
**What was tested:** 8 shape types, all from JSON config objects.

Confirmed working:
- Right triangle (vertices, side labels, right angle marker, angle labels, highlight)
- Isoceles triangle (apex up, angle labels α, β)
- Circle (center point, radius line, points on circumference, chord)
- Rectangle (side labels, diagonal, right angle marker)
- Number line (open/closed points, shading between values)
- Coordinate plane (axes with arrows, grid lines, plotted points, segments)
- Parallel lines with transversal (angle labels at both intersections)
- Right triangle with altitude (altitude line, foot point, all labels)

**Key validation:** Diagrams drawn from JSON config — not hardcoded SVG. This is the architecture used in production.

---

### ✅ Chart.js Graph Rendering
**File:** `chartjs-test.html`  
**What was tested:** 8 chart types, all from JSON config objects.

Confirmed working:
- Line chart (single line, straight, grid, axis labels)
- Two-line system of equations (intersection point labeled)
- Scatter plot with line of best fit (dashed, different color)
- Bar chart (individual bar colors, category labels)
- Histogram (no gap between bars, frequency distribution)
- Line chart with categories (time series, two datasets, legend)
- Box plot (simulated with floating bars, whiskers)
- Dot plot (stacked dots, frequency counting)

---

### ✅ Combined Rendering — All Three Together
**File:** `combined-test.html`  
**What was tested:** 5 complete question cards with real SAT questions.

Confirmed working:
- KaTeX in question stems
- KaTeX in answer choices
- KaTeX in explanations (after Check Answer)
- SVG diagram (right triangle) above question
- SVG diagram (circle) above question
- Chart.js (line graph) above question
- Chart.js (scatter plot) above question
- R&W passage in styled box
- Check Answer button (correct/incorrect feedback)
- All three renderers coexist without interference

**Note:** Required `CLAUDE_CODE_MAX_OUTPUT_TOKENS=100000` to generate this file.

---

### ✅ Dynamic Data-Driven Rendering
**File:** `api-test.html`  
**What was tested:** Questions loaded from external JSON file (not hardcoded).

Confirmed working:
- `fetch()` loads questions.json array
- Cards built dynamically from fetched data
- KaTeX renders on dynamically-built DOM
- SVG draws on dynamically-built containers
- Chart.js draws on dynamically-built canvases
- Check Answer works on dynamic cards

**Key validation:** This is exactly how Thymeleaf + Spring Boot will work — the rendering pipeline is agnostic to whether data comes from a JSON file or a PostgreSQL database.

---

### ✅ AI Learning Panel — Live API Calls
**Validated in:** Browser screenshot (confirmed working)

Confirmed working:
- Three tabs: Solution, Core Concept, Prerequisites
- Each tab fires a separate Claude API call on click
- Content generated fresh (not static/cached at this stage)
- KaTeX renders in AI-generated explanations
- Haiku 4.5 model confirmed in UI

---

## Built and Running

### ✅ generate_questions.py
- Randomly selects section, domain, difficulty, type, diagram presence
- Calls Claude Haiku API once per question
- Generates MCQ, SPR, and R&W questions
- Generates SVG programmatic configs for geometry questions
- Generates Chart.js configs for data questions
- Auto-increments external IDs per domain
- Saves batch to `questions/batch_YYYYMMDD_HHMMSS.json`
- Shows progress line per question

### ✅ review_questions.html
- Opens batch JSON file via file picker
- Renders each question visually with KaTeX, SVG, Chart.js
- Shows correct answer (review mode)
- Pass / Fail buttons
- Downloads reviewed JSON file

---

## Not Yet Built

| Item | Status | Target |
|------|--------|--------|
| Spring Boot application | 🔄 Starting | Month 1 |
| Flyway DB migrations | 🔄 Starting | Month 1, Week 1 |
| Question display (Thymeleaf) | ⬜ Not started | Month 1, Week 2 |
| Exam engine (TestSession) | ⬜ Not started | Month 1, Week 3 |
| Score report | ⬜ Not started | Month 1, Week 4 |
| AI panel in Thymeleaf | ⬜ Not started | Month 2, Week 5-6 |
| User authentication | ⬜ Not started | Month 2, Week 7 |
| Stripe payment | ⬜ Not started | Month 2, Week 8 |
| Landing page | ⬜ Not started | Month 3, Week 10 |
| Error Autopsy | ⬜ Not started | Month 2 |
| Socratic Hints | ⬜ Not started | Month 2 |
| Tutor Chat | ⬜ Not started | Month 3 |
| import_questions.py | ⬜ Not started | When DB ready |
