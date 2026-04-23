package com.satengine.dto;

import com.fasterxml.jackson.annotation.JsonRawValue;
import lombok.*;

import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.UUID;

@Data @Builder @NoArgsConstructor @AllArgsConstructor
public class SymPyQuestionResponse {
    private UUID          id;
    private String        externalId;
    private String        status;
    private String        section;
    private String        domain;
    private String        skill;
    private String        skillKey;
    private String        scenarioTag;
    private short         difficulty;
    private String        questionType;
    private String        questionStem;
    private String        optionA;
    private String        optionB;
    private String        optionC;
    private String        optionD;
    private String        correctAnswer;   // from sympy_question_answers
    private BigDecimal    sprMin;
    private BigDecimal    sprMax;
    private String        explanationShort;
    @JsonRawValue private String explanationSteps;
    private String        coreConcept;
    @JsonRawValue private String distractorRationale;
    @JsonRawValue private String prerequisites;
    private String        alternativeApproach;
    @JsonRawValue private String diagram;
    @JsonRawValue private String mathObject;   // raw Python output — debug panel
    private String        paramHash;
    private String        reviewNotes;         // Sonnet flag detail
    private String        pool;
    private OffsetDateTime generatedAt;
}
