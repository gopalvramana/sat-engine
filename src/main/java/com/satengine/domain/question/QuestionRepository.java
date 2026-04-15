package com.satengine.domain.question;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

public interface QuestionRepository extends JpaRepository<Question, UUID> {

    Optional<Question> findByExternalId(String externalId);

    /**
     * Count approved questions per domain broken down by difficulty band.
     * Returns rows of [domain, easy_count, medium_count, hard_count, total].
     * easy=1-2, medium=3-5, hard=6-7
     */
    @Query(value = """
            SELECT domain,
              SUM(CASE WHEN difficulty BETWEEN 1 AND 2 THEN 1 ELSE 0 END) AS easy,
              SUM(CASE WHEN difficulty BETWEEN 3 AND 5 THEN 1 ELSE 0 END) AS medium,
              SUM(CASE WHEN difficulty BETWEEN 6 AND 7 THEN 1 ELSE 0 END) AS hard,
              COUNT(*) AS total
            FROM questions
            WHERE status = 'approved'
            AND (:section IS NULL OR section = :section)
            GROUP BY domain
            """, nativeQuery = true)
    List<Object[]> countByDomainAndDifficulty(@Param("section") String section);

    /**
     * Find a random reviewed question for the given pool and section,
     * excluding questions that have already been answered in this session.
     */
    @Query(value = """
            SELECT * FROM questions
            WHERE status = 'approved'
            AND pool IN ('both', :pool)
            AND (:section IS NULL OR section = :section)
            AND id NOT IN (:excludeIds)
            ORDER BY RANDOM()
            LIMIT 1
            """, nativeQuery = true)
    Optional<Question> findNextQuestion(
            @Param("pool") String pool,
            @Param("section") String section,
            @Param("excludeIds") List<UUID> excludeIds
    );

    /**
     * Find a random approved question with no exclusions (first question of a session).
     */
    @Query(value = """
            SELECT * FROM questions
            WHERE status = 'approved'
            AND pool IN ('both', :pool)
            AND (:section IS NULL OR section = :section)
            ORDER BY RANDOM()
            LIMIT 1
            """, nativeQuery = true)
    Optional<Question> findNextQuestionNoExclusions(
            @Param("pool") String pool,
            @Param("section") String section
    );

    /**
     * Find a random approved question for a specific domain, excluding already-answered ones.
     */
    @Query(value = """
            SELECT * FROM questions
            WHERE status = 'approved'
            AND pool IN ('both', :pool)
            AND (:section IS NULL OR section = :section)
            AND domain = :domain
            AND id NOT IN (:excludeIds)
            ORDER BY RANDOM()
            LIMIT 1
            """, nativeQuery = true)
    Optional<Question> findNextQuestionByDomain(
            @Param("pool") String pool,
            @Param("section") String section,
            @Param("domain") String domain,
            @Param("excludeIds") List<UUID> excludeIds
    );

    /**
     * Find a random approved question for a specific domain, no exclusions.
     */
    @Query(value = """
            SELECT * FROM questions
            WHERE status = 'approved'
            AND pool IN ('both', :pool)
            AND (:section IS NULL OR section = :section)
            AND domain = :domain
            ORDER BY RANDOM()
            LIMIT 1
            """, nativeQuery = true)
    Optional<Question> findNextQuestionByDomainNoExclusions(
            @Param("pool") String pool,
            @Param("section") String section,
            @Param("domain") String domain
    );

    /**
     * Find a random approved question for a specific domain + difficulty range, excluding answered.
     */
    @Query(value = """
            SELECT * FROM questions
            WHERE status = 'approved'
            AND pool IN ('both', :pool)
            AND (:section IS NULL OR section = :section)
            AND domain = :domain
            AND difficulty BETWEEN :minDiff AND :maxDiff
            AND id NOT IN (:excludeIds)
            ORDER BY RANDOM()
            LIMIT 1
            """, nativeQuery = true)
    Optional<Question> findNextQuestionByDomainAndDifficulty(
            @Param("pool") String pool,
            @Param("section") String section,
            @Param("domain") String domain,
            @Param("excludeIds") List<UUID> excludeIds,
            @Param("minDiff") int minDiff,
            @Param("maxDiff") int maxDiff
    );

    /**
     * Find a random approved question for a specific domain + difficulty range, no exclusions.
     */
    @Query(value = """
            SELECT * FROM questions
            WHERE status = 'approved'
            AND pool IN ('both', :pool)
            AND (:section IS NULL OR section = :section)
            AND domain = :domain
            AND difficulty BETWEEN :minDiff AND :maxDiff
            ORDER BY RANDOM()
            LIMIT 1
            """, nativeQuery = true)
    Optional<Question> findNextQuestionByDomainAndDifficultyNoExclusions(
            @Param("pool") String pool,
            @Param("section") String section,
            @Param("domain") String domain,
            @Param("minDiff") int minDiff,
            @Param("maxDiff") int maxDiff
    );

    List<Question> findByStatus(String status);

    /** Approved questions that were never enriched (coreConcept is null). */
    @Query("SELECT q FROM Question q WHERE q.status = 'approved' AND q.coreConcept IS NULL")
    List<Question> findApprovedUnenriched();

    /** Approved or enriched MCQ questions missing choiceExplanations — for choice-explanation backfill. */
    @Query("SELECT q FROM Question q WHERE q.status IN ('approved', 'enriched') AND q.choiceExplanations IS NULL AND q.questionType = 'mcq'")
    List<Question> findMissingChoiceExplanations();

    /** Approved or enriched questions — for re-enrich runs. */
    @Query("SELECT q FROM Question q WHERE q.status IN ('approved', 'enriched')")
    List<Question> findAllApproved();

    /** Approved or enriched questions filtered by section (re-enrich). */
    @Query("SELECT q FROM Question q WHERE q.status IN ('approved', 'enriched') AND q.section = :section")
    List<Question> findAllApprovedBySection(@Param("section") String section);

    /** Approved or enriched questions filtered by domain (re-enrich). */
    @Query("SELECT q FROM Question q WHERE q.status IN ('approved', 'enriched') AND q.domain = :domain")
    List<Question> findAllApprovedByDomain(@Param("domain") String domain);

    /** Reviewed questions filtered by section. */
    @Query("SELECT q FROM Question q WHERE q.status = 'reviewed' AND q.section = :section")
    List<Question> findReviewedBySection(@Param("section") String section);

    /** Reviewed questions filtered by domain. */
    @Query("SELECT q FROM Question q WHERE q.status = 'reviewed' AND q.domain = :domain")
    List<Question> findReviewedByDomain(@Param("domain") String domain);

    @Query(value = """
        SELECT COALESCE(
          MAX(CAST(SUBSTRING(external_id FROM LENGTH(:prefix)+1 FOR 3) AS INTEGER)), 0
        ) FROM questions WHERE external_id LIKE :pattern
        """, nativeQuery = true)
    int findMaxSeqForPrefix(@Param("prefix") String prefix, @Param("pattern") String pattern);

    List<Question> findBySection(String section);

    List<Question> findBySectionAndDomain(String section, String domain);

    List<Question> findByStatusAndSection(String status, String section);

    List<Question> findByStatusAndDomain(String status, String domain);

    List<Question> findByStatusAndSectionAndDomain(String status, String section, String domain);

    List<Question> findByDifficulty(Short difficulty);

    List<Question> findBySectionAndDomainAndDifficulty(String section, String domain, Short difficulty);

    List<Question> findBySectionAndDifficulty(String section, Short difficulty);

    List<Question> findByDomainAndDifficulty(String domain, Short difficulty);

    /**
     * Returns up to N most-recent questions for the given domain+skillKey,
     * used to build the "existing questions" diversity context before generation.
     * Returns only fields needed for the prompt (externalId, questionStem, scenarioTag).
     */
    /**
     * Returns ALL non-rejected questions in a domain for the diversity context.
     * No skill filter and no limit — Claude must see every existing stem to avoid duplicates.
     * Each Object[] is { external_id (String), question_stem (String), scenario_tag (String) }.
     */
    @Query(value = """
        SELECT external_id, question_stem, scenario_tag
        FROM questions
        WHERE domain = :domain
          AND status != 'rejected'
        ORDER BY generated_at DESC
        """, nativeQuery = true)
    List<Object[]> findAllForDiversityContext(@Param("domain") String domain);

    /**
     * Returns all non-rejected question stems for a domain.
     * Used by GenerateStage to detect near-duplicate stems before saving.
     */
    @Query(value = """
        SELECT question_stem
        FROM questions
        WHERE domain = :domain
          AND status != 'rejected'
        """, nativeQuery = true)
    List<String> findAllStemsForDomain(@Param("domain") String domain);

    /**
     * Returns non-rejected question stems for a domain scoped to a specific pool.
     * Used for diagnostic generation so the Jaccard check only compares against
     * other diagnostic questions — not the entire drill/test pool.
     */
    @Query(value = """
        SELECT question_stem
        FROM questions
        WHERE domain = :domain
          AND pool = :pool
          AND status != 'rejected'
        """, nativeQuery = true)
    List<String> findStemsForDomainAndPool(@Param("domain") String domain, @Param("pool") String pool);

    /**
     * Returns question counts per skill_key for a domain.
     * Used by GenerateStage to pick the least-covered skill for even distribution.
     * Each Object[] is { skill_key (String), count (Long) }.
     */
    @Query(value = """
        SELECT skill_key, COUNT(*) AS cnt
        FROM questions
        WHERE domain = :domain
          AND skill_key IS NOT NULL
          AND status NOT IN ('rejected', 'failed_review')
        GROUP BY skill_key
        """, nativeQuery = true)
    List<Object[]> countBySkillKeyForDomain(@Param("domain") String domain);

    /**
     * Count usable questions (non-rejected) per skill+difficulty for a domain.
     * Used for per-skill difficulty balancing during generation.
     * Returns rows of [skill_key, difficulty, count].
     */
    @Query(value = """
        SELECT skill_key, difficulty, COUNT(*) AS cnt
        FROM questions
        WHERE domain = :domain
          AND skill_key IS NOT NULL
          AND status NOT IN ('rejected', 'failed_review')
        GROUP BY skill_key, difficulty
        """, nativeQuery = true)
    List<Object[]> countBySkillAndDifficultyForDomain(@Param("domain") String domain);

    /**
     * Full spread breakdown for the admin dashboard.
     * Returns rows of [section, domain, skill_key, difficulty, usable_count, pending_count, failed_count].
     * usable = approved/enriched/reviewed; pending = pending_review; failed = rejected/failed_review.
     */
    @Query(value = """
        SELECT section, domain, skill_key, difficulty,
          COUNT(*) FILTER (WHERE status IN ('approved', 'enriched', 'reviewed')) AS usable,
          COUNT(*) FILTER (WHERE status IN ('pending_review', 'generated')) AS pending,
          COUNT(*) FILTER (WHERE status IN ('rejected', 'failed_review')) AS failed
        FROM questions
        WHERE skill_key IS NOT NULL
        GROUP BY section, domain, skill_key, difficulty
        ORDER BY section, domain, skill_key, difficulty
        """, nativeQuery = true)
    List<Object[]> countSpreadForDashboard();

    /** Approved/enriched geometry questions with animation.eligible=true but no frames yet — for animation backfill. */
    @Query(value = """
        SELECT * FROM questions
        WHERE status IN ('approved', 'enriched')
          AND CAST(animation->>'eligible' AS boolean) = true
          AND animation->'frames' IS NULL
        """, nativeQuery = true)
    List<Question> findAnimationEligible();

    /** All eligible geometry questions regardless of whether frames exist — for force re-enrichment. */
    @Query(value = """
        SELECT * FROM questions
        WHERE status IN ('approved', 'enriched')
          AND CAST(animation->>'eligible' AS boolean) = true
        """, nativeQuery = true)
    List<Question> findAllAnimationEligible();

    /** Count questions by status — used by the pipeline dashboard stats endpoint. */
    long countByStatus(String status);

    /**
     * Count non-rejected questions per skill_key for a specific pool.
     * Used by GenerateStage DIAGNOSTIC mode to pick the globally least-covered skill.
     * Each Object[] is { skill_key (String), count (Long) }.
     */
    @Query(value = """
        SELECT skill_key, COUNT(*) AS cnt
        FROM questions
        WHERE pool = :pool
          AND skill_key IS NOT NULL
          AND status NOT IN ('rejected', 'failed_review')
        GROUP BY skill_key
        """, nativeQuery = true)
    List<Object[]> countBySkillKeyForPool(@Param("pool") String pool);

    /**
     * Count approved questions per skill_key grouped by pool.
     * Used by the pool-spread admin dashboard endpoint.
     * Each Object[] is { skill_key (String), pool (String), count (Long) }.
     */
    @Query(value = """
        SELECT skill_key, pool, COUNT(*) AS cnt
        FROM questions
        WHERE skill_key IS NOT NULL
          AND status = 'approved'
        GROUP BY skill_key, pool
        ORDER BY skill_key, pool
        """, nativeQuery = true)
    List<Object[]> countBySkillAndPoolApproved();
}
