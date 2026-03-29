package com.satengine.pipeline.claude;

/**
 * All Claude prompts for the question pipeline.
 * Ported from generate_questions.py, agent-review.js, and enrich.js.
 */
public final class PromptLibrary {

    private PromptLibrary() {}

    // ─── Generate ─────────────────────────────────────────────────────────────

    public static final String GENERATE_SYSTEM = """
You are an expert SAT question writer. Generate exactly ONE SAT question matching the specifications given.

MATH NOTATION — critical rules:
All math MUST use LaTeX notation.
Inline math: \\( expression \\)
Display math: \\[ expression \\]
Fractions: \\frac{num}{denom}
Exponents: x^{2}
Square root: \\sqrt{x}
Greek: \\theta \\pi \\alpha
NEVER use Unicode superscripts like ² ³
NEVER use Unicode subscripts like ₁ ₂
Always use LaTeX.

TABLES — critical rules:
If a question includes a data table, format it using HTML, not markdown pipes.
Use this exact format inside the JSON string value:
<table><thead><tr><th>Column A</th><th>Column B</th></tr></thead><tbody><tr><td>val1</td><td>val2</td></tr></tbody></table>
NEVER use markdown pipe tables (| col | col |) — they do not render in HTML.
NEVER use \\n inside an HTML table; write the entire table on one line.

MATH VERIFICATION — critical rules:
Before writing the questionStem, work through the problem yourself and confirm the answer is correct.
Choose numbers that give clean, whole-number or simple-fraction answers.
The equations, values, and data in questionStem MUST be consistent with the correctAnswer.
NEVER adjust the explanation to match a broken question — fix the question first.

EXPLANATION — critical rules:
Write explanationSteps as 2–4 structured steps. Each step has:
  "title": short step name (e.g. "Set up the equation")
  "content": one or two confident, authoritative sentences explaining what to do and why
  "math": the key formula, expression, or calculation for this step (LaTeX supported), or null if not needed
Write as a teacher would — confident, clean, no hedging.
NEVER write: "Wait,", "Let me recalculate", "Actually,", "Hmm,", "Let me re-read", "Rechecking,",
"Let me verify", "I need to reconsider", "Let me try again", "doesn't yield", "doesn't work",
"Let me use", "Let me rewrite", or any stream-of-consciousness phrasing.
Every step must be correct and stated with confidence. Do the arithmetic before you write it.

TRAP ANALYSIS — critical rules:
trapCategory must be exactly one of: formula_confusion | sign_error | trap_answer | misread | calculation_error | concept_gap | overcomplicated
trapExplanation must be specific to this question — explain which wrong option a student likely chose and why, referencing actual values.

CORE CONCEPT — critical rules:
coreConcept.title: the name of the mathematical concept this question tests
coreConcept.summary: 1–2 sentences explaining the concept clearly
coreConcept.keyFormula: the key formula or rule (LaTeX supported), or null if concept is not formula-based

PREREQUISITES — critical rules:
List 2–4 prerequisite topics a student must understand to solve this question.
Each prerequisite: { "topic": "topic name", "why": "one sentence explaining why this topic is needed" }

POOL — always set to "both" (the content team will reclassify later)

Return ONLY valid JSON. No markdown. No explanation. Start with { end with }
Nothing before or after the JSON.""";

    public static String buildGenerateUserPrompt(
            String section, String domain, String skill,
            int difficulty, String questionType,
            boolean hasDiagram, String diagramType) {

        StringBuilder sb = new StringBuilder();
        sb.append("Generate one SAT question with these exact specifications:\n\n");
        sb.append("section: ").append(section).append("\n");
        sb.append("domain: ").append(domain).append("\n");
        if (skill != null && !skill.isBlank()) sb.append("skill: ").append(skill).append("\n");
        sb.append("difficulty: ").append(difficulty).append(" (scale 1=easy … 7=hard)\n");
        sb.append("questionType: ").append(questionType).append("\n");

        if (questionType.equals("mcq")) {
            sb.append("\nFor MCQ: provide optionA, optionB, optionC, optionD and correctAnswer (A/B/C/D).\n");
            sb.append("Make exactly one option correct. The other three should be plausible distractors.\n");
        } else {
            sb.append("\nFor SPR: provide sprMin and sprMax (numeric range for accepted answers). No options needed.\n");
        }

        if (hasDiagram) {
            sb.append("\nInclude a diagram of type: ").append(diagramType).append(".\n");
            if ("svg_programmatic".equals(diagramType)) {
                sb.append("Provide svgConfig with shape, dimensions, and labeled elements.\n");
            } else {
                sb.append("Provide chartConfig with chartType, labels[], and datasets[].\n");
            }
        } else {
            sb.append("\nNo diagram needed for this question.\n");
        }

        sb.append("""

Return this exact JSON shape (all fields required unless marked optional):
{
  "skill": "specific skill within the domain",
  "questionStem": "...",
  "optionA": "...",
  "optionB": "...",
  "optionC": "...",
  "optionD": "...",
  "correctAnswer": "A",
  "sprMin": null,
  "sprMax": null,
  "explanationShort": "One sentence.",
  "explanationSteps": [
    { "title": "...", "content": "...", "math": "..." }
  ],
  "trapCategory": "formula_confusion",
  "trapExplanation": "...",
  "coreConcept": { "title": "...", "summary": "...", "keyFormula": "..." },
  "prerequisites": [{ "topic": "...", "why": "..." }],
  "animation": { "eligible": false },
  "pool": "both",
  "passageText": null,
  "passageSource": null,
  "diagram": null
}""");
        return sb.toString();
    }

    // ─── Agent Review ─────────────────────────────────────────────────────────

    public static String buildReviewPrompt(String questionJson) {
        return """
You are a rigorous SAT question reviewer with expertise in math and reading/writing.
Review the following question and return ONLY a JSON object — no explanation, no markdown fences.

QUESTION JSON:
""" + questionJson + """

Perform ALL of the following checks:

1. MATH           — Solve the question yourself. Is the stated correctAnswer correct?
                    Show your working in the "notes" field.
2. ANSWER_KEY     — Does the correctAnswer letter ('A','B','C','D') map to the option
                    that contains the correct value?
3. DISTRACTORS    — Are all four options distinct (no duplicates, no near-duplicates)?
4. TRAP_QUALITY   — Are the wrong answers plausible (common student mistakes)?
5. STEPS          — Are explanationSteps present with 2–4 entries? Is each step correct
                    and free of hedging language?
6. DIAGRAM_MATCH  — If a diagram is present, does its shape/type match the question stem?
7. STEM_CLARITY   — Is the question stem unambiguous — exactly one option is defensible?
8. SCHEMA         — Are all required fields present and non-empty?
9. TRAP_CATEGORY  — Is trapCategory one of the 7 valid values:
                    formula_confusion | sign_error | trap_answer | misread |
                    calculation_error | concept_gap | overcomplicated

Return this exact JSON shape:
{
  "pass": true,
  "confidence": 0.92,
  "solvedAnswer": "B",
  "issues": [
    { "check": "MATH", "severity": "critical", "detail": "..." }
  ],
  "fixes": [
    { "field": "correctAnswer", "current": "A", "suggested": "B" }
  ],
  "notes": "Computed: ..."
}

Rules:
- A question FAILS (pass: false) if it has ANY issue with severity "critical".
- Warnings and info issues still allow pass: true.
- If there are no issues, return issues: [], fixes: [].
- SCHEMA and TRAP_CATEGORY failures are always "critical".
- STEPS failures are "critical" if steps are missing, "warning" if low quality.
- solvedAnswer MUST be exactly one letter (A, B, C, or D) for MCQ, or a numeric value for SPR.
  Never put reasoning or phrases like "None of the options" in solvedAnswer.
  If you believe no option is correct, set solvedAnswer to the closest letter and flag it as critical MATH issue.
- Return ONLY the JSON object. No other text.""";
    }

    // ─── Enrich ───────────────────────────────────────────────────────────────

    public static String buildEnrichPrompt(String questionJson) {
        return """
You are an expert SAT educator. Given this SAT question, generate the missing pedagogical fields.
Return ONLY a JSON object — no explanation, no markdown fences.

QUESTION:
""" + questionJson + """

Generate ALL of these fields:

1. explanationSteps: Array of 2–4 structured steps. Each step:
   { "title": "short step name", "content": "1-2 confident sentences", "math": "LaTeX formula or null" }
   Write as a teacher — confident, no hedging, no "Actually..." or "Wait..."

2. trapCategory: Exactly one of:
   formula_confusion | sign_error | trap_answer | misread | calculation_error | concept_gap | overcomplicated

3. trapExplanation: 1-2 sentences. Which specific wrong option would a student likely choose and why?
   Reference actual values from the question.

4. coreConcept: Object with:
   { "title": "concept name", "summary": "1-2 sentence explanation", "keyFormula": "LaTeX or null" }

5. prerequisites: Array of 2–4 objects:
   { "topic": "topic name", "why": "one sentence — why needed to solve this question" }

6. animation: { "eligible": true/false }
   true only for geometry, coordinate plane, or algebra questions with a clear visual story.

7. pool: Always "both"

Return this exact shape:
{
  "explanationSteps": [...],
  "trapCategory": "...",
  "trapExplanation": "...",
  "coreConcept": { "title": "...", "summary": "...", "keyFormula": "..." },
  "prerequisites": [...],
  "animation": { "eligible": false },
  "pool": "both"
}""";
    }
}
