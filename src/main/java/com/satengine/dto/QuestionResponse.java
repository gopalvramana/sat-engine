package com.satengine.dto;

import com.satengine.domain.sympy.SatQuestion;

import java.math.BigDecimal;
import java.util.UUID;

/**
 * Public-facing question DTO — never includes the correct answer.
 */
public record QuestionResponse(
        UUID id,
        String externalId,
        String section,
        String domain,
        String skill,
        Short difficulty,
        String questionType,
        String questionStem,
        String optionA,
        String optionB,
        String optionC,
        String optionD,
        BigDecimal sprMin,
        BigDecimal sprMax,
        String explanationShort,
        String explanationSteps,
        String trapCategory,
        String trapExplanation,
        String coreConceptJson,
        String prerequisitesJson,
        String animationJson,
        String choiceExplanations,
        String alternativeApproach,
        String pool,
        String passageText,
        String passageSource,
        String diagramJson,
        Boolean calculatorOk,
        String skillKey
) {

    /**
     * Factory method — maps from a SatQuestion entity, omitting the correct answer.
     * sprMin/sprMax are stored as numbers in content JSONB and parsed to BigDecimal.
     */
    public static QuestionResponse from(SatQuestion sq) {
        BigDecimal sprMin = null, sprMax = null;
        try { String s = sq.getSprMinStr(); if (s != null) sprMin = new BigDecimal(s); } catch (Exception ignored) {}
        try { String s = sq.getSprMaxStr(); if (s != null) sprMax = new BigDecimal(s); } catch (Exception ignored) {}
        return new QuestionResponse(
                sq.getId(),
                sq.getExternalId(),
                sq.getSection(),
                sq.getDomain(),
                sq.getSkillKey(),       // skill display = skillKey for sympy questions
                sq.getDifficulty(),
                sq.getQuestionType(),
                sq.getQuestionStem(),
                sq.getOptionA(),
                sq.getOptionB(),
                sq.getOptionC(),
                sq.getOptionD(),
                sprMin,
                sprMax,
                sq.getExplanationShort(),
                sq.getRawExplanationSteps(),
                null,                   // trapCategory — not in sympy questions
                null,                   // trapExplanation — not in sympy questions
                sq.getCoreConcept(),
                sq.getRawPrerequisites(),
                null,                   // animationJson — not in sympy questions
                null,                   // choiceExplanations — not in sympy questions
                sq.getAlternativeApproach(),
                sq.getPool(),
                null,                   // passageText — math only
                null,                   // passageSource — math only
                sq.getRawDiagram(),
                true,                   // calculatorOk — math section default
                sq.getSkillKey()
        );
    }

}
