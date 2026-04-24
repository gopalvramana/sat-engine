package com.satengine.domain.sympy;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

public interface SatQuestionRepository extends JpaRepository<SatQuestion, UUID> {

    // ── Session selection — no exclusions ─────────────────────────────────

    @Query(value = """
        SELECT * FROM sat_questions
        WHERE status = 'approved'
        AND (:section IS NULL OR section = :section)
        ORDER BY RANDOM() LIMIT 1
        """, nativeQuery = true)
    Optional<SatQuestion> findNextNoExclusions(@Param("section") String section);

    @Query(value = """
        SELECT * FROM sat_questions
        WHERE status = 'approved'
        AND (:section IS NULL OR section = :section)
        AND domain = :domain
        AND difficulty BETWEEN :minDiff AND :maxDiff
        ORDER BY RANDOM() LIMIT 1
        """, nativeQuery = true)
    Optional<SatQuestion> findNextByDomainDiffNoExclusions(
            @Param("section") String section,
            @Param("domain")  String domain,
            @Param("minDiff") int minDiff,
            @Param("maxDiff") int maxDiff);

    // ── Session selection — with exclusions ───────────────────────────────

    @Query(value = """
        SELECT * FROM sat_questions
        WHERE status = 'approved'
        AND (:section IS NULL OR section = :section)
        AND id NOT IN (:excludeIds)
        ORDER BY RANDOM() LIMIT 1
        """, nativeQuery = true)
    Optional<SatQuestion> findNext(
            @Param("section")    String     section,
            @Param("excludeIds") List<UUID> excludeIds);

    @Query(value = """
        SELECT * FROM sat_questions
        WHERE status = 'approved'
        AND (:section IS NULL OR section = :section)
        AND domain = :domain
        AND difficulty BETWEEN :minDiff AND :maxDiff
        AND id NOT IN (:excludeIds)
        ORDER BY RANDOM() LIMIT 1
        """, nativeQuery = true)
    Optional<SatQuestion> findNextByDomainDiff(
            @Param("section")    String     section,
            @Param("domain")     String     domain,
            @Param("excludeIds") List<UUID> excludeIds,
            @Param("minDiff")    int        minDiff,
            @Param("maxDiff")    int        maxDiff);

    // ── Diversity-aware selection ─────────────────────────────────────────
    // Excludes (template, variant) pairs seen in the student's last N sessions.
    // Falls back gracefully when no diverse question exists (new student, small pool).

    @Query(value = """
        SELECT * FROM sat_questions sq
        WHERE sq.status = 'approved'
        AND (:section IS NULL OR sq.section = :section)
        AND sq.id NOT IN (:excludeIds)
        AND (sq.template IS NULL OR sq.variant IS NULL
             OR (sq.template, sq.variant) NOT IN (
               SELECT sq2.template, sq2.variant
               FROM session_answers sa
               JOIN sessions       s   ON sa.session_id  = s.id
               JOIN sat_questions  sq2 ON sa.question_id = sq2.id
               WHERE s.user_id = :userId
                 AND sq2.template IS NOT NULL
                 AND sq2.variant  IS NOT NULL
               ORDER BY s.created_at DESC
               LIMIT :recentSessions
             ))
        ORDER BY RANDOM() LIMIT 1
        """, nativeQuery = true)
    Optional<SatQuestion> findNextDiverse(
            @Param("section")        String     section,
            @Param("excludeIds")     List<UUID> excludeIds,
            @Param("userId")         UUID       userId,
            @Param("recentSessions") int        recentSessions);

    // ── Admin / stats ─────────────────────────────────────────────────────

    @Query(value = """
        SELECT domain,
          SUM(CASE WHEN difficulty = 1 THEN 1 ELSE 0 END) AS easy,
          SUM(CASE WHEN difficulty = 2 THEN 1 ELSE 0 END) AS medium,
          SUM(CASE WHEN difficulty = 3 THEN 1 ELSE 0 END) AS hard,
          COUNT(*) AS total
        FROM sat_questions
        WHERE status = 'approved'
        AND (:section IS NULL OR section = :section)
        GROUP BY domain
        ORDER BY domain
        """, nativeQuery = true)
    List<Object[]> countByDomainAndDifficulty(@Param("section") String section);

    @Query(value = """
        SELECT skill_key, COUNT(*) AS cnt
        FROM sat_questions
        WHERE skill_key IS NOT NULL
          AND status NOT IN ('rejected', 'failed_review')
        GROUP BY skill_key
        ORDER BY skill_key
        """, nativeQuery = true)
    List<Object[]> countBySkillKey();

    // ── Duplicate detection ───────────────────────────────────────────────

    boolean existsBySkillKeyAndParamHash(String skillKey, String paramHash);

    @Query(value = """
        SELECT param_hash FROM sat_questions
        WHERE skill_key = :skillKey
          AND param_hash IS NOT NULL
          AND status != 'rejected'
        """, nativeQuery = true)
    List<String> findParamHashesBySkillKey(@Param("skillKey") String skillKey);

    // ── Scenario tag deduplication ────────────────────────────────────────

    @Query(value = """
        SELECT scenario_tag FROM sat_questions
        WHERE skill_key = :skillKey
          AND scenario_tag IS NOT NULL
          AND status != 'rejected'
        ORDER BY generated_at DESC
        LIMIT :limit
        """, nativeQuery = true)
    List<String> findRecentScenarioTagsForSkill(
            @Param("skillKey") String skillKey,
            @Param("limit")    int    limit);

    // ── QuestionService filtering (approved questions only) ───────────────
    // Spring Data JPA auto-generates these from method names.

    List<SatQuestion> findByStatus(String status);
    List<SatQuestion> findByStatusAndSection(String status, String section);
    List<SatQuestion> findByStatusAndDifficulty(String status, Short difficulty);
    List<SatQuestion> findByStatusAndDomain(String status, String domain);
    List<SatQuestion> findByStatusAndSectionAndDomain(String status, String section, String domain);
    List<SatQuestion> findByStatusAndSectionAndDifficulty(String status, String section, Short difficulty);
    List<SatQuestion> findByStatusAndDomainAndDifficulty(String status, String domain, Short difficulty);
    List<SatQuestion> findByStatusAndSectionAndDomainAndDifficulty(
            String status, String section, String domain, Short difficulty);

    // ── External ID allocation ────────────────────────────────────────────

    @Query(value = """
        SELECT COALESCE(MAX(CAST(SUBSTRING(external_id FROM :prefixLen) AS INTEGER)), 0)
        FROM sat_questions WHERE external_id LIKE :prefix
        """, nativeQuery = true)
    int findMaxSeqForPrefix(
            @Param("prefix")    String prefix,
            @Param("prefixLen") int    prefixLen);
}
