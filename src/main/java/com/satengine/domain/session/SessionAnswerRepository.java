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

    @Query("""
        SELECT sa FROM SessionAnswer sa
        WHERE sa.sessionId IN (
            SELECT s.id FROM Session s WHERE s.userId = :userId
        )
        """)
    List<SessionAnswer> findAllByUserId(@Param("userId") UUID userId);

    /**
     * Returns per-domain accuracy for a user.
     * Each Object[] row: [domain (String), total (Long), correct (Long)]
     */
    @Query(value = """
        SELECT q.domain,
               COUNT(sa.id)                                            AS total,
               SUM(CASE WHEN sa.is_correct = true THEN 1 ELSE 0 END)  AS correct
        FROM session_answers sa
        JOIN questions q ON sa.question_id = q.id
        JOIN sessions  s ON sa.session_id  = s.id
        WHERE s.user_id = :userId
        GROUP BY q.domain
        ORDER BY q.domain
        """, nativeQuery = true)
    List<Object[]> getDomainAccuracyForUser(@Param("userId") UUID userId);
}
