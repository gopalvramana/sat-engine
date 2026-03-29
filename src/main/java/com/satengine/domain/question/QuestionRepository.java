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
}
