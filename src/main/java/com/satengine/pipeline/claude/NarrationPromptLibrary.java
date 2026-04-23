package com.satengine.pipeline.claude;

import com.satengine.pipeline.sympy.MathObject;
import com.fasterxml.jackson.databind.ObjectMapper;

/**
 * Prompt templates for the SymPy pipeline narration and cross-verify steps.
 *
 * Design principles:
 *  - LLM writes prose only — it NEVER touches the numbers.
 *  - All mathematical values come from MathObject (Python-verified).
 *  - Cross-verify is a soft check: mismatch flags but does not block saving.
 */
public final class NarrationPromptLibrary {

    private NarrationPromptLibrary() {}

    // ── Haiku narration ───────────────────────────────────────────────────────

    public static final String NARRATION_SYSTEM = """
You are a precise SAT math question writer. Your job is to narrate a question stem and
explanation around a pre-computed math problem. You NEVER change, invent, or recalculate
any numbers — all numbers, answers, and options are provided to you and must appear
exactly as given.

Output valid JSON only. No markdown, no code fences, no prose outside the JSON object.

Output schema:
{
  "questionStem":     "<full question text with LaTeX for math>",
  "explanationShort": "<one sentence summary of method>",
  "explanationSteps": [
    {"step": 1, "title": "...", "content": "..."},
    ...
  ],
  "coreConcept":      "<one sentence: the core SAT skill this question tests, plain English, no LaTeX, max 15 words>",
  "distractorRationale": {
    "A": "<why a student would pick this wrong answer — skip this key if A is correct>",
    "B": "<...>",
    "C": "<...>",
    "D": "<...>"
  },
  "prerequisites": ["<topic students need to know before this>", "..."],
  "alternativeApproach": "<one paragraph: a different valid method to solve this problem>"
}

⚠ MANDATORY LATEX FORMATTING — applies to every field except coreConcept, prerequisites, and distractorRationale:
- ALL equations, expressions, and variables MUST be wrapped in \\(...\\)
- Inline math: \\(...\\)   e.g. \\(3x + 7 = 22\\) or \\(4x\\) or \\(x = 9\\)
- Display math: \\[...\\]  (only for standalone formulas on their own line)
- NEVER write bare math like:  4x + 9 = 45  or  3x  or  x = 7  — always wrap it
- NEVER use $...$ or $$...$$  (those are reserved for currency like \\(\\$6\\))
- WRONG: "If 4x + 9 = 45, what is the value of 4x?"
- RIGHT:  "If \\(4x + 9 = 45\\), what is the value of \\(4x\\)?"

This rule applies especially to explanationSteps content — every equation must be wrapped:
- CORRECT step: "Divide both sides by 4: \\(x = \\frac{46}{4} = \\frac{23}{2}\\)"
- WRONG step:   "Divide both sides by 4: \\frac{46}{4} = \\frac{23}{2}"
- CORRECT step: "Setting \\(y = 0\\): \\(4x - 8(0) = 46\\), so \\(x = \\frac{46}{4}\\)"
- WRONG step:   "Setting y = 0: 4x = 46, so x = \\frac{46}{4}"

Rules for coreConcept:
- Plain English only, no math notation
- Describes the skill, not the specific numbers (e.g. "Solving a linear equation with variables on both sides")
- Max 15 words

Rules for distractorRationale:
- Only include keys for WRONG answer choices (omit the correct letter)
- Each value describes the specific mistake a student would make to arrive at that wrong answer
- One sentence each, plain English
- For SPR questions, set distractorRationale to null

Rules for prerequisites:
- List 1–3 topics a student must understand before attempting this question
- Short noun phrases only (e.g. "slope-intercept form", "distributive property")
- Plain English, no LaTeX

Rules for alternativeApproach:
- Describe ONE alternative valid method (e.g. substitution vs elimination, guess-and-check, graphing)
- Keep it to 2–3 sentences, plain English
- If no meaningful alternative exists, set to null

Rules for diagram questions (when a graph or diagram is shown):
- NEVER state the slope of the graphed line in the question stem
- NEVER state the y-intercept or any coordinate of the graphed line in the question stem
- The graph is the ONLY source of slope and intercept information — the student must read those values from the graph
- The question stem must only reference that "the graph is shown" and ask what the question asks for
- Stating slope or intercept in the stem reduces the question to pure arithmetic and defeats the entire purpose of the graph
""";

    /**
     * Build the user message for Haiku narration of an MCQ question.
     *
     * @param mo             the MathObject from Python
     * @param optionA-D      the shuffled answer choices (A=correct slot is already set)
     * @param correctLetter  which slot holds the correct answer
     * @param examplesBlock  pre-formatted SAT style examples (from ExampleLoader), or ""
     */
    public static String buildNarrationPrompt(MathObject mo,
                                               String optionA, String optionB,
                                               String optionC, String optionD,
                                               String correctLetter,
                                               ObjectMapper mapper,
                                               String examplesBlock) {
        String paramsJson;
        try {
            paramsJson = mapper.writeValueAsString(mo.params());
        } catch (Exception e) {
            paramsJson = mo.params().toString();
        }

        String diagramHint = mo.diagramSpec() != null
                ? "\nA diagram will be shown. Reference it naturally but do not describe its exact coordinates."
                : "";

        String scenarioHint = mo.scenarioTag() != null
                ? "\nScenario context: " + mo.scenarioTag().replace("_", " ") +
                  ". Weave this naturally into a word problem. Keep it 1–2 sentences of setup, then the question."
                : "\nNo scenario — write a direct math question (no story wrapper needed).";

        String questionContextBlock = (mo.questionContext() != null && !mo.questionContext().isBlank())
                ? "\n⚠ MANDATORY QUESTION CONSTRAINT: " + mo.questionContext() +
                  "\n   The questionStem MUST ask for exactly this quantity. Do not ask for any other derived value."
                : "";

        return """
%sskill:      %s
Difficulty: %d (1=Easy, 2=Medium, 3=Hard)
Question type: %s
Parameters (use EXACTLY these values): %s
Verified answer: %s
Option A: %s
Option B: %s
Option C: %s
Option D: %s
Correct option: %s
%s%s%s

Write the questionStem, explanationShort, explanationSteps, coreConcept, and distractorRationale.
- questionStem must use all parameter values naturally and end with a clear question.
- Match the SAT phrasing style shown in the examples above (if provided).
- The question asked in questionStem must match the MANDATORY QUESTION CONSTRAINT above.
- For MCQ: do NOT reveal the correct answer in the stem or explanation steps.
- explanationSteps should show the full solution (3-5 steps) working toward the verified answer.
- Each step title should be ≤ 5 words. Content ≤ 2 sentences.
- coreConcept: one sentence describing the SAT skill tested, plain English, max 15 words.
- distractorRationale: for each wrong option, one sentence on the mistake that leads there.
⚠ LATEX REMINDER: wrap EVERY equation and expression in \\(...\\). Never write bare math in the stem or steps.
""".formatted(
                examplesBlock,
                mo.skill(), mo.difficulty(), mo.questionType(),
                paramsJson,
                mo.verifiedAnswer(),
                optionA, optionB, optionC, optionD,
                correctLetter,
                scenarioHint, diagramHint, questionContextBlock
        );
    }

    /**
     * Build the user message for Haiku narration of an SPR question.
     */
    public static String buildSprNarrationPrompt(MathObject mo, ObjectMapper mapper,
                                                  String examplesBlock) {
        String paramsJson;
        try {
            paramsJson = mapper.writeValueAsString(mo.params());
        } catch (Exception e) {
            paramsJson = mo.params().toString();
        }

        String scenarioHint = mo.scenarioTag() != null
                ? "\nScenario context: " + mo.scenarioTag().replace("_", " ") +
                  ". Weave this naturally into a word problem."
                : "\nNo scenario — write a direct math question.";

        // When Python supplies an exactStem, show it to Haiku so explanations are
        // anchored to the correct question. Java will also override questionStem in
        // the response, but Haiku must see the correct stem to write correct steps.
        String exactStemBlock = (mo.exactStem() != null && !mo.exactStem().isBlank())
                ? "\n⚠ EXACT QUESTION STEM — use this verbatim as questionStem, write all explanations for THIS question:\n\""
                  + mo.exactStem() + "\"\n"
                : "";

        return """
%sSkill:      %s
Difficulty: %d (1=Easy, 2=Medium, 3=Hard)
Question type: spr (student-produced response, no choices)
Parameters (use EXACTLY these values): %s
Verified answer: %s
%s%s

Write the questionStem, explanationShort, explanationSteps, and coreConcept. Set distractorRationale to null.
- If an EXACT QUESTION STEM is provided above, copy it verbatim as questionStem. Write all explanation steps for that exact question.
- Otherwise, questionStem must end with "What is the value of [quantity]?" or similar open phrasing.
- Match the SAT phrasing style shown in the examples above (if provided).
- Do NOT provide answer choices — this is a grid-in question.
- explanationSteps: 3-5 steps showing full solution.
- coreConcept: one sentence describing the SAT skill tested, plain English, max 15 words.
⚠ LATEX REMINDER: wrap EVERY equation and expression in \\(...\\). Never write bare math in the stem or steps.
""".formatted(
                examplesBlock,
                mo.skill(), mo.difficulty(),
                paramsJson,
                mo.verifiedAnswer(),
                scenarioHint,
                exactStemBlock
        );
    }

    // ── Sonnet cross-verify ───────────────────────────────────────────────────

    public static final String CROSS_VERIFY_SYSTEM = """
You are a senior SAT math content reviewer. You will be given a math question, its
stated correct answer, and the intended question intent. Your job is four checks:

1. Is the stated answer mathematically correct given the question stem?
2. Does the question stem ask for exactly what the intent specifies?
3. Is the question unambiguous — could a well-prepared student reasonably interpret it differently?
4. Does the question stem or any answer choice accidentally reveal or hint at the correct answer?

Respond with JSON only — no markdown, no prose outside the object:
{
  "agrees":              true | false,
  "stem_matches_intent": true | false,
  "is_ambiguous":        true | false,
  "answer_leaked":       true | false,
  "reasoning":           "<one sentence covering all four checks>"
}

Rules:
- "agrees" = false only when the math is genuinely wrong, not just an unusual phrasing
- "stem_matches_intent" = false when the stem asks for a different quantity than the intent
- "is_ambiguous" = true only when a correct student could arrive at two different valid answers
- "answer_leaked" = true when the correct letter/value is obvious from the stem or choice wording
- If intent is null or empty, set stem_matches_intent to true (no intent to check against)
""";

    /**
     * Build the cross-verify prompt sent to Sonnet 4.6 after Haiku narration.
     *
     * @param questionContext  the prescriptive intent string from MathObject (may be null)
     */
    public static String buildCrossVerifyPrompt(String questionStem,
                                                 String correctAnswer,
                                                 String optionA,
                                                 String optionB,
                                                 String optionC,
                                                 String optionD,
                                                 String correctLetter,
                                                 String questionContext) {
        boolean isMcq = correctLetter != null;
        String choicesSection = isMcq ? """
Options:
  A) %s
  B) %s
  C) %s
  D) %s
Stated correct answer: %s) %s
""".formatted(optionA, optionB, optionC, optionD, correctLetter, correctAnswer)
                : "Stated correct answer: " + correctAnswer + " (student-produced response)";

        String intentSection = (questionContext != null && !questionContext.isBlank())
                ? "Intent (what the question MUST ask for):\n" + questionContext
                : "Intent: (none provided)";

        return """
Question:
%s

%s

%s

Run all four checks and reply with the JSON schema above.
""".formatted(questionStem, choicesSection, intentSection);
    }
}
