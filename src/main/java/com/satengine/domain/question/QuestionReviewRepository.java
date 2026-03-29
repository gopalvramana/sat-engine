package com.satengine.domain.question;

import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;
import java.util.UUID;

public interface QuestionReviewRepository extends JpaRepository<QuestionReview, UUID> {
    Optional<QuestionReview> findByQuestionId(UUID questionId);

    Optional<QuestionReview> findByQuestion(Question question);
}
