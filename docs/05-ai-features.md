# 05 — AI Features

---

## The AI Panel — Core Feature

### ADR-023 — Three-Tab Structured AI Panel

**Decision:** Three separate Claude API calls, each with a different system prompt, each serving a different pedagogical purpose.

| Tab | Purpose | System Prompt Focus | Student Who Needs It |
|-----|---------|--------------------|--------------------|
| **Solution** | How to solve THIS problem | Step-by-step procedural | Got it wrong, wants to understand the solution |
| **Core Concept** | The underlying math/grammar idea | Conceptual, generalisable | Wants to understand the category of problem |
| **Prerequisites** | What to learn before this | Diagnostic, foundational | Completely lost, needs to go back further |

### Key Implementation Decisions
- **Lazy loaded** — only fires when student clicks the tab (not on page load)
- **Cached per question** — generate once, serve to every student from cache
- **Available in Review Mode only** — not during timed exam
- **KaTeX re-renders** on AI response (explanations contain LaTeX)
- **Streams token by token** (Spring AI streaming via SSE)

**Status:** ✅ DECIDED — Validated working with live API calls

---

### System Prompt Templates

**Solution Tab:**
```
You are an expert SAT tutor.
A student got this question wrong.

Question: {question_stem}
Their answer: {student_answer}
Correct answer: {correct_answer}

Structure your solution like this:
1. Common mistake: What students typically do wrong here and why it fails.
2. Key insight: The one thing to notice to solve this efficiently.
3. Step-by-step solution: Each step clearly labeled with LaTeX.
4. Shortcut: A faster method if one exists.
5. Takeaway: One sentence — what to remember next time.

Keep under 200 words. Use LaTeX for all math.
```

**Core Concept Tab:**
```
You are an expert SAT tutor.
Question: {question_stem}
Domain: {domain}

Explain the core mathematical concept being tested.
Do NOT solve this specific question.
Format:
- What concept this tests (one sentence)
- The key formula or rule (LaTeX)
- When this appears on SAT (rare/common/very common)
- One real-world analogy if helpful

Keep under 150 words.
```

**Prerequisites Tab:**
```
You are an expert SAT tutor.
Question: {question_stem}
Domain: {domain}
Difficulty: {difficulty}/7
Student's mastered topics: {mastered_topics}

List 3–5 prerequisite topics this student needs.
Format each as:
• **Topic name** — one sentence explaining why it's needed for this specific question.

Order from most fundamental to most advanced.
Be specific: not "know algebra" but "solve for a variable in a two-step equation."
```

---

## ADR-024 — AI Model Selection

**Phase 1 (Validation — now to Month 6):** Claude Haiku 4.5 for everything.

**Phase 2 (Post-launch routing):**

| Condition | Model | Cost (output) |
|-----------|-------|---------------|
| Difficulty 1–3, any tab | Groq/Llama 3.3 70B | $0.79/MTok |
| Difficulty 4–5 | Claude Haiku 4.5 | $5.00/MTok |
| Difficulty 6–7, Solution tab | Claude Sonnet 4.6 | $15.00/MTok |
| All R&W questions | Claude Haiku 4.5 | $5.00/MTok |

Spring AI's abstraction makes this routing a config change, not a code rewrite.

**Status:** ✅ DECIDED

---

## ADR-025 — AI Cost Model

**Per test review (realistic student behaviour):**
```
Wrong answers reviewed:     ~35 out of 98
AI tabs opened per question: ~1.5 average
API calls per test review:   ~52

Cost per call (Haiku, 500 input + 300 output tokens):
  Input:  500 × $1/MTok  = $0.0005
  Output: 300 × $5/MTok  = $0.0015
  Total per call:          $0.002

Cost per test review: 52 × $0.002 = $0.10
(pre-caching)

With 90% cache hit rate at scale:
  Effective cost per test review: ~$0.01
  Cost per student per month:     ~$0.50
  Gross margin at $14.99/month:   ~97%
```

**Status:** ✅ DECIDED

---

## Interactive AI Features — Build Priority

### ADR-026 — Build Order

| Priority | Feature | When | Effort | Uniqueness |
|----------|---------|------|--------|------------|
| 1 | **Error Autopsy** | Month 2, Week 5-6 | Low | High — nobody has this |
| 2 | **Socratic Hints** | Month 2, Week 7-8 | Medium | High |
| 3 | **Tutor Chat** | Month 3 | Low | Medium |
| 4 | **Debate Mode** | Month 4-5 | Medium | Very high — completely unique |
| 5 | **What-If Explorer** | Month 5-6 | Medium | High |

**Status:** 🔄 IN PROGRESS

---

### Feature 1: Error Autopsy

**What:** AI diagnoses exactly HOW the student reasoned incorrectly — not just what the right answer is.

**When:** Fires automatically in review mode for every wrong answer. Shown in amber box before the main explanation.

**System prompt:**
```
Determine the most likely reasoning error that led a student
to choose [{wrong_answer}] when the correct answer is [{correct_answer}].

Format:
DIAGNOSIS: [one line — the specific mistake]
EXPLANATION: [2-3 sentences — why this thinking fails]
MEMORY TRICK: [one memorable tip to avoid this mistake]
```

**Endpoint:** `POST /api/autopsy/{questionId}` with student's wrong answer

---

### Feature 2: Socratic Hint System

**What:** 3-level hints before showing the solution. Student earns the answer.

**Flow:**
- Click "Get a Hint" → Hint 1 (conceptual nudge)
- Click again → Hint 2 (formula reminder)
- Click again → Hint 3 (partial solution)
- Click again → Full solution reveals

Track how many hints each student needs per domain — this is a diagnostic signal for weak areas.

---

### Feature 3: Tutor Chat

**What:** Persistent contextual chat below the three tabs. Always available in review mode.

**Context sent with every message:**
- Full question content
- Student's wrong answer
- What the three tabs already said
- Student's weakness profile

**Endpoint:** `POST /api/chat/{questionId}`
```json
{
  "message": "Why is B wrong?",
  "conversationHistory": [...]
}
```

---

### Feature 4: Debate Mode — "Convince Me"

**What:** AI argues for the wrong answer. Student must counter with correct reasoning to win.

**Flow:**
1. Student gets question wrong
2. Clicks "Debate Mode"
3. AI: "I think the answer is B. Here's why: [plausible wrong argument]"
4. Student argues back
5. AI pushes back with counter-arguments
6. Student uses correct mathematical reasoning to win
7. AI concedes: "You're right. I was confusing X with Y."
8. "AI Defeated!" celebration

**System prompt:** AI argues plausibly for wrong answer. Pushes back. Concedes only when student demonstrates full understanding.

**Why this is the most unique feature:** No SAT platform has this. It's genuinely fun. Students will mention it on Reddit.

---

### Feature 5: What-If Explorer

**What:** AI generates 3 variations of the same question — same concept, different numbers.

**Flow:**
- After wrong answer review → "Try Variations" button
- Three mini-questions appear inline (no timer, no full test flow)
- Instant feedback after each
- 2 correct in a row → "Concept mastered"
- Keep failing → flags domain for targeted practice

**Prevents:** Pattern memorisation. Forces genuine concept generalisation.

---

## ADR-027 — Open Source Model Policy

**Decision:** Add open source routing only after launch when real usage data justifies the engineering effort. Never sacrifice explanation quality for cost savings.

**Reasoning:**
1. Validate with Claude first — if quality is poor, you know it's a prompt problem not a model problem
2. Caching saves 90% of costs at scale — more impactful than model switching
3. Quality is the product's core differentiator — Acely's failure is low-quality AI

**When to add open source:** After Month 6, when you have 100+ students, real usage data, and proven quality baseline.

**Best open source option for SAT:** Llama 3.3 70B via Groq ($0.79/MTok output) for easy questions.

**Status:** ✅ DECIDED
