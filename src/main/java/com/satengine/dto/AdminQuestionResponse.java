package com.satengine.dto;

import com.fasterxml.jackson.annotation.JsonRawValue;
import lombok.*;
import java.math.BigDecimal;
import java.util.UUID;

@Data @Builder @NoArgsConstructor @AllArgsConstructor
public class AdminQuestionResponse {
    private UUID   id;
    private String externalId;
    private String status;
    private String section;
    private String domain;
    private String skill;
    /** Canonical slug from sat_taxonomy.json — exact match for coverage tracking */
    private String skillKey;
    /** Real-world scenario type — e.g. projectile_motion, rectangle_area */
    private String scenarioTag;
    private short  difficulty;
    private String questionType;
    private String questionStem;
    private String optionA;
    private String optionB;
    private String optionC;
    private String optionD;
    private String correctAnswer;      // from question_answers
    private BigDecimal sprMin;
    private BigDecimal sprMax;
    private String explanationShort;
    @JsonRawValue private String explanationSteps;  // raw JSONB → pass through as JSON
    private String trapCategory;
    private String trapExplanation;
    @JsonRawValue private String coreConcept;
    @JsonRawValue private String prerequisites;
    @JsonRawValue private String animation;
    @JsonRawValue private String alternativeApproach;
    @JsonRawValue private String wrongAnswerExplanations;
    @JsonRawValue private String choiceExplanations;
    @JsonRawValue private String diagram;
    private String pool;
    private String passageText;
    private AgentReviewSummary agentReview;  // nullable

    @Data @Builder @NoArgsConstructor @AllArgsConstructor
    public static class AgentReviewSummary {
        private Boolean pass;
        private Double  confidence;
        private String  solvedAnswer;
        @JsonRawValue private String issues;   // raw JSONB
        private String  notes;
    }
}
