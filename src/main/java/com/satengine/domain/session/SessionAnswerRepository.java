package com.satengine.domain.session;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

public interface SessionAnswerRepository extends JpaRepository<SessionAnswer, UUID> {

    List<SessionAnswer> findBySessionId(UUID sessionId);

    Optional<SessionAnswer> findBySessionIdAndQuestionId(UUID sessionId, UUID questionId);

    @Query("SELECT sa.questionId FROM SessionAnswer sa WHERE sa.sessionId = :sessionId")
    List<UUID> findAnsweredQuestionIds(@Param("sessionId") UUID sessionId);
}
