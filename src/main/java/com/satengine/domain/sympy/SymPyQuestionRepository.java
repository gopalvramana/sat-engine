package com.satengine.domain.sympy;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;
import java.util.UUID;

public interface SymPyQuestionRepository extends JpaRepository<SymPyQuestion, UUID> {

    /** Count non-rejected questions per skill key — used for coverage balancing. */
    @Query(value = """
        SELECT skill_key, COUNT(*) AS cnt
        FROM sympy_questions
        WHERE skill_key IS NOT NULL
          AND status NOT IN ('rejected', 'failed_review')
        GROUP BY skill_key
        """, nativeQuery = true)
    List<Object[]> countBySkillKey();

    /** Return the N most recent scenario tags for a skill — used to avoid repeating contexts. */
    @Query(value = """
        SELECT scenario_tag
        FROM sympy_questions
        WHERE skill_key = :skillKey
          AND scenario_tag IS NOT NULL
          AND status != 'rejected'
        ORDER BY generated_at DESC
        LIMIT :limit
        """, nativeQuery = true)
    List<String> findRecentScenarioTagsForSkill(@Param("skillKey") String skillKey,
                                                @Param("limit") int limit);

    /** True when a question with the same param_hash already exists for this skill. */
    boolean existsBySkillKeyAndParamHash(String skillKey, String paramHash);

    /** All non-null param hashes for a skill — used to pre-seed excludeParams at run start. */
    @Query(value = """
        SELECT param_hash
        FROM sympy_questions
        WHERE skill_key = :skillKey
          AND param_hash IS NOT NULL
          AND status != 'rejected'
        """, nativeQuery = true)
    List<String> findParamHashesBySkillKey(@Param("skillKey") String skillKey);

    /** Find the highest numeric suffix already used for an external_id prefix (e.g. "SP-LEQ-"). */
    @Query(value = """
        SELECT COALESCE(MAX(CAST(SUBSTRING(external_id FROM :prefixLen) AS INTEGER)), 0)
        FROM sympy_questions
        WHERE external_id LIKE :prefix
        """, nativeQuery = true)
    int findMaxSeqForPrefix(@Param("prefix") String prefix, @Param("prefixLen") int prefixLen);
}
