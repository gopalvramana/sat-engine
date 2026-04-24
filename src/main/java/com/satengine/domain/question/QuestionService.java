package com.satengine.domain.question;

import com.satengine.domain.sympy.SatQuestion;
import com.satengine.domain.sympy.SatQuestionRepository;
import com.satengine.dto.QuestionResponse;
import com.satengine.exception.ResourceNotFoundException;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.UUID;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class QuestionService {

    private final SatQuestionRepository satQuestionRepository;

    /**
     * Retrieve a single question by ID (no correct answer in response).
     */
    public QuestionResponse getQuestion(UUID id) {
        SatQuestion question = satQuestionRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Question", id));
        return QuestionResponse.from(question);
    }

    /**
     * Count approved questions per domain broken down by difficulty band.
     * Used by the session builder UI (/api/questions/count).
     * Returns rows: [domain, easy, medium, hard, total]
     */
    public List<Object[]> getCountsByDomain(String section) {
        return satQuestionRepository.countByDomainAndDifficulty(section);
    }

    /**
     * Retrieve a filtered list of approved questions.
     * All parameters are optional — null means "no filter on that field".
     */
    public List<QuestionResponse> getQuestions(String section, String domain, Integer difficulty) {
        Short diff = difficulty != null ? difficulty.shortValue() : null;

        List<SatQuestion> questions;

        if (section != null && domain != null && diff != null) {
            questions = satQuestionRepository.findByStatusAndSectionAndDomainAndDifficulty(
                    "approved", section, domain, diff);
        } else if (section != null && domain != null) {
            questions = satQuestionRepository.findByStatusAndSectionAndDomain(
                    "approved", section, domain);
        } else if (section != null && diff != null) {
            questions = satQuestionRepository.findByStatusAndSectionAndDifficulty(
                    "approved", section, diff);
        } else if (domain != null && diff != null) {
            questions = satQuestionRepository.findByStatusAndDomainAndDifficulty(
                    "approved", domain, diff);
        } else if (section != null) {
            questions = satQuestionRepository.findByStatusAndSection("approved", section);
        } else if (diff != null) {
            questions = satQuestionRepository.findByStatusAndDifficulty("approved", diff);
        } else {
            questions = satQuestionRepository.findByStatus("approved");
        }

        return questions.stream()
                .map(QuestionResponse::from)
                .toList();
    }
}
