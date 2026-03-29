package com.satengine.api.admin;

import com.satengine.domain.question.*;
import com.satengine.dto.AdminQuestionResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class AdminQuestionService {

    private final QuestionRepository       questionRepository;
    private final QuestionAnswerRepository questionAnswerRepository;
    private final QuestionReviewRepository questionReviewRepository;

    public List<AdminQuestionResponse> getByStatus(String status) {
        List<Question> questions = "all".equalsIgnoreCase(status)
                ? questionRepository.findAll()
                : questionRepository.findByStatus(status);
        return questions.stream().map(this::toResponse).toList();
    }

    @Transactional
    public void approve(UUID id) {
        Question q = findOrThrow(id);
        q.setStatus("approved");
        questionRepository.save(q);
    }

    @Transactional
    public void reject(UUID id) {
        Question q = findOrThrow(id);
        q.setStatus("rejected");
        questionRepository.save(q);
    }

    @Transactional
    public void revertToPending(UUID id) {
        Question q = findOrThrow(id);
        q.setStatus("enriched");
        questionRepository.save(q);
    }

    @Transactional
    public void fixAnswer(UUID id, String newAnswer) {
        Question q = findOrThrow(id);
        // Update correct answer
        QuestionAnswer qa = questionAnswerRepository.findByQuestionId(id)
                .orElse(QuestionAnswer.builder().question(q).build());
        qa.setCorrectAnswer(newAnswer.toUpperCase());
        questionAnswerRepository.save(qa);
        // Auto-approve after fix
        q.setStatus("approved");
        questionRepository.save(q);
    }

    @Transactional
    public void updatePool(UUID id, String pool) {
        Question q = findOrThrow(id);
        q.setPool(pool);
        questionRepository.save(q);
    }

    private Question findOrThrow(UUID id) {
        return questionRepository.findById(id)
                .orElseThrow(() -> new IllegalArgumentException("Question not found: " + id));
    }

    private AdminQuestionResponse toResponse(Question q) {
        String correctAnswer = questionAnswerRepository.findByQuestionId(q.getId())
                .map(QuestionAnswer::getCorrectAnswer)
                .orElse(null);

        AdminQuestionResponse.AgentReviewSummary review = questionReviewRepository
                .findByQuestion(q)
                .map(r -> AdminQuestionResponse.AgentReviewSummary.builder()
                        .pass(r.getPass())
                        .confidence(r.getConfidence() != null ? r.getConfidence().doubleValue() : null)
                        .solvedAnswer(r.getSolvedAnswer())
                        .issues(r.getIssues())
                        .notes(r.getNotes())
                        .build())
                .orElse(null);

        return AdminQuestionResponse.builder()
                .id(q.getId())
                .externalId(q.getExternalId())
                .status(q.getStatus())
                .section(q.getSection())
                .domain(q.getDomain())
                .skill(q.getSkill())
                .difficulty(q.getDifficulty())
                .explanationShort(q.getExplanationShort())
                .explanationSteps(q.getExplanationSteps())
                .trapCategory(q.getTrapCategory())
                .trapExplanation(q.getTrapExplanation())
                .coreConcept(q.getCoreConcept())
                .prerequisites(q.getPrerequisites())
                .animation(q.getAnimation())
                .diagram(q.getDiagram())
                .pool(q.getPool())
                .passageText(q.getPassageText())
                .questionType(q.getQuestionType())
                .questionStem(q.getQuestionStem())
                .optionA(q.getOptionA())
                .optionB(q.getOptionB())
                .optionC(q.getOptionC())
                .optionD(q.getOptionD())
                .correctAnswer(correctAnswer)
                .agentReview(review)
                .build();
    }
}
