package com.satengine.domain.sympy;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

import java.time.OffsetDateTime;
import java.util.UUID;

/**
 * Consolidated question entity for sat_questions.
 *
 * Replaces the two-table sympy_questions + sympy_question_answers design.
 * All question content (stem, options, explanation, diagram, mathObject) lives
 * in the {@code content} JSONB column. Convenience accessor methods parse it
 * lazily so calling code never has to touch Jackson directly.
 *
 * Flat indexed columns (template, variant, skill_key, difficulty, status, domain,
 * pool, correct_answer) are first-class for session queries — no JSONB parsing needed
 * on the hot path.
 */
@Entity
@Table(name = "sat_questions")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class SatQuestion {

    private static final ObjectMapper _MAPPER = new ObjectMapper();

    @Id
    @GeneratedValue(strategy = GenerationType.AUTO)
    @Column(columnDefinition = "uuid", updatable = false, nullable = false)
    private UUID id;

    @Column(name = "external_id", unique = true, nullable = false, length = 20)
    private String externalId;

    @Column(name = "skill_key", nullable = false, length = 60)
    private String skillKey;

    /** Template name — first-class column for diversity queries. */
    @Column(name = "template", length = 60)
    private String template;

    /** Variant name — first-class column for diversity queries. */
    @Column(name = "variant", length = 60)
    private String variant;

    @Column(name = "difficulty", nullable = false)
    private Short difficulty;

    @Column(name = "question_type", nullable = false, length = 5)
    private String questionType;

    @Column(name = "section", nullable = false, length = 20)
    private String section;

    @Column(name = "domain", nullable = false, length = 50)
    private String domain;

    @Column(name = "pool", nullable = false, length = 20)
    @Builder.Default
    private String pool = "drill";

    @Column(name = "status", nullable = false, length = 30)
    @Builder.Default
    private String status = "generated";

    /** Correct answer — flat column for O(1) answer checking. */
    @Column(name = "correct_answer", columnDefinition = "TEXT")
    private String correctAnswer;

    @Column(name = "param_hash", length = 64)
    private String paramHash;

    @Column(name = "scenario_tag", length = 60)
    private String scenarioTag;

    @Column(name = "review_notes", columnDefinition = "TEXT")
    private String reviewNotes;

    @Column(name = "generated_at")
    private OffsetDateTime generatedAt;

    @Column(name = "created_at", updatable = false)
    private OffsetDateTime createdAt;

    /**
     * All question content in one JSONB blob:
     * questionStem, optionA–D, correctLetter, sprMin, sprMax,
     * explanationShort, explanationSteps, coreConcept, distractorRationale,
     * prerequisites, alternativeApproach, diagram, mathObject.
     */
    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "content", columnDefinition = "jsonb", nullable = false)
    private String content;

    @PrePersist
    protected void onCreate() {
        if (createdAt == null) createdAt = OffsetDateTime.now();
    }

    // ── Lazy content node ─────────────────────────────────────────────────

    @Transient
    private transient JsonNode _contentNode;

    private JsonNode contentNode() {
        if (_contentNode == null) {
            try {
                _contentNode = _MAPPER.readTree(content != null ? content : "{}");
            } catch (Exception e) {
                _contentNode = _MAPPER.createObjectNode();
            }
        }
        return _contentNode;
    }

    // ── Plain-text content accessors ──────────────────────────────────────

    public String getQuestionStem()        { return txt("questionStem"); }
    public String getOptionA()             { return txt("optionA"); }
    public String getOptionB()             { return txt("optionB"); }
    public String getOptionC()             { return txt("optionC"); }
    public String getOptionD()             { return txt("optionD"); }
    public String getExplanationShort()    { return txt("explanationShort"); }
    public String getCoreConcept()         { return txt("coreConcept"); }
    public String getAlternativeApproach() { return txt("alternativeApproach"); }

    /** sprMin stored in content as a number; returned as String for SPR bounds. */
    public String getSprMinStr() {
        JsonNode n = contentNode().path("sprMin");
        return (n.isMissingNode() || n.isNull()) ? null : n.asText();
    }

    /** sprMax stored in content as a number; returned as String for SPR bounds. */
    public String getSprMaxStr() {
        JsonNode n = contentNode().path("sprMax");
        return (n.isMissingNode() || n.isNull()) ? null : n.asText();
    }

    // ── Raw-JSON accessors (for @JsonRawValue fields in response DTOs) ────
    // These return the field serialised as a JSON string so @JsonRawValue
    // emits it verbatim without double-encoding.

    public String getRawExplanationSteps()    { return rawJson("explanationSteps"); }
    public String getRawDistractorRationale() { return rawJson("distractorRationale"); }
    public String getRawCoreConcept()         { return rawJson("coreConcept"); }
    public String getRawPrerequisites()       { return rawJson("prerequisites"); }
    public String getRawDiagram()             { return rawJson("diagram"); }
    public String getRawMathObject()          { return rawJson("mathObject"); }

    // ── Private helpers ───────────────────────────────────────────────────

    private String txt(String field) {
        String v = contentNode().path(field).asText(null);
        return "null".equals(v) ? null : v;
    }

    private String rawJson(String field) {
        JsonNode n = contentNode().path(field);
        if (n.isMissingNode() || n.isNull()) return null;
        return n.toString();
    }
}
