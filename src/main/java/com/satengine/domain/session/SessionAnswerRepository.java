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
            SELECT s.id FROM Session s WHERE s.userId = :userId AND s.status != 'archived'
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
        JOIN sat_questions q ON sa.question_id = q.id
        JOIN sessions      s ON sa.session_id  = s.id
        WHERE s.user_id = :userId
          AND s.status != 'archived'
        GROUP BY q.domain
        ORDER BY q.domain
        """, nativeQuery = true)
    List<Object[]> getDomainAccuracyForUser(@Param("userId") UUID userId);

    /**
     * Wrong answers for the error log.
     * Each Object[] row: [session_id, question_id, student_answer, time_spent_seconds, answered_at,
     *                     domain, skill_key, difficulty, question_stem, correct_answer]
     */
    @Query(value = """
        SELECT sa.session_id, sa.question_id, sa.student_answer,
               sa.time_spent_seconds, sa.answered_at,
               q.domain, q.skill_key, q.difficulty,
               q.content->>'questionStem' AS question_stem,
               q.correct_answer
        FROM session_answers sa
        JOIN sat_questions q ON sa.question_id = q.id
        JOIN sessions      s ON sa.session_id  = s.id
        WHERE s.user_id = :userId
          AND s.status != 'archived'
          AND sa.is_correct = false
        ORDER BY sa.answered_at DESC
        """, nativeQuery = true)
    List<Object[]> findWrongAnswersByUserId(@Param("userId") UUID userId);

    /**
     * Questions per day for analytics (last 30 days).
     * Each Object[] row: [day (String "YYYY-MM-DD"), count (Long)]
     */
    @Query(value = """
        SELECT TO_CHAR(sa.answered_at AT TIME ZONE 'UTC', 'YYYY-MM-DD') AS day,
               COUNT(sa.id) AS cnt
        FROM session_answers sa
        JOIN sessions s ON sa.session_id = s.id
        WHERE s.user_id = :userId
          AND s.status != 'archived'
          AND sa.answered_at >= NOW() - INTERVAL '30 days'
        GROUP BY day
        ORDER BY day
        """, nativeQuery = true)
    List<Object[]> getQuestionsPerDayForUser(@Param("userId") UUID userId);

    /**
     * Per-domain stats with avg time for analytics.
     * Each Object[] row: [domain, section, total, correct, avg_time]
     */
    @Query(value = """
        SELECT q.domain,
               q.section,
               COUNT(sa.id)                                            AS total,
               SUM(CASE WHEN sa.is_correct = true THEN 1 ELSE 0 END)  AS correct,
               AVG(sa.time_spent_seconds)                              AS avg_time
        FROM session_answers sa
        JOIN sat_questions q ON sa.question_id = q.id
        JOIN sessions      s ON sa.session_id  = s.id
        WHERE s.user_id = :userId
          AND s.status != 'archived'
        GROUP BY q.domain, q.section
        ORDER BY total DESC
        """, nativeQuery = true)
    List<Object[]> getDomainStatsForUser(@Param("userId") UUID userId);

    /**
     * Average difficulty across all answers for a user (1=Easy, 2=Med, 3=Hard).
     */
    @Query(value = """
        SELECT AVG(q.difficulty)
        FROM session_answers sa
        JOIN sat_questions q ON sa.question_id = q.id
        JOIN sessions      s ON sa.session_id  = s.id
        WHERE s.user_id = :userId
          AND s.status != 'archived'
        """, nativeQuery = true)
    Double getAvgDifficultyForUser(@Param("userId") UUID userId);

    /**
     * Stats for the trailing 24-hour window.
     * Returns one Object[] row: [total (Long), correct (Long), avgDifficulty (Double)]
     * COUNT always returns a value (0 if no rows); SUM/AVG return null for empty sets.
     */
    @Query(value = """
        SELECT COUNT(sa.id),
               SUM(CASE WHEN sa.is_correct = true THEN 1 ELSE 0 END),
               AVG(q.difficulty)
        FROM session_answers sa
        JOIN sat_questions q ON sa.question_id = q.id
        JOIN sessions      s ON sa.session_id  = s.id
        WHERE s.user_id = :userId
          AND s.status != 'archived'
          AND sa.answered_at >= NOW() - INTERVAL '24 hours'
        """, nativeQuery = true)
    List<Object[]> getLast24hStatsForUser(@Param("userId") UUID userId);

    /**
     * Last 5 sessions that have at least one answer, newest first.
     * Each Object[] row: [id, session_type, section, started_at, total (Long), correct (Long)]
     */
    @Query(value = """
        SELECT s.id, s.session_type, s.section, s.started_at,
               COUNT(sa.id)                                            AS total,
               SUM(CASE WHEN sa.is_correct = true THEN 1 ELSE 0 END)  AS correct
        FROM sessions s
        JOIN session_answers sa ON sa.session_id = s.id
        WHERE s.user_id = :userId
          AND s.status != 'archived'
        GROUP BY s.id, s.session_type, s.section, s.started_at
        ORDER BY s.started_at DESC
        LIMIT 5
        """, nativeQuery = true)
    List<Object[]> getRecentSessionsForUser(@Param("userId") UUID userId);
}
