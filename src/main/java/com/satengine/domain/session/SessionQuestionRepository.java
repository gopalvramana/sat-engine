package com.satengine.domain.session;

import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

public interface SessionQuestionRepository extends JpaRepository<SessionQuestion, UUID> {

    List<SessionQuestion> findBySessionIdOrderByPositionAsc(UUID sessionId);

    boolean existsBySessionId(UUID sessionId);

    Optional<SessionQuestion> findBySessionIdAndQuestionId(UUID sessionId, UUID questionId);
}
