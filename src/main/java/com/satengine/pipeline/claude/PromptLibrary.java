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
                hasDiagram, diagramType, null, null);
    }

    public static String buildGenerateUserPrompt(
            String section, String domain, String skill,
            int difficulty, String questionType,
            boolean hasDiagram, String diagramType,
            String diversityContext) {
        return buildGenerateUserPrompt(section, domain, skill, difficulty, questionType,
                hasDiagram, diagramType, diversityContext, null);
    }

    public static String buildGenerateUserPrompt(
            String section, String domain, String skill,
            int difficulty, String questionType,
            boolean hasDiagram, String diagramType,
            String diversityContext, String targetLetter) {

        if ("reading_writing".equals(section)) {
            return buildGenerateUserPromptRW(domain, skill, difficulty, targetLetter);
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
            sb.append("""
QUESTION DESIGN — do this first, before writing options:
1. Solve the problem yourself and obtain ONE specific answer (a number, expression, or statement).
2. Design the stem so that answer is THE ONLY correct one. Avoid stems like "which of the following satisfies..."
   or "which of the following is a valid..." where multiple values could independently satisfy the condition.
   Instead use stems that demand one specific answer: "What is the value of x?", "What is the slope?",
   "Which equation represents this relationship?" — questions with a unique solution.
3. Write the correct option first, then construct the three wrong options as specific common mistakes
   (sign error, wrong formula, arithmetic slip — each a different error type).

DISTRACTOR RULES — verified before submitting:
- Substitute each wrong option back into the problem. It must produce an INCORRECT result.
- If you cannot show why an option is wrong, the stem is too broad — rewrite the stem to be more specific.
- NEVER use a stem where an inequality, set membership, or property could be satisfied by more than one option.
""");
            if (targetLetter != null) {
                sb.append("IMPORTANT: The correct answer MUST be option ").append(targetLetter)
                  .append(". Design the question so that option ").append(targetLetter)
                  .append(" is definitively correct and set correctAnswer to \"").append(targetLetter).append("\".\n");
            }
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
  "distractorErrors": {
    "X": "when substituted into the problem, option X gives [result] which is wrong because [reason]",
    "Y": "when substituted into the problem, option Y gives [result] which is wrong because [reason]",
    "Z": "when substituted into the problem, option Z gives [result] which is wrong because [reason]"
  },
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
        return buildGenerateUserPromptRW(domain, skill, difficulty, null);
    }

    private static String buildGenerateUserPromptRW(String domain, String skill, int difficulty, String targetLetter) {
        StringBuilder sb = new StringBuilder();
        sb.append("Generate one SAT Reading & Writing question with these exact specifications:\n\n");
        sb.append("section: reading_writing\n");
        sb.append("domain: ").append(domain).append("\n");
        if (skill != null && !skill.isBlank()) sb.append("skill: ").append(skill).append("\n");
        sb.append("difficulty: ").append(difficulty).append(" (scale 1=easy … 7=hard)\n");
        sb.append("questionType: mcq\n\n");
        sb.append("Provide optionA, optionB, optionC, optionD and correctAnswer (A/B/C/D).\n");
        sb.append("""
QUESTION DESIGN — do this first, before writing options:
1. Identify the ONE specific meaning, choice, or completion the passage uniquely supports.
2. Design the stem so only that one interpretation is correct. Avoid stems where multiple options
   could plausibly complete the text or answer the question.
3. Write the correct option, then construct three wrong options each representing a distinct failure:
   too broad, contradicted by the passage, opposite meaning, or out of scope.

DISTRACTOR RULES — verified before submitting:
- Re-read each wrong option against the passage and confirm it is NOT supported.
- If you cannot clearly explain why an option is wrong, rewrite the passage or stem to be more specific.
- NEVER write options that are merely less precise — if it's accurate it's correct, not a distractor.
- NEVER write two options that could both be argued as correct interpretations.
""");
        if (targetLetter != null) {
            sb.append("IMPORTANT: The correct answer MUST be option ").append(targetLetter)
              .append(". Set correctAnswer to \"").append(targetLetter).append("\" and make sure option ")
              .append(targetLetter).append(" is the definitively correct choice.\n");
        }
        sb.append("\n");

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
  "distractorErrors": {
    "X": "one sentence: why this wrong option is wrong — the specific mistake it represents",
    "Y": "...",
    "Z": "..."
  },
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

    /**
     * Builds the enrichment prompt with difficulty-calibrated guardrails baked in.
     *
     * @param questionJson  slim question JSON (stem, options, answer, difficulty, domain, etc.)
     * @param section       "math" or "reading_writing"
     * @param domain        e.g. "algebra", "geometry_trigonometry"
     * @param difficulty    1–7
     * @param questionType  "mcq" or "spr"
     */
    public static String buildEnrichPrompt(
            String questionJson,
            String section,
            String domain,
            int    difficulty,
            String questionType) {

        // ── Difficulty-calibrated limits ──────────────────────────────────────
        int maxSteps    = difficulty <= 2 ? 2 : difficulty <= 4 ? 3 : difficulty <= 6 ? 4 : 5;
        int maxAltSteps = Math.max(maxSteps, 2); // alternative approach always gets at least 2 steps
        int maxWords    = difficulty <= 2 ? 25 : difficulty <= 4 ? 45 : difficulty <= 6 ? 65 : 80;
        int maxPrereqs  = difficulty <= 2 ? 1  : difficulty <= 4 ? 2  : 3;
        boolean isMcq  = "mcq".equalsIgnoreCase(questionType);

        // ── Difficulty language calibration ───────────────────────────────────
        String diffCalibration;
        if (difficulty <= 2) {
            diffCalibration =
                "  This is a VERY EASY question. Use plain language. Every step spells out the operation explicitly.\n" +
                "  Do not assume prior knowledge. Keep content short and reassuring.\n" +
                "  If you find yourself writing more than 2 steps, you are over-explaining — stop.";
        } else if (difficulty <= 4) {
            diffCalibration =
                "  This is an AVERAGE difficulty question. Use standard SAT-level language.\n" +
                "  Moderate detail — explain the logic but don't over-narrate basic algebra.";
        } else if (difficulty <= 6) {
            diffCalibration =
                "  This is a HARD question. Be concise — assume the student knows fundamentals.\n" +
                "  Focus on the non-obvious insight or the key decision point that trips students up.";
        } else {
            diffCalibration =
                "  This is a VERY HARD question. Assume solid foundational knowledge.\n" +
                "  Focus on the elegant approach or the single non-obvious leap.\n" +
                "  One well-chosen insight beats three obvious steps.";
        }

        // ── Diagram instruction based on domain ────────────────────────────────
        String diagramInstruction;
        if ("geometry_trigonometry".equals(domain)) {
            diagramInstruction =
                "DIAGRAM RULE: Geometry questions MUST include a diagram in at least one step.\n" +
                "  Add a \"diagram\" field to the relevant step using the same JSON schema as the question-level diagram field.\n" +
                "  Suggested size: width=280, height=280.";
        } else if ("algebra".equals(domain) || "advanced_math".equals(domain)) {
            diagramInstruction =
                "DIAGRAM RULE: If the solution involves graphing, coordinate geometry, or a visual transformation,\n" +
                "  include a \"diagram\" field on the setup step (type: coordinatePlane or similar).\n" +
                "  If the solution is purely algebraic, omit diagram fields entirely.";
        } else {
            diagramInstruction =
                "DIAGRAM RULE: Do not include diagram fields for this domain.";
        }

        // ── Wrong answer explanations (MCQ only) ──────────────────────────────
        String wrongAnswerField = isMcq
            ? "\n7. wrongAnswerExplanations: One sentence per option — the specific mistake that leads a student there.\n" +
              "   { \"A\": \"...\", \"B\": \"...\", \"C\": \"...\", \"D\": \"...\" }\n" +
              "   - For the CORRECT option key: write exactly \"Correct.\"\n" +
              "   - For each wrong option: name the exact error mechanism.\n" +
              "     BAD: \"This is incorrect.\"  BAD: \"Student may have made a computational error.\"\n" +
              "     GOOD: \"Results from applying the theorem with x=−2 instead of x=2 — sign confusion from (x−2).\"\n" +
              "     GOOD: \"Arithmetic slip: computed 5×4=16 instead of 20 in the second term.\""
            : "";

        String wrongAnswerSchemaLine = isMcq
            ? "  \"wrongAnswerExplanations\": { \"A\": \"...\", \"B\": \"...\", \"C\": \"...\", \"D\": \"...\" }"
            : "  \"wrongAnswerExplanations\": null";

        // ── Choice explanations (MCQ only) — full explanation for ALL choices ─
        String choiceExplField = isMcq
            ? "\n8. choiceExplanations: 1–2 sentence explanation for EVERY choice — why it is correct OR what trap it represents.\n" +
              "   { \"A\": \"...\", \"B\": \"...\", \"C\": \"...\", \"D\": \"...\" }\n" +
              "   - For the CORRECT choice: explain precisely WHY it is the right answer (not just 'Correct').\n" +
              "   - For each WRONG choice: explain the specific misconception or error that leads a student there.\n" +
              "   - Max 35 words per explanation. Plain English only — no LaTeX.\n"
            : "";

        String choiceExplSchemaLine = isMcq
            ? "  \"choiceExplanations\": { \"A\": \"...\", \"B\": \"...\", \"C\": \"...\", \"D\": \"...\" }"
            : "  \"choiceExplanations\": null";

        // ── Build the full prompt ──────────────────────────────────────────────
        return
            "You are an expert SAT educator and pedagogy specialist.\n" +
            "Your job: generate explanation content for a student who JUST GOT THIS QUESTION WRONG.\n\n" +

            "AUDIENCE: A student who answered incorrectly.\n" +
            "GOAL: After reading your explanation the student should:\n" +
            "  1. Understand exactly what mistake they likely made\n" +
            "  2. Know the correct approach step by step\n" +
            "  3. Recognise this question type and strategy in future\n\n" +

            "QUESTION:\n" + questionJson + "\n\n" +

            "═══════════════════════════════════════════════════════\n" +
            "HARD LIMITS — these are rules, not suggestions:\n" +
            "  explanationSteps : MAX " + maxSteps + " steps  (difficulty " + difficulty + "/7)\n" +
            "  Words per content : MAX " + maxWords + " words per step\n" +
            "  prerequisites    : MAX " + maxPrereqs + " topics\n" +
            "  Exceeding any limit = you are over-explaining. Combine steps, cut words.\n\n" +
            "  FORMULA LAW (enforced by validator — violation fails the whole enrichment):\n" +
            "  If ANY step content names a formula, that formula's LaTeX MUST be in the\n" +
            "  step's \"math\" field. This applies to EVERY named formula, no exceptions:\n" +
            "    quadratic formula     → math: \"x = \\\\frac{-b \\\\pm \\\\sqrt{b^2-4ac}}{2a}\"\n" +
            "    Pythagorean theorem   → math: \"a^2 + b^2 = c^2\"\n" +
            "    slope-intercept form  → math: \"y = mx + b\"\n" +
            "    distance formula      → math: \"d = \\\\sqrt{(x_2-x_1)^2+(y_2-y_1)^2}\"\n" +
            "    midpoint formula      → math: \"M = \\\\left(\\\\frac{x_1+x_2}{2}, \\\\frac{y_1+y_2}{2}\\\\right)\"\n" +
            "    law of sines          → math: \"\\\\frac{a}{\\\\sin A} = \\\\frac{b}{\\\\sin B}\"\n" +
            "    completing the square → show the completed form in math\n" +
            "    discriminant          → math: \"b^2 - 4ac\"\n" +
            "    vertex formula        → math: \"x = -\\\\frac{b}{2a}\"\n" +
            "  If you mention a formula by name without showing it → FAIL.\n" +
            "═══════════════════════════════════════════════════════\n\n" +

            "STEP WRITING RULES:\n" +
            "- Each step = exactly ONE logical operation. Never combine two operations in one step.\n" +
            "- Step title = imperative action verb: \"Apply\", \"Factor\", \"Substitute\", \"Verify\", \"Set up\", \"Identify\"\n" +
            "- Step content: explain WHY this step is necessary NOW, not just what to do\n" +
            "- Active voice only: \"Substitute x=2\" — not \"x=2 is substituted\"\n" +
            "- Start content with: \"When you see...\", \"Notice that...\", \"The key insight is...\", \"The trap here is...\"\n" +
            "- FORMULA RULE: see HARD LIMITS above — any named formula MUST appear in that step's \"math\" field.\n" +
            "- OBVIOUS TEST: if a step states something a difficulty-" + difficulty + " student already knows, remove it or merge it.\n" +
            "- At step limit with steps remaining? Combine the two simplest. Never exceed " + maxSteps + ".\n\n" +

            "LANGUAGE CALIBRATION (difficulty " + difficulty + "/7):\n" +
            diffCalibration + "\n\n" +

            "FORMATTING RULES:\n" +
            "- Plain text only in all content fields. No markdown: no **bold**, no *italic*, no `code`, no # headers.\n" +
            "- Numbers and answers go in plain text: write \"2\" not \"**2**\"\n\n" +

            "VISUAL REFERENCE RULE:\n" +
            "- NEVER mention visual concepts (graph, curve, intersect, coordinate plane, plot, slope, line) in step\n" +
            "  content UNLESS you have included a \"diagram\" field in that same step.\n" +
            "- If a question is about intersections or graphing but you cannot produce a diagram,\n" +
            "  rewrite the explanation using purely algebraic/numerical language instead.\n\n" +

            "PREREQUISITE RULES:\n" +
            "- List only concepts this student at difficulty " + difficulty + " might genuinely not know\n" +
            (difficulty >= 4
                ? "- Do NOT list: arithmetic, basic fractions, order of operations, basic algebra — student knows these\n"
                : "- Keep it to the single most important concept they need\n") +
            "- Each \"why\" must be specific to THIS question, not generic\n\n" +

            diagramInstruction + "\n\n" +

            "TRAP EXPLANATION RULES:\n" +
            "- Name the specific, memorable mistake — not a generic description\n" +
            "  GOOD: \"The trap is thinking you need polynomial long division. The Remainder Theorem makes this 10 seconds.\"\n" +
            "  BAD: \"Students may make computational errors.\"\n" +
            "- trapCategory must be exactly one of:\n" +
            "  sign_error | wrong_formula | misread_question | arithmetic | off_by_one |\n" +
            "  incomplete_setup | wrong_method | unit_error | algebra_manipulation\n\n" +

            "ALTERNATIVE APPROACH RULES:\n" +
            "- Must be genuinely different — a real methodological difference, not a rephrasing:\n" +
            "  VALID: formula-based vs. visual/geometric, substitution vs. elimination, algebraic vs. numeric\n" +
            "  INVALID: same method with slightly different arithmetic order, same formula rewritten\n" +
            ("geometry_trigonometry".equals(domain)
                ? "- For geometry, check these before returning null:\n" +
                  "  · distance/midpoint: distance formula vs. Pythagorean theorem on a drawn right triangle\n" +
                  "  · triangle sides/angles: law of cosines vs. decomposing into two right triangles\n" +
                  "  · coordinate geometry: algebraic (slope/equation) vs. classical geometric (angle/congruence) reasoning\n" +
                  "  · area: formula-based vs. coordinate/shoelace method\n" +
                  "  If none of these apply AND a different approach would just be a restatement, return null.\n"
                : "- Check these before returning null:\n" +
                  "  algebraic vs. numeric substitution, forward vs. backward solving, formula vs. first-principles\n" +
                  "  If no genuinely different method exists, return null.\n") +
            "- Apply the same step count and word count limits as explanationSteps\n\n" +

            "FIELDS TO GENERATE:\n" +
            "1. explanationSteps: array of max " + maxSteps + " steps — each: { \"title\", \"content\", \"math\", optionally \"diagram\" }\n" +
            "2. alternativeApproach: { \"title\", \"steps\" } — steps array max " + maxAltSteps + " steps (or null if genuinely no alternative exists)\n" +
            "3. coreConcept: { \"title\", \"summary\" (1-2 sentences), \"keyFormula\" (LaTeX or null) }\n" +
            "4. prerequisites: array of max " + maxPrereqs + " objects — each: { \"topic\", \"why\" }\n" +
            "5. animation: { \"eligible\": true/false } — true only for geometry/coordinate/transformation problems\n" +
            "6. pool: always \"both\"\n" +
            wrongAnswerField + "\n" +
            choiceExplField + "\n\n" +

            "Return ONLY this exact JSON shape — no markdown fences, no extra text:\n" +
            "{\n" +
            "  \"explanationSteps\": [...],\n" +
            "  \"alternativeApproach\": { \"title\": \"...\", \"steps\": [...] },\n" +
            "  \"coreConcept\": { \"title\": \"...\", \"summary\": \"...\", \"keyFormula\": \"...\" },\n" +
            "  \"prerequisites\": [...],\n" +
            "  \"animation\": { \"eligible\": false },\n" +
            "  \"pool\": \"both\",\n" +
            wrongAnswerSchemaLine + ",\n" +
            choiceExplSchemaLine + "\n" +
            "}";
    }
}
