# 18 — Question Generation Pipeline Architecture

---

## Overview

The pipeline is a **6-stage CLI-driven process** that transforms a blank database into a fully enriched, pedagogically validated question bank. Each stage runs as an independent job via `--job=` flag. Stages are designed to be **idempotent** — you can re-run any stage safely.

---

## End-to-End Pipeline Flow

```mermaid
flowchart TD
    A([Start: java -jar sat-engine.jar --job=generate]) --> B

    subgraph S1["Stage 1 — Generate (Haiku 4.5)"]
        B[Load sat_taxonomy.json] --> C[Pick least-covered skill]
        C --> D[Pick most-underrepresented difficulty]
        D --> E["Build diversity context\nfetch all domain questions\nso Claude avoids duplicates"]
        E --> F["Call Claude Haiku\ntemp=0.8, max=4000"]
        F --> G{"Artifact check\nJaccard duplicate\ndiagram format"}
        G -->|"Fail, attempt < 2"| F
        G -->|Pass| H["Save Question + QuestionAnswer\nstatus: generated"]
    end

    H --> I

    subgraph S2["Stage 2 — Render Normalize"]
        I["Scan questions with status=generated"] --> J["Fix LaTeX delimiters\ndollar signs to backslash-paren"]
        J --> K[status stays: generated]
    end

    K --> L

    subgraph S3["Stage 3 — Agent Review (Opus 4.5)"]
        L[Load generated questions] --> M["Build slim question JSON\nstem + options + answer + diagram type"]
        M --> N["Call Claude Opus 4.5\nmax=1200"]
        N --> O["Receive: pass, confidence,\nsolvedAnswer, issues"]
        O --> P{"solvedAnswer\nvalid?"}
        P -->|"MCQ: A-D"| Q[Save QuestionReview]
        P -->|"SPR: numeric"| Q
        P -->|Invalid prose| R["pass=false\ncritical issue added"]
        R --> Q
        Q --> S[status: reviewed]
    end

    S --> T

    subgraph S4["Stage 4 — Enrich (Opus 4.6)"]
        T{"Math or\nReading+Writing?"}
        T -->|"Reading and Writing"| U["Skip enrichment\npool=both, status=enriched"]
        T -->|Math| V["Call Claude Opus 4.6\nmax=3500"]
        V --> W["Receive: explanationSteps,\nalternativeApproach, coreConcept,\nprerequisites, animation,\nchoiceExplanations"]
        W --> X{"Formula law\nvalidation"}
        X -->|"Formula named\nbut math field empty"| Y["Retry — max 2 attempts"]
        Y --> V
        X -->|Pass| Z["Apply all fields to Question\nstatus: enriched"]
        Z --> AA["Run animation backfill\nfor questions missing frames"]
    end

    AA --> AB

    subgraph S5["Stage 5 — Visual Check"]
        AB[Geometry questions only] --> AC{"Diagram\nvalid?"}
        AC -->|"Issues found + fix flag"| AD[Auto-patch fixable issues]
        AC -->|Pass| AE[Log OK]
    end

    AE --> AF

    subgraph S6["Stage 6 — Human Review (validate.html)"]
        AF["Admin opens validate.html"] --> AG["View question with\nfull rendering"]
        AG --> AH{Decision}
        AH -->|Approve| AI["status: approved\nquestion goes live"]
        AH -->|Reject| AJ["status: rejected\nnever served to students"]
    end

    AI --> AK([Question live in DB — served to students])
```

---

## Stage Details

### Stage 1 — Generate

**Entry point:** `GenerateStage.java`
**Model:** `claude-haiku-4-5-20251001` | temp: 0.8 | max_tokens: 4000

#### Skill & Difficulty Balancing

```mermaid
flowchart LR
    A[Load taxonomy\nskill list per domain] --> B[pickLeastCoveredSkill]
    B --> C[Query DB:\nSELECT skillKey, COUNT\nGROUP BY skillKey]
    C --> D[Pick skill with\nlowest count]
    D --> E[pickDifficultyForSkill]
    E --> F[Compare actual distribution\nvs DIFFICULTY_WEIGHTS target]
    F --> G[Pick most under-\nrepresented difficulty]
```

**Difficulty weight targets:**

| Mode | d1 | d2 | d3 | d4 | d5 | d6 | d7 |
|------|----|----|----|----|----|----|-----|
| DRILL (current) | 0 | 5 | 10 | 20 | 25 | 25 | 15 |
| TEST (planned #62) | 0 | 8 | 15 | 27 | 27 | 15 | 6 |
| DIAGNOSTIC (planned #62) | 0 | 0 | 25 | 50 | 25 | 0 | 0 |

#### Diagram Probability by Domain

| Domain | Has Diagram | Diagram Type |
|--------|-------------|--------------|
| geometry_trigonometry | 100% | svg_programmatic |
| problem_solving_data | 70% | chartjs (scatter/bar/histogram) |
| algebra | 25% | svg_programmatic (coordinate plane) |
| advanced_math | 20% | svg_programmatic |
| information_ideas | conditional | chartjs (command_evidence_quantitative only) |
| standard_english / craft_structure | 0% | — |

#### Duplicate Prevention

```mermaid
flowchart LR
    A[Generated question] --> B[buildDiversityContext\nfetch all non-rejected in domain]
    B --> C[Pass existing stems to Claude\nso it avoids duplicates]
    C --> D[isDuplicateStem check]
    D --> E[Jaccard word overlap\nthreshold: 0.85]
    E -->|overlap ≥ 0.85| F[Reject — retry]
    E -->|overlap < 0.85| G[Accept]
```

#### Artifact Detection

Rejects questions containing stream-of-consciousness phrases:
`"wait,"` · `"let me recalculate"` · `"actually,"` · `"hmm,"` · `"I need to"` · `"let me re-"` · `"oops"` · `"I made an error"` · `"let me redo"`

Rejected on attempt 1 and 2. Accepted on attempt 3 (final) if no other failures.

#### Question ID Format

```
MATH-ALG-031    →   section=math, domain=algebra, sequence=031
MATH-GEO-015    →   section=math, domain=geometry_trigonometry, sequence=015
RW-SE-008       →   section=reading_writing, domain=standard_english, sequence=008
```

---

### Stage 2 — Render Normalize

**Entry point:** `RenderNormalizeStage.java`
**Purpose:** Fix inconsistent LaTeX delimiters generated by Claude.

```mermaid
flowchart LR
    A["Input: dollar-sign x^2 + 1 dollar-sign"] --> B{Normalize}
    B --> C["Output: backslash-paren x^2 + 1 backslash-paren"]

    D["Input: double-dollar frac a b double-dollar"] --> E{Normalize}
    E --> F["Output: backslash-bracket frac a b backslash-bracket"]
```

Flags: `--all` (check all statuses), `--dry-run` (report without writing), `--id` (single question).

---

### Stage 3 — Agent Review

**Entry point:** `AgentReviewStage.java`
**Model:** `claude-opus-4-5` | max_tokens: 1200

#### Review Decision Tree

```mermaid
flowchart TD
    A[Question JSON\nstem + options + answer + explanation] --> B[Call Opus 4.5]
    B --> C[Receive: pass, confidence,\nsolvedAnswer, issues]
    C --> D{MCQ or SPR?}

    D -->|MCQ| E{solvedAnswer\nmatches A-D?}
    E -->|Yes| F{confidence\n≥ 0.85?}
    E -->|No — extract via regex| G{Extracted\nA-D found?}
    G -->|Yes| F
    G -->|No| H[solvedAnswer=null\npass=false\nSeverity: CRITICAL]

    D -->|SPR| I{solvedAnswer\nnumeric string?}
    I -->|Yes| F
    I -->|No — extract via regex| J{Number\nfound?}
    J -->|Yes| F
    J -->|No| K[solvedAnswer=null\npass=false\nSeverity: CRITICAL]

    F -->|≥ 0.85 + pass=true| L[Status: PASS\nSave QuestionReview]
    F -->|< 0.85 + pass=true| M[Status: WARN\nSave QuestionReview]
    F -->|pass=false| N[Status: FAIL\nSave QuestionReview]

    H --> N
    K --> N
    L --> O[status → reviewed]
    M --> O
    N --> O
```

**Issue severity levels:**

| Severity | Meaning | Example |
|----------|---------|---------|
| `critical` | Answer extraction failed or factually wrong | Invalid solvedAnswer format |
| `warning` | Borderline quality issue | Distractor too obviously wrong |
| `info` | Minor note | Phrasing could be clearer |

**CLI flags:**
```bash
--job=agent-review                          # Review all generated questions
--job=agent-review --only-failed            # Re-review pass=false questions
--job=agent-review --domain=algebra         # Filter by domain
--job=agent-review --section=math           # Filter by section
```

---

### Stage 4 — Enrich

**Entry point:** `EnrichStage.java`
**Model:** `claude-opus-4-6` (newest, highest capability) | max_tokens: 3500

#### Enrichment Decision Flow

```mermaid
flowchart TD
    A[Question with status=reviewed] --> B{Section?}

    B -->|reading_writing| C["Skip enrichment\npool=both, status=enriched\nLog: skipped Reading+Writing"]

    B -->|math| D[Call Opus 4.6\nwith question + domain + difficulty]
    D --> E[Receive full enrichment JSON]
    E --> F{explanationSteps\narray ≥ 2 items?}
    F -->|No| G[Retry — attempt 2]
    G --> D
    F -->|Yes| H{Formula law\ncheck}

    H --> I{Step mentions\nnamed formula?}
    I -->|No named formula| J[Pass]
    I -->|Yes — formula named| K{math field\npopulated?}
    K -->|Yes| J
    K -->|No — math empty| L[Retry — attempt 2]
    L --> D

    J --> M[Apply all fields to Question]
    M --> N[status=enriched]
    N --> O[Run AnimationBackfill\nfor questions missing frames]
```

**Formula law trigger keywords:** `quadratic formula` · `pythagorean theorem` · `law of sines` · `law of cosines` · `distance formula` · `midpoint formula` · `slope formula` · `standard form` · `vertex form` · `completing the square` · `FOIL` · `product rule` · `chain rule` · `power rule` · (25+ total)

#### Fields populated by Enrich stage

```mermaid
block-beta
    columns 3
    A["explanationSteps\nArray of {title,content,math}\nmin 2 steps"]:1
    B["alternativeApproach\n{title, steps[]}optional"]:1
    C["coreConcept\n{title, summary, keyFormula}"]:1
    D["prerequisites\nArray of {topic, why}"]:1
    E["animation\n{frames[]} — SVG animation JSON"]:1
    F["wrongAnswerExplanations\n{A:..., B:..., C:..., D:...}"]:1
    G["choiceExplanations\n{A:..., B:..., C:..., D:...}"]:1
    H["pool\ndefault: 'both'"]:1
```

**CLI flags:**
```bash
--job=enrich                         # Enrich all reviewed questions
--job=enrich --section=math          # Math only
--job=enrich --domain=algebra        # Domain filter
--job=enrich --include-approved      # Re-enrich already approved questions
--job=enrich --id=MATH-GEO-010       # Single question by externalId
```

---

### Stage 5 — Visual Check

**Entry point:** `VisualCheckStage.java`
**Scope:** Geometry questions only (domain=geometry_trigonometry)

Validates SVG diagram config — checks for missing required fields, invalid coordinates, out-of-bounds labels. With `--fix` flag, auto-patches known fixable issues (e.g., label coordinates outside viewbox).

---

### Stage 6 — Human Review (validate.html)

**Location:** `src/main/resources/static/admin/validate.html`

Admin UI served at `/admin/validate.html`. Renders each question with full KaTeX + SVG + Chart.js. Admin clicks Approve or Reject per question. Approved questions get `status=approved` and become live to students.

---

## PipelineRunner — CLI Routing

```mermaid
flowchart LR
    A[JVM start with --job=X] --> B[PipelineRunner.run]
    B --> C{--job value}
    C -->|generate| D[GenerateStage.run]
    C -->|agent-review| E[AgentReviewStage.run]
    C -->|enrich| F[EnrichStage.run + AnimationBackfill]
    C -->|visual-check| G[VisualCheckStage.run]
    C -->|render-normalize| H[RenderNormalizeStage.run]
    D --> Z[System.exit 0]
    E --> Z
    F --> Z
    G --> Z
    H --> Z
```

When `--job` flag is absent → `WebApplicationType.NONE` is NOT set → Spring Boot starts normally as a web server.

---

## Claude Client Architecture

```mermaid
flowchart TD
    A[ClaudeClient @PostConstruct init] --> B[Search for .env file\nin candidate directories]
    B --> C[./\nsat-engine/\n../sat-engine/\nJAR parent dir]
    C --> D[Extract ANTHROPIC_API_KEY]
    D --> E[Create AnthropicOkHttpClient]

    F[Pipeline Stage calls claude.call] --> G{Temperature\nprovided?}
    G -->|Yes| H[MessageCreateParams\nwith temperature]
    G -->|No| I[MessageCreateParams\ndefault temperature]
    H --> J[client.messages.create — sync]
    I --> J
    J --> K[Return text content\nof first response block]
```

**Model assignments by stage:**

| Stage | Model | Reason |
|-------|-------|--------|
| GenerateStage | `claude-haiku-4-5-20251001` | High volume, cost-sensitive |
| AgentReviewStage | `claude-opus-4-5` | Answer validation needs accuracy |
| EnrichStage | `claude-opus-4-6` | Complex pedagogical content |
| GapAnalysisService | `claude-haiku-4-5` | Real-time, latency-sensitive |

---

## PromptLibrary — Prompt Overview

```mermaid
mindmap
  root((PromptLibrary))
    Generate
      GENERATE_SYSTEM_MATH
        LaTeX rules inline and display mode
        Table rules HTML only
        Verify answers before writing
        No stream-of-consciousness
      GENERATE_SYSTEM_RandW
        Passage-based domains
        Sentence-level for Standard English
        Answer must be unambiguous
      buildGenerateUserPrompt
        section domain skill difficulty
        questionType MCQ or SPR
        hasDiagram + diagramType
        diversityContext existing stems
        targetLetter optional forced answer
    Review
      buildReviewPrompt
        questionJson + section + questionType
        Validate answer correctness
        Check explanation logic
        Return pass confidence solvedAnswer issues
    Enrich
      buildEnrichPrompt
        Full question + section + domain + difficulty
        Return explanationSteps alternativeApproach
        coreConcept prerequisites animation
        wrongAnswerExplanations choiceExplanations
```

---

## Question Status State Machine

```mermaid
stateDiagram-v2
    [*] --> generated: GenerateStage saves\nnew question

    generated --> generated: RenderNormalizeStage\nfixes LaTeX delimiters

    generated --> reviewed: AgentReviewStage\nsaves QuestionReview\n(pass or fail — both advance)

    reviewed --> reviewed: AgentReviewStage only-failed\nre-reviews failed questions

    reviewed --> enriched: EnrichStage adds\npedagogical content

    enriched --> enriched: AnimationBackfill adds\nmissing animation frames

    enriched --> approved: Human approves\nin validate.html\nLIVE TO STUDENTS

    enriched --> rejected: Human rejects\nin validate.html\nNEVER SERVED

    approved --> enriched: EnrichStage include-approved\nre-enriches if needed

    approved --> rejected: Human re-rejects\nafter approval

    rejected --> [*]
    approved --> [*]: Served to students
```

---

## Database Tables — Pipeline Writes

```mermaid
erDiagram
    questions {
        UUID id PK
        VARCHAR external_id UK
        VARCHAR section
        VARCHAR domain
        VARCHAR skill
        VARCHAR skill_key
        VARCHAR scenario_tag
        SMALLINT difficulty
        VARCHAR question_type
        TEXT question_stem
        TEXT option_a
        TEXT option_b
        TEXT option_c
        TEXT option_d
        NUMERIC spr_min
        NUMERIC spr_max
        TEXT explanation_short
        JSONB explanation_steps
        VARCHAR trap_category
        TEXT trap_explanation
        JSONB core_concept
        JSONB prerequisites
        JSONB animation
        JSONB alternative_approach
        JSONB wrong_answer_explanations
        JSONB choice_explanations
        VARCHAR pool
        TEXT passage_text
        TEXT passage_source
        JSONB diagram
        BOOLEAN calculator_ok
        VARCHAR source
        VARCHAR status
        TIMESTAMPTZ generated_at
        TIMESTAMPTZ created_at
        vector embedding
    }

    question_answers {
        UUID id PK
        UUID question_id FK
        VARCHAR correct_answer
    }

    question_reviews {
        UUID id PK
        UUID question_id FK
        BOOLEAN pass
        NUMERIC confidence
        VARCHAR solved_answer
        JSONB issues
        TEXT notes
        VARCHAR model
        TIMESTAMPTZ checked_at
    }

    questions ||--|| question_answers : "1-to-1\ncorrectAnswer stored separately"
    questions ||--|| question_reviews : "1-to-1\ncreated by AgentReview"
```

---

## Pipeline Stage × Field Responsibility Matrix

| Field | Generate | Render-Normalize | Agent Review | Enrich | Human Review |
|-------|----------|-----------------|--------------|--------|--------------|
| `externalId` | ✅ | — | — | — | — |
| `section / domain / skill / skillKey` | ✅ | — | — | — | — |
| `difficulty / questionType` | ✅ | — | — | — | — |
| `questionStem / optionA-D` | ✅ | ✅ fixes | — | — | — |
| `explanationShort` | ✅ | — | — | — | — |
| `diagram` | ✅ | — | — | — | — |
| `scenarioTag / calculatorOk` | ✅ | — | — | — | — |
| `pool` | ✅ default=both | — | — | ✅ may update | — |
| `status` | ✅ generated | — | ✅ reviewed | ✅ enriched | ✅ approved/rejected |
| `question_answers.correct_answer` | ✅ | — | — | — | — |
| `question_reviews.*` | — | — | ✅ all fields | — | — |
| `explanationSteps` | — | — | — | ✅ | — |
| `alternativeApproach` | — | — | — | ✅ | — |
| `coreConcept` | — | — | — | ✅ | — |
| `prerequisites` | — | — | — | ✅ | — |
| `animation` | — | — | — | ✅ | — |
| `wrongAnswerExplanations` | — | — | — | ✅ | — |
| `choiceExplanations` | — | — | — | ✅ | — |
| `trapCategory / trapExplanation` | — | — | — | *(planned)* | — |
