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

    List<Question> findByStatus(String status);

    /** Approved questions that were never enriched (coreConcept is null). */
    @Query("SELECT q FROM Question q WHERE q.status = 'approved' AND q.coreConcept IS NULL")
    List<Question> findApprovedUnenriched();

    /** All approved questions — including already-enriched ones (for re-enrich runs). */
    @Query("SELECT q FROM Question q WHERE q.status = 'approved'")
    List<Question> findAllApproved();

    /** Approved questions filtered by section (re-enrich). */
    @Query("SELECT q FROM Question q WHERE q.status = 'approved' AND q.section = :section")
    List<Question> findAllApprovedBySection(@Param("section") String section);

    /** Approved questions filtered by domain (re-enrich). */
    @Query("SELECT q FROM Question q WHERE q.status = 'approved' AND q.domain = :domain")
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

    List<Question> findByDifficulty(Short difficulty);

    List<Question> findBySectionAndDomainAndDifficulty(String section, String domain, Short difficulty);

    List<Question> findBySectionAndDifficulty(String section, Short difficulty);

    List<Question> findByDomainAndDifficulty(String domain, Short difficulty);

    /**
     * Returns up to N most-recent questions for the given domain+skillKey,
     * used to build the "existing questions" diversity context before generation.
     * Returns only fields needed for the prompt (externalId, questionStem, scenarioTag).
     */
    @Query(value = """
        SELECT external_id, question_stem, scenario_tag
        FROM questions
        WHERE domain = :domain
          AND (:skillKey IS NULL OR skill_key = :skillKey)
        ORDER BY generated_at DESC
        LIMIT :limit
        """, nativeQuery = true)
    List<Object[]> findRecentForDiversityContext(
            @Param("domain")    String domain,
            @Param("skillKey")  String skillKey,
            @Param("limit")     int limit
    );

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
        GROUP BY skill_key
        """, nativeQuery = true)
    List<Object[]> countBySkillKeyForDomain(@Param("domain") String domain);
}
