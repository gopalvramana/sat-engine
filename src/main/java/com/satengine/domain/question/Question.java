package com.satengine.domain.question;

import com.satengine.pipeline.QuestionStatus;
import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.UUID;

@Entity
@Table(name = "questions")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Question {

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

    /** Canonical slug from sat_taxonomy.json — e.g. "linear_eq_one_var", "pythagorean_theorem" */
    @Column(name = "skill_key", length = 60)
    private String skillKey;

    /** Real-world scenario type — e.g. "projectile_motion", "rectangle_area", "revenue_model".
     *  Injected at generation time to prevent duplicate scenarios within the same skill. */
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

    @Column(name = "trap_category", length = 30)
    private String trapCategory;

    @Column(name = "trap_explanation", columnDefinition = "TEXT")
    private String trapExplanation;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "core_concept", columnDefinition = "jsonb")
    private String coreConcept;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "prerequisites", columnDefinition = "jsonb")
    private String prerequisites;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "animation", columnDefinition = "jsonb")
    private String animation;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "alternative_approach", columnDefinition = "jsonb")
    private String alternativeApproach;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "wrong_answer_explanations", columnDefinition = "jsonb")
    private String wrongAnswerExplanations;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "choice_explanations", columnDefinition = "jsonb")
    private String choiceExplanations;

    @Column(name = "pool", nullable = false, length = 10)
    @Builder.Default
    private String pool = "both";

    @Column(name = "passage_text", columnDefinition = "TEXT")
    private String passageText;

    @Column(name = "passage_source", columnDefinition = "TEXT")
    private String passageSource;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "diagram", columnDefinition = "jsonb")
    private String diagram;

    @Column(name = "calculator_ok")
    @Builder.Default
    private Boolean calculatorOk = true;

    @Column(name = "source", length = 20)
    @Builder.Default
    private String source = "ai_generated";

    @Column(name = "status", nullable = false, length = 20)
    @Builder.Default
    private String status = QuestionStatus.GENERATED.lower();

    @Column(name = "generated_at")
    private OffsetDateTime generatedAt;

    @Column(name = "created_at", updatable = false)
    private OffsetDateTime createdAt;

    // embedding is stored as vector(1536) in DB — managed via native SQL when similarity search is implemented
    @Transient
    private float[] embedding;

    @PrePersist
    protected void onCreate() {
        if (createdAt == null) {
            createdAt = OffsetDateTime.now();
        }
    }
}
