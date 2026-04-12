package com.satengine.domain.question;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

public interface QuestionAnswerRepository extends JpaRepository<QuestionAnswer, UUID> {

    Optional<QuestionAnswer> findByQuestionId(UUID questionId);

    @Query("SELECT qa FROM QuestionAnswer qa WHERE qa.question.id IN :ids")
    List<QuestionAnswer> findAllByQuestionIds(@Param("ids") List<UUID> ids);
}
