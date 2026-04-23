package com.satengine.pipeline.sympy;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.satengine.domain.question.Question;
import com.satengine.domain.question.QuestionAnswer;
import com.satengine.domain.question.QuestionAnswerRepository;
import com.satengine.domain.question.QuestionRepository;
import com.satengine.domain.sympy.SymPyQuestion;
import com.satengine.domain.sympy.SymPyQuestionAnswer;
import com.satengine.domain.sympy.SymPyQuestionAnswerRepository;
import com.satengine.domain.sympy.SymPyQuestionRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/**
 * Promotes an approved sympy_question into the production questions table.
 *
 * SymPy-specific fields (mathObject, paramHash, reviewNotes) stay in sympy_questions.
 * The promoted question gets source="sympy_generated" and animation=null (animations dropped).
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class SymPyPromoteService {

    private final SymPyQuestionRepository       sympyRepo;
    private final SymPyQuestionAnswerRepository sympyAnswerRepo;
    private final QuestionRepository            questionRepo;
    private final QuestionAnswerRepository      questionAnswerRepo;
    private final ObjectMapper                  objectMapper;

    /**
     * Promote a single sympy_question to the production questions table.
     *
     * @param sympyId the UUID of the sympy_question to promote
     * @return the UUID of the newly created production question
     * @throws IllegalStateException if question not found or already promoted
     */
    @Transactional
    public UUID promote(UUID sympyId) {
        SymPyQuestion sq = sympyRepo.findById(sympyId)
                .orElseThrow(() -> new IllegalStateException("SymPy question not found: " + sympyId));

        if ("promoted".equals(sq.getStatus())) {
            throw new IllegalStateException("Question already promoted: " + sympyId);
        }

        // Map sympy_question → production Question
        Question q = Question.builder()
                .externalId(sq.getExternalId())
                .section(sq.getSection())
                .domain(sq.getDomain())
                .skill(sq.getSkill())
                .skillKey(sq.getSkillKey())
                .scenarioTag(sq.getScenarioTag())
                .difficulty(sq.getDifficulty())
                .questionType(sq.getQuestionType())
                .questionStem(sq.getQuestionStem())
                .optionA(sq.getOptionA())
                .optionB(sq.getOptionB())
                .optionC(sq.getOptionC())
                .optionD(sq.getOptionD())
                .sprMin(sq.getSprMin())
                .sprMax(sq.getSprMax())
                .explanationShort(sq.getExplanationShort())
                .explanationSteps(sq.getExplanationSteps())
                .coreConcept(wrapCoreConcept(sq.getCoreConcept()))
                .prerequisites(sq.getPrerequisites())
                .alternativeApproach(wrapAltApproach(sq.getAlternativeApproach()))
                .wrongAnswerExplanations(sq.getDistractorRationale())
                .diagram(sq.getDiagram())
                .pool(sq.getPool())
                .calculatorOk(sq.getCalculatorOk())
                .source("sympy_generated")
                .status("approved")
                .generatedAt(sq.getGeneratedAt())
                .build();

        questionRepo.save(q);

        // Copy correct answer — mandatory; fail loudly if missing
        SymPyQuestionAnswer sa = sympyAnswerRepo.findByQuestionId(sympyId)
                .orElseThrow(() -> new IllegalStateException(
                        "No answer found for sympy question: " + sympyId));
        QuestionAnswer qa = QuestionAnswer.builder()
                .question(q)
                .correctAnswer(sa.getCorrectAnswer())
                .build();
        questionAnswerRepo.save(qa);

        // Mark sympy_question as promoted
        sq.setStatus("promoted");
        sympyRepo.save(sq);

        log.info("Promoted {} → questions table as {}", sq.getExternalId(), q.getId());
        return q.getId();
    }

    // ── Helpers ───────────────────────────────────────────────────────────────

    /**
     * sympy_questions stores coreConcept as a plain TEXT sentence.
     * questions.core_concept is JSONB and the frontend expects {title, summary, keyFormula}.
     */
    private String wrapCoreConcept(String text) {
        if (text == null || text.isBlank()) return null;
        try {
            Map<String, Object> obj = new LinkedHashMap<>();
            obj.put("title",      text.trim());
            obj.put("summary",    null);
            obj.put("keyFormula", null);
            return objectMapper.writeValueAsString(obj);
        } catch (Exception e) {
            log.warn("Failed to wrap coreConcept: {}", e.getMessage());
            return null;
        }
    }

    /**
     * sympy_questions stores alternativeApproach as a plain TEXT paragraph.
     * questions.alternative_approach is JSONB and the frontend expects {title, steps[]}.
     */
    private String wrapAltApproach(String text) {
        if (text == null || text.isBlank()) return null;
        try {
            Map<String, Object> step = new LinkedHashMap<>();
            step.put("title",   "Alternative Approach");
            step.put("content", text.trim());
            Map<String, Object> obj = new LinkedHashMap<>();
            obj.put("title", "Alternative Method");
            obj.put("steps", List.of(step));
            return objectMapper.writeValueAsString(obj);
        } catch (Exception e) {
            log.warn("Failed to wrap alternativeApproach: {}", e.getMessage());
            return null;
        }
    }
}
