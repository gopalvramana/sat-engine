package com.satengine.domain.question;

import com.satengine.dto.QuestionResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.UUID;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class QuestionService {

    private final QuestionRepository questionRepository;

    /**
     * Retrieve a single question by ID (no correct answer in response).
     */
    public QuestionResponse getQuestion(UUID id) {
        Question question = questionRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Question not found: " + id));
        return QuestionResponse.from(question);
    }

    /**
     * Count questions per domain for the session builder.
     */
    public List<Object[]> getCountsByDomain(String section, int minDifficulty, int maxDifficulty) {
        return questionRepository.countByDomainFiltered(section, minDifficulty, maxDifficulty);
    }

    /**
     * Retrieve a filtered list of questions.
     * All parameters are optional — null means "no filter on that field".
     */
    public List<QuestionResponse> getQuestions(String section, String domain, Integer difficulty) {
        List<Question> questions;

        Short diff = difficulty != null ? difficulty.shortValue() : null;

        if (section != null && domain != null && diff != null) {
            questions = questionRepository.findBySectionAndDomainAndDifficulty(section, domain, diff);
        } else if (section != null && domain != null) {
            questions = questionRepository.findBySectionAndDomain(section, domain);
        } else if (section != null && diff != null) {
            questions = questionRepository.findBySectionAndDifficulty(section, diff);
        } else if (domain != null && diff != null) {
            questions = questionRepository.findByDomainAndDifficulty(domain, diff);
        } else if (section != null) {
            questions = questionRepository.findBySection(section);
        } else if (diff != null) {
            questions = questionRepository.findByDifficulty(diff);
        } else {
            questions = questionRepository.findAll();
        }

        return questions.stream()
                .map(QuestionResponse::from)
                .toList();
    }
}
