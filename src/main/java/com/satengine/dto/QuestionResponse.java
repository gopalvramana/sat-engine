package com.satengine.dto;

import com.satengine.domain.question.Question;

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
     * Factory method — maps from the Question entity, omitting the correct answer.
     */
    public static QuestionResponse from(Question q) {
        return new QuestionResponse(
                q.getId(),
                q.getExternalId(),
                q.getSection(),
                q.getDomain(),
                q.getSkill(),
                q.getDifficulty(),
                q.getQuestionType(),
                q.getQuestionStem(),
                q.getOptionA(),
                q.getOptionB(),
                q.getOptionC(),
                q.getOptionD(),
                q.getSprMin(),
                q.getSprMax(),
                q.getExplanationShort(),
                q.getExplanationSteps(),
                q.getTrapCategory(),
                q.getTrapExplanation(),
                q.getCoreConcept(),
                q.getPrerequisites(),
                q.getAnimation(),
                q.getChoiceExplanations(),
                q.getAlternativeApproach(),
                q.getPool(),
                q.getPassageText(),
                q.getPassageSource(),
                q.getDiagram(),
                q.getCalculatorOk(),
                q.getSkillKey()
        );
    }
}
