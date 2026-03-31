package com.satengine.pipeline.claude;

/**
 * All Claude prompts for the question pipeline.
 * Ported from generate_questions.py, agent-review.js, and enrich.js.
 */
public final class PromptLibrary {

    private PromptLibrary() {}

    // ─── Generate — Math ──────────────────────────────────────────────────────

    public static final String GENERATE_SYSTEM_MATH = """
You are an expert SAT Math question writer. Generate exactly ONE SAT question matching the specifications given.

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

    // ─── Generate — Reading & Writing ─────────────────────────────────────────

    public static final String GENERATE_SYSTEM_RW = """
You are an expert SAT Reading & Writing question writer. Generate exactly ONE SAT question matching the specifications given.

DOMAIN TYPES — understand the difference:
• information_ideas / craft_structure / expression_ideas — PASSAGE-BASED: tests reading comprehension.
  Always include passageText. The passage must clearly and unambiguously support exactly one answer.
• standard_english — SENTENCE-LEVEL: tests grammar and mechanics. passageText is a single sentence with ___ where the answer goes. Question stem is always "Which choice completes the text so that it conforms to the conventions of Standard Written English?"

PASSAGE QUALITY — critical rules (for passage-based domains):
Write original, coherent prose — not generic filler. The passage must have a clear argument or narrative.
The correct answer must be supported by the passage directly — not merely suggested.
If two options both seem defensible, rewrite the passage or options until exactly one is correct.
passageText must be plain prose. No LaTeX, no markdown, no bullet points (except for rhetorical_synthesis notes).

SENTENCE-LEVEL QUALITY — critical rules (for standard_english):
Test exactly one grammar rule per question. The sentence must be self-contained.
Exactly one option must be grammatically correct. The other three must violate the rule being tested.

CORRECT ANSWER — critical rules (all domains):
Exactly one option must be correct. The other three must be wrong for clear, articulable reasons.
"Best answer" means unambiguously best — not just plausible.
Test only what the skill specifies.

EXPLANATION — critical rules:
explanationShort must explain in 2–3 confident sentences:
  1. Why the correct answer is right (quote or reference the passage/sentence directly).
  2. Why the most tempting wrong answer fails.
Write as a teacher — confident, no hedging.
NEVER write: "Wait,", "Actually,", "Hmm,", or any stream-of-consciousness phrasing.

POOL — always set to "both"

Return ONLY valid JSON. No markdown. No explanation. Start with { end with }
Nothing before or after the JSON.""";

    /** Returns the correct system prompt for the given section. */
    public static String getGenerateSystem(String section) {
        return "reading_writing".equals(section) ? GENERATE_SYSTEM_RW : GENERATE_SYSTEM_MATH;
    }

    public static String buildGenerateUserPrompt(
            String section, String domain, String skill,
            int difficulty, String questionType,
            boolean hasDiagram, String diagramType) {

        if ("reading_writing".equals(section)) {
            return buildGenerateUserPromptRW(domain, skill, difficulty);
        }

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
                sb.append("""
Provide svgConfig.  The supported shape values and their key fields are:

  triangle / right_triangle — vertices:{A:{x,y},B:{x,y},C:{x,y}}, sides:[{from,to,label}],
    angles:[{at,label}], angleMarkers:[{at,type:"right"|"arc"|"double_arc"}],
    equalSides:[[...]], rightAngleAt:"A"

  circle — cx,cy,radius, sectors:[{fromAngle,toAngle,fillColor,label,centralAngle}],
    radii:[{angle,label}], arcs:[{fromAngle,toAngle,label}],
    chords:[{fromAngle,toAngle,label}], tangents:[{angle,length,label}],
    inscribedAngles:[{vertex,from,to,label}], center:{show,label}, points:[{angle,label}],
    innerRadius (number) — draws annulus/ring; use labels:{outerRadius,innerRadius} for dimension labels
    inscribedPolygon:{sides,rotationDeg,vertexLabels:[],sideLabels:[]} — polygon inside circle
    circumscribedPolygon:{sides,rotationDeg,vertexLabels:[]} — polygon around circle

  angle_figure — angles:[{vx,vy,ray1Angle,ray2Angle,rayLength,label,
    point1Label,point2Label,vertexLabel,rightAngle,arcCount}],
    extraRays:[{vx,vy,angle,length,label}]
    Use this for pure angle-relationship problems (supplementary, vertical, etc.)

  two_triangles — triangle1:{vertices:{A,B,C}}, triangle2:{vertices:{D,E,F}},
    congruentSides:[["AB","DE"]], congruentAngles:[["A","D"]],
    similarity:"AA"|"SAS"|"SSS"|"1:2", scaleFactor:2

  coordinate_plane — xMin,xMax,yMin,yMax
    subtype: "function_graph"  — functions:[{type,params,color,label,labelAt:{x,y}}]
      function types: linear(m,b), quadratic(a,b,c), cubic(a,b,c,d), absolute(a,h,k),
        square_root(a,h,k), exponential(a,b,c), reciprocal(a,h,k), constant(c)
    subtype: "system_of_equations" — functions:[...], intersections:[{x,y,label}]
    subtype: "piecewise" — pieces:[{type,params,domainMin,domainMax,
        leftEndpoint:"open"|"closed"|"none", rightEndpoint:"open"|"closed"|"none", color}]
      Use for SAT questions where f(x) is defined differently on separate intervals.
    subtype: "inequality" — inequalities:[{type,params,operator:"gt"|"gte"|"lt"|"lte",
        shadeAbove:true|false, fillColor, borderColor, lineStyle:"solid"|"dashed"}]
      Use to shade the region satisfying an inequality (e.g. y > 2x+1).
    regions:[{function1:{type,params}, function2:{type,params},
        xMin,xMax, fillColor, color1, color2, label}]
      Add regions[] to shade the area BETWEEN two curves on any subtype.
    points:[{x,y,label,color}], segments:[{from:{x,y},to:{x,y},color,style}]

  normal_curve — mean, stdDev, xMin?, xMax?,
    shadedRegions:[{from,to,fillColor,label}],
    markers:[{x,label,color,dashed}], title?
    Use for statistics questions about normal distributions, z-scores, percentiles.

  regular_polygon — sides(3–12), sideLabel?, vertexLabels:[], showDiagonals?,
    shading?, label?, rotationDeg?
    Use for geometry questions about regular hexagons, pentagons, octagons, etc.

  venn_diagram — sets:[{label,color?,value?,regionLabel?},{label,color?,value?,regionLabel?}],
    intersection:{label?,value?,color?}, title?,
    universal:{label?,value?}  (draws enclosing rectangle = sample space)
    Use for probability set questions: P(A∩B), P(A∪B), P(A only), counting problems.

  rectangle / parallelogram / trapezoid — vertices:{A,B,C,D:{x,y}},
    sides:[{from,to,label}], angles:[{at,label}], showHeight, heightLabel

  parallel_transversal — angle label pairs, transversal line

  triangle_with_altitude — triangle with a perpendicular height line

  number_line — min, max, step, points:[{value,label,style}]

  3d_shape — type: "rectangular_prism"|"cube"|"cylinder"|"cone"|"pyramid"|
    "sphere"|"triangular_prism"|"frustum"
    labels:{length,width,height,radius,base,topRadius,bottomRadius,depth}

  composite — shapes:[{shape:"rectangle",offsetX,offsetY,...},
    {shape:"triangle",offsetX,offsetY,...}],
    dimensions:[{x,y,label}], arrows:[{x1,y1,x2,y2,label}]
    Use when a question involves a combined figure (e.g. rectangle + semicircle).

Set width/height in pixels (typical: 240×200 for simple shapes, 320×240 for complex).
""");
            } else {
                sb.append("Provide chartConfig with chartType, labels[], datasets[], and optional fields:\n  stacked:true  — for stacked bar charts (datasets[] still used)\n  Each dataset: {label, values:[], color}\n  Multiple datasets in bar chart = grouped bars (side by side) by default.\n  Set stacked:true for stacked bars (e.g. showing parts of a whole).\n");
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

    private static String buildGenerateUserPromptRW(String domain, String skill, int difficulty) {
        StringBuilder sb = new StringBuilder();
        sb.append("Generate one SAT Reading & Writing question with these exact specifications:\n\n");
        sb.append("section: reading_writing\n");
        sb.append("domain: ").append(domain).append("\n");
        if (skill != null && !skill.isBlank()) sb.append("skill: ").append(skill).append("\n");
        sb.append("difficulty: ").append(difficulty).append(" (scale 1=easy … 7=hard)\n");
        sb.append("questionType: mcq\n\n");
        sb.append("Provide optionA, optionB, optionC, optionD and correctAnswer (A/B/C/D).\n");
        sb.append("Make exactly one option correct. The other three must be wrong for clear, articulable reasons.\n\n");

        // Domain-specific passage instructions
        switch (domain == null ? "" : domain) {
            case "information_ideas" -> sb.append("""
PASSAGE REQUIRED — this domain always tests comprehension of a text.
Write an original 3–6 sentence passage on any academic topic (science, history, social science, humanities).
The passage must clearly and unambiguously support the correct answer.
The question tests one of: central idea, key detail, textual evidence, quantitative evidence, inference, or cross-text connection.
passageText must be non-null.
""");
            case "craft_structure" -> sb.append("""
PASSAGE REQUIRED — this domain always tests how and why an author wrote a text.
Write an original 3–5 sentence passage with clear rhetorical choices (word choice, structure, tone, purpose).
The question tests one of: vocabulary in context, text structure/purpose, or author's perspective/rhetorical choice.
The correct vocabulary answer must be the word that best fits the passage's specific context and tone — not just any synonym.
passageText must be non-null.
""");
            case "expression_ideas" -> sb.append("""
PASSAGE / NOTES REQUIRED — this domain always provides source material.
For rhetorical_synthesis: provide 3–5 bullet-point notes as passageText (format: "• Note one\\n• Note two\\n...").
  The question asks the student to select which sentence best synthesizes the notes for a specific purpose.
For transitions: provide a short 2–3 sentence passage with a blank [BLANK] where the transition word/phrase goes.
  The options are competing transition words/phrases. Exactly one fits the logical relationship.
passageText must be non-null.
""");
            case "standard_english" -> sb.append("""
PASSAGE REQUIRED — Standard English questions always provide a sentence for the student to complete.
passageText must be a single sentence (or 2 short sentences for context) containing ___ where the answer goes.
Example passageText: "The researchers, who had studied the phenomenon for decades, ___ their findings at the annual conference."
questionStem must be exactly: "Which choice completes the text so that it conforms to the conventions of Standard Written English?"
The four options are alternative word/phrase choices for the blank. Exactly one is grammatically correct.
Test exactly one rule per question: sentence boundaries, subject-verb agreement, pronoun-antecedent agreement,
verb tense/form, punctuation, or modifier placement.
The sentence must be self-contained — no external context needed.
""");
            default -> sb.append("Include a passage if the skill requires reading comprehension; set passageText to null for sentence-level grammar questions.\n");
        }

        sb.append("""
Return this exact JSON shape:
{
  "skill": "specific skill within the domain",
  "passageText": "passage / notes / sentence-with-blank — required for all R&W domains",
  "passageSource": null,
  "questionStem": "...",
  "optionA": "...",
  "optionB": "...",
  "optionC": "...",
  "optionD": "...",
  "correctAnswer": "A",
  "explanationShort": "2-3 sentences: why the correct answer is right and why the best distractor fails.",
  "pool": "both",
  "diagram": null
}""");
        return sb.toString();
    }

    // ─── Agent Review ─────────────────────────────────────────────────────────

    /** Returns the correct review prompt for the given section. */
    public static String buildReviewPrompt(String questionJson, String section, String questionType) {
        if ("reading_writing".equals(section)) return buildReviewPromptRW(questionJson);
        if ("spr".equals(questionType))        return buildReviewPromptMathSPR(questionJson);
        return buildReviewPromptMathMCQ(questionJson);
    }

    public static String buildReviewPrompt(String questionJson, String section) {
        return buildReviewPrompt(questionJson, section, "mcq");
    }

    /** Backwards-compatible overload — assumes math MCQ. */
    public static String buildReviewPrompt(String questionJson) {
        return buildReviewPromptMathMCQ(questionJson);
    }

    private static String buildReviewPromptMathMCQ(String questionJson) {
        return """
You are a rigorous SAT Math question reviewer.
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
                    Required for MCQ: questionStem, optionA, optionB, optionC, optionD,
                    correctAnswer (A/B/C/D), explanationShort.

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
- SCHEMA failures are always "critical".
- STEPS failures are "critical" if steps are missing, "warning" if low quality.
- solvedAnswer MUST be exactly one letter (A, B, C, or D).
  Never put reasoning or phrases like "None of the options" in solvedAnswer.
  If you believe no option is correct, set solvedAnswer to the closest letter and flag it as critical MATH issue.
- Return ONLY the JSON object. No other text.""";
    }

    private static String buildReviewPromptMathSPR(String questionJson) {
        return """
You are a rigorous SAT Math question reviewer. This is an SPR (Student Produced Response) question — no answer choices, student enters a numeric answer.
Review the following question and return ONLY a JSON object — no explanation, no markdown fences.

QUESTION JSON:
""" + questionJson + """

Perform ALL of the following checks:

1. MATH           — Solve the question yourself. Verify that your answer falls within
                    the sprMin–sprMax range. Show your working in the "notes" field.
2. SPR_RANGE      — Is the sprMin–sprMax range correct and reasonable?
                    A single exact answer should have sprMin == sprMax.
3. STEPS          — Are explanationSteps present with 2–4 entries? Is each step correct
                    and free of hedging language?
4. DIAGRAM_MATCH  — If a diagram is present, does its shape/type match the question stem?
5. STEM_CLARITY   — Is the question stem unambiguous — exactly one numeric answer is defensible?
6. SCHEMA         — Are all required fields present and non-empty?
                    Required for SPR: questionStem, sprMin, sprMax, explanationShort.
                    optionA–D and correctAnswer MUST be null — do NOT flag their absence as an error.

Return this exact JSON shape:
{
  "pass": true,
  "confidence": 0.92,
  "solvedAnswer": "320",
  "issues": [
    { "check": "MATH", "severity": "critical", "detail": "..." }
  ],
  "fixes": [
    { "field": "sprMin", "current": "300", "suggested": "320" }
  ],
  "notes": "Computed: ..."
}

Rules:
- A question FAILS (pass: false) if it has ANY issue with severity "critical".
- Warnings and info issues still allow pass: true.
- If there are no issues, return issues: [], fixes: [].
- SCHEMA and SPR_RANGE failures are always "critical".
- STEPS failures are "critical" if steps are missing, "warning" if low quality.
- solvedAnswer MUST be a numeric value (not a letter).
- Return ONLY the JSON object. No other text.""";
    }

    private static String buildReviewPromptRW(String questionJson) {
        return """
You are a rigorous SAT Reading & Writing question reviewer.
Review the following question and return ONLY a JSON object — no explanation, no markdown fences.

QUESTION JSON:
""" + questionJson + """

Perform ALL of the following checks:

1. CORRECT_ANSWER  — Read the passage/sentence and question carefully. Is the stated
                     correctAnswer actually the best answer? Show your reasoning in "notes".
2. ANSWER_KEY      — Does the correctAnswer letter ('A','B','C','D') map to the option
                     that contains the correct text?
3. DISTRACTORS     — Are all four options distinct (no duplicates, no near-duplicates)?
4. SINGLE_BEST     — Is exactly ONE option defensible? Could a strong student argue for
                     any wrong answer? If so, flag as critical.
5. PASSAGE_SUPPORT — For information_ideas / craft_structure / expression_ideas:
                     passageText must be present and must directly support the correct answer.
                     Flag as critical if passageText is null or does not clearly support the answer.
                     For standard_english: passageText should be a single sentence with ___ — flag as critical if null.
6. STEM_CLARITY    — Is the question stem unambiguous and grammatically correct?
7. SCHEMA          — Are all required fields present and non-empty
                     (questionStem, optionA-D, correctAnswer, explanationShort)?

Return this exact JSON shape:
{
  "pass": true,
  "confidence": 0.92,
  "solvedAnswer": "B",
  "issues": [
    { "check": "CORRECT_ANSWER", "severity": "critical", "detail": "..." }
  ],
  "fixes": [
    { "field": "correctAnswer", "current": "A", "suggested": "B" }
  ],
  "notes": "Reasoning: ..."
}

Rules:
- A question FAILS (pass: false) if it has ANY issue with severity "critical".
- Warnings and info issues still allow pass: true.
- If there are no issues, return issues: [], fixes: [].
- SCHEMA, CORRECT_ANSWER, and SINGLE_BEST failures are always "critical".
- solvedAnswer MUST be exactly one letter (A, B, C, or D).
  If you believe no option is correct, set solvedAnswer to the closest letter and flag as critical.
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

2. alternativeApproach: An object describing a second, different method to solve this question.
   { "title": "short name for this method (e.g. 'Substitution', 'Graphical Method')",
     "steps": [ { "title": "...", "content": "...", "math": "..." } ]
   }
   The approach must be genuinely different from the primary explanationSteps (e.g. algebraic vs. arithmetic, substitution vs. elimination, visual vs. analytic).
   If there is no meaningfully different second approach, return null.

3. coreConcept: Object with:
   { "title": "concept name", "summary": "1-2 sentence explanation", "keyFormula": "LaTeX or null" }

4. prerequisites: Array of 2–4 objects:
   { "topic": "topic name", "why": "one sentence — why needed to solve this question" }

5. animation: { "eligible": true/false }
   true only for geometry, coordinate plane, or algebra questions with a clear visual story.

6. pool: Always "both"

Return this exact shape:
{
  "explanationSteps": [...],
  "alternativeApproach": { "title": "...", "steps": [...] },
  "coreConcept": { "title": "...", "summary": "...", "keyFormula": "..." },
  "prerequisites": [...],
  "animation": { "eligible": false },
  "pool": "both"
}""";
    }
}
