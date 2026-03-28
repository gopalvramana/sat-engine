package com.satengine.domain.question;

import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;
import java.util.UUID;

public interface QuestionAnswerRepository extends JpaRepository<QuestionAnswer, UUID> {

    Optional<QuestionAnswer> findByQuestionId(UUID questionId);
}
