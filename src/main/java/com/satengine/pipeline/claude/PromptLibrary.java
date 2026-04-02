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
Option fields (optionA–optionD) MUST also use LaTeX delimiters for any math.
NEVER write bare LaTeX like \\frac{2}{5} as an option — always wrap: \\(\\frac{2}{5}\\)
A standalone expression as an option must be written as \\( expression \\).

TABLES — critical rules:
If a question includes a data table, format it using HTML, not markdown pipes.
Use this exact format inside the JSON string value:
<table><thead><tr><th>Column A</th><th>Column B</th></tr></thead><tbody><tr><td>val1</td><td>val2</td></tr></tbody></table>
NEVER use markdown pipe tables (| col | col |) — they do not render in HTML.
NEVER use \\n inside an HTML table; write the entire table on one line.

TABLE SELF-CHECK (mandatory before returning JSON):
Scan your questionStem for any | pipe characters. If found, you have accidentally used a markdown
table. Stop and replace it with the HTML <table> format shown above before returning.

TABLE DATA COMPUTATION — critical rules (when the answer requires calculating from table data):
After writing the table and answer choices, MANUALLY compute the answer from the table values and
confirm it equals the correctAnswer choice within ±0.05.
For weighted mean / average: compute Σ(midpoint × frequency) / Σ(frequency) yourself, step by step.
For open-ended intervals (e.g. "21+" or "100+"), choose a midpoint, state it explicitly in the
first explanationStep, and use that exact midpoint in your calculation.
If your computed value does not match any option exactly, REDESIGN the table data until it does —
never round to a wrong answer and hope the student won't notice.
Each wrong option must correspond to a distinct, nameable student mistake (wrong midpoint, wrong
formula, off-by-one frequency, etc.). No two options should produce the same computed value.

MATH VERIFICATION — critical rules:
Before writing the questionStem, work through the problem yourself and confirm the answer is correct.
Choose numbers that give clean, whole-number or simple-fraction answers.
The equations, values, and data in questionStem MUST be consistent with the correctAnswer.
For table-based questions: after building the table, compute the answer from YOUR OWN table values
and verify it matches correctAnswer. Do NOT assume the answer is correct because you intended it to be.
NEVER adjust the explanation to match a broken question — fix the question first.

DIAGRAM DATA VERIFICATION — critical rules (applies when diagram is present):
Every value in the diagram (bar heights, scatter points, function params, table cells) must be
arithmetically consistent with the correct answer.
After generating diagram data, MANUALLY compute the answer from those values and confirm it
matches correctAnswer before writing the options.
No single bar value, axis value, or data point should accidentally equal the correct answer's
intermediate value by coincidence — each wrong option must correspond to a distinct mistake.
If the diagram is a bar/scatter chart, verify: sum of relevant bars / total = stated percentage or ratio.

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
        return buildGenerateUserPrompt(section, domain, skill, difficulty, questionType,
                hasDiagram, diagramType, null);
    }

    public static String buildGenerateUserPrompt(
            String section, String domain, String skill,
            int difficulty, String questionType,
            boolean hasDiagram, String diagramType,
            String diversityContext) {

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
            sb.append("Set correctAnswer to the numeric answer as a string (e.g. \"48\" or \"3.5\") — NOT a letter.\n");
            sb.append("Set optionA, optionB, optionC, optionD to null.\n");
        }

        if (hasDiagram) {
            sb.append("\nInclude a diagram of type: ").append(diagramType).append(".\n");
            sb.append("""

DIAGRAM TYPE RULES — critical:
Use svg_programmatic (coordinate_plane subtype) for ALL of these:
  - Any graph of a mathematical function: linear, quadratic, absolute value, etc.
  - System of equations / line intersections
  - Inequalities shaded on a coordinate plane
  - Piecewise functions
  - Any diagram where the visual IS the mathematical relationship

Use chartjs ONLY for statistical / data charts:
  - Scatter plots of real-world data (e.g. hours studied vs. test score)
  - Bar charts, histograms, line charts of tabular data
  - Pie charts, box plots, dot plots
  NEVER use chartjs scatter to draw mathematical equations or function graphs.
  chartjs scatter connects a small number of hand-picked points — it looks like dots, not lines.

""");
            if ("svg_programmatic".equals(diagramType)) {
                sb.append("""
The diagram field MUST use this exact two-level structure — no exceptions:
  "diagram": {
    "diagramType": "svg_programmatic",   ← always "svg_programmatic", never "type"
    "svgConfig": {                        ← all shape fields go INSIDE svgConfig
      "shape": "triangle",
      "width": 300, "height": 270,
      ...
    }
  }

Supported shape values and their key fields:

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
      function types: linear(m,b), quadratic(a,b,c), cubic(a,b,c,d),
        quartic(a,b,c,d,e)  [ax⁴+bx³+cx²+dx+e], absolute(a,h,k),
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
                sb.append("""
The diagram field MUST use this exact two-level structure — no exceptions:
  "diagram": {
    "diagramType": "chartjs",          ← always "chartjs", never "type"
    "chartConfig": {                   ← all chart fields go INSIDE chartConfig
      "chartType": "bar",              ← "bar"|"histogram"|"line"|"scatter"|"pie"|"boxplot"|"dotplot"
      "title": "Chart Title",
      "categories": ["A","B","C"],     ← bar/line x-axis labels — NOT "labels"
      "xAxis": { "label": "X label" },
      "yAxis": { "min": 0, "max": 100, "stepSize": 20, "label": "Y label" },
      "datasets": [
        { "label": "Series name", "data": [10, 20, 30], "color": "#2563eb" }
      ]
    }
  }

FIELD NAMES — use EXACTLY these names inside chartConfig (do NOT use Chart.js native names):
  x-axis labels    : "categories": ["A","B","C"]   — NOT "labels"
  single color     : "color": "#hex"  per dataset   — NOT "backgroundColor"
  per-bar colors   : "colors": ["#hex",...]          — NOT "backgroundColor"

Each dataset for bar/line/histogram: { "label", "data":[], "color":"#hex" }
For scatter: datasets:[{ "label", "points":[{"x","y"}], "color" }]
stacked:true — for stacked bar charts.
Multiple datasets in bar chart = grouped bars by default.
REMINDER: if the question involves a mathematical function or equation graph, use svg_programmatic instead.
""");
            }
        } else {
            sb.append("\nNo diagram needed for this question.\n");
        }

        // Inject existing-question diversity context if provided
        if (diversityContext != null && !diversityContext.isBlank()) {
            sb.append("\n").append(diversityContext).append("\n");
        }

        sb.append("""

Return this exact JSON shape (all fields required unless marked optional):
{
  "skill": "specific skill within the domain",
  "scenarioTag": "snake_case label for the real-world scenario used (e.g. projectile_motion, rectangle_area, revenue_model, consecutive_integers, rate_distance_time, mixture_problem, age_problem, coin_problem, work_rate, percent_change)",
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

    /**
     * Builds the diversity context block injected into the generate user prompt.
     * Lists existing scenario tags + question stems for the same domain/skill so
     * Claude can avoid duplicate real-world setups.
     *
     * @param rows  rows from QuestionRepository.findRecentForDiversityContext:
     *              each Object[] is { external_id (String), question_stem (String), scenario_tag (String) }
     * @param domain  domain key, used for labelling only
     * @param skillKey  skill key, used for labelling only
     */
    public static String buildDiversityContext(java.util.List<Object[]> rows, String domain, String skillKey) {
        if (rows == null || rows.isEmpty()) return "";

        StringBuilder sb = new StringBuilder();
        sb.append("\n--- EXISTING QUESTIONS FOR THIS SKILL (do not duplicate) ---\n");
        sb.append("Domain: ").append(domain);
        if (skillKey != null && !skillKey.isBlank()) sb.append(" | Skill: ").append(skillKey);
        sb.append("\n\n");

        for (Object[] row : rows) {
            String id          = row[0] != null ? row[0].toString() : "?";
            String stem        = row[1] != null ? row[1].toString() : "";
            String scenarioTag = row[2] != null ? row[2].toString() : "";

            // Truncate stem to 120 chars to keep token cost low
            String stemShort = stem.length() > 120 ? stem.substring(0, 117) + "..." : stem;
            // Strip LaTeX for readability in the prompt
            stemShort = stemShort.replaceAll("\\\\[a-zA-Z]+\\{[^}]*}", "").replaceAll("[\\\\()]", "").trim();

            sb.append("  ").append(id);
            if (!scenarioTag.isBlank()) sb.append(" [").append(scenarioTag).append("]");
            sb.append(": ").append(stemShort).append("\n");
        }

        sb.append("""

DIVERSITY RULES — strictly enforced:
- Choose a DIFFERENT real-world scenario from every entry above.
- Use different variable names, numbers, and context.
- Avoid these scenario types if already present above: projectile_motion, rectangle_area, revenue_model, etc.
- If the list above shows 2+ word problems, consider a pure-algebra or graphical question instead.
- Set "scenarioTag" in your response to a concise snake_case label for the scenario you chose.
--- END EXISTING QUESTIONS ---
""");
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
   FORMULA RULE: If a step references a named formula (e.g. "quadratic formula", "slope-intercept form",
   "distance formula", "Pythagorean theorem", "completing the square"), the formula itself MUST appear
   in that step's "math" field. Never mention a formula by name without showing it.

2. alternativeApproach: An object describing a second, different method to solve this question.
   { "title": "short name for this method (e.g. 'Substitution', 'Graphical Method')",
     "steps": [ { "title": "...", "content": "...", "math": "..." } ]
   }
   The approach must be genuinely different from the primary explanationSteps (e.g. algebraic vs. arithmetic, substitution vs. elimination, visual vs. analytic).
   If there is no meaningfully different second approach, return null.
   FORMULA RULE (same as above): any step that names a formula must show it in "math".

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
