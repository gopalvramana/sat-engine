package com.satengine.pipeline.sympy;

import com.satengine.domain.sympy.SatQuestion;
import com.satengine.domain.sympy.SatQuestionRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.UUID;

/**
 * "Promotes" an approved sat_question to active delivery status.
 *
 * In the new architecture sat_questions IS the production table, so
 * promotion simply sets status → "promoted" and returns the same ID.
 * No cross-table copy is needed.
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class SymPyPromoteService {

    private final SatQuestionRepository satRepo;

    /**
     * Mark a sat_question as promoted (active for student delivery).
     *
     * @param satId the UUID of the sat_question to promote
     * @return the same UUID (sat_questions is the production table)
     * @throws IllegalStateException if question not found or already promoted
     */
    @Transactional
    public UUID promote(UUID satId) {
        SatQuestion sq = satRepo.findById(satId)
                .orElseThrow(() -> new IllegalStateException("Question not found: " + satId));

        if ("promoted".equals(sq.getStatus())) {
            throw new IllegalStateException("Question already promoted: " + satId);
        }

        sq.setStatus("promoted");
        satRepo.save(sq);

        log.info("Promoted {} (externalId={}) in sat_questions", satId, sq.getExternalId());
        return satId;
    }
}
