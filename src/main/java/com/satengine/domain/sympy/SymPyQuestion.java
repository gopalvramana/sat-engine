package com.satengine.domain.sympy;

import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.UUID;

@Entity
@Table(name = "sympy_questions")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class SymPyQuestion {

    @Id
    @GeneratedValue(strategy = GenerationType.AUTO)
    @Column(columnDefinition = "uuid", updatable = false, nullable = false)
    private UUID id;

    @Column(name = "external_id", unique = true, nullable = false, length = 20)
    private String externalId;

    @Column(name = "section", nullable = false, length = 20)
    private String section;

    @Column(name = "domain", nullable = false, length = 50)
    private String domain;

    @Column(name = "skill", length = 100)
    private String skill;

    @Column(name = "skill_key", length = 60)
    private String skillKey;

    @Column(name = "scenario_tag", length = 60)
    private String scenarioTag;

    @Column(name = "difficulty", nullable = false)
    private Short difficulty;

    @Column(name = "question_type", nullable = false, length = 5)
    private String questionType;

    @Column(name = "question_stem", nullable = false, columnDefinition = "TEXT")
    private String questionStem;

    @Column(name = "option_a", columnDefinition = "TEXT")
    private String optionA;

    @Column(name = "option_b", columnDefinition = "TEXT")
    private String optionB;

    @Column(name = "option_c", columnDefinition = "TEXT")
    private String optionC;

    @Column(name = "option_d", columnDefinition = "TEXT")
    private String optionD;

    @Column(name = "spr_min", precision = 10, scale = 4)
    private BigDecimal sprMin;

    @Column(name = "spr_max", precision = 10, scale = 4)
    private BigDecimal sprMax;

    @Column(name = "explanation_short", columnDefinition = "TEXT")
    private String explanationShort;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "explanation_steps", columnDefinition = "jsonb")
    private String explanationSteps;

    @Column(name = "pool", nullable = false, length = 20)
    @Builder.Default
    private String pool = "drill";

    @Column(name = "core_concept", columnDefinition = "TEXT")
    private String coreConcept;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "distractor_rationale", columnDefinition = "jsonb")
    private String distractorRationale;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "prerequisites", columnDefinition = "jsonb")
    private String prerequisites;

    @Column(name = "alternative_approach", columnDefinition = "TEXT")
    private String alternativeApproach;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "diagram", columnDefinition = "jsonb")
    private String diagram;

    @Column(name = "calculator_ok")
    @Builder.Default
    private Boolean calculatorOk = true;

    @Column(name = "source", length = 30)
    @Builder.Default
    private String source = "sympy_generated";

    @Column(name = "status", nullable = false, length = 30)
    @Builder.Default
    private String status = "generated";

    /** Raw MathObject JSON from math_engine.py — primary debugging surface */
    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "math_object", nullable = false, columnDefinition = "jsonb")
    private String mathObject;

    /** SHA-256 of parameter tuple — used for duplicate detection */
    @Column(name = "param_hash", length = 64)
    private String paramHash;

    /** Soft flag detail from Sonnet cross-verify, null when clean */
    @Column(name = "review_notes", columnDefinition = "TEXT")
    private String reviewNotes;

    @Column(name = "generated_at")
    private OffsetDateTime generatedAt;

    @Column(name = "created_at", updatable = false)
    private OffsetDateTime createdAt;

    @PrePersist
    protected void onCreate() {
        if (createdAt == null) createdAt = OffsetDateTime.now();
    }
}
