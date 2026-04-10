package com.satengine;

import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Component;

import java.util.UUID;

/**
 * Inserts and removes test fixture data directly via JDBC.
 * Avoids going through the domain model so tests are isolated from
 * pipeline/enrichment logic.
 */
@Component
public class TestDataHelper {

    private final JdbcTemplate jdbc;

    public TestDataHelper(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    /**
     * Insert a minimal approved MCQ question and its answer.
     *
     * @param section  "math" or "reading_writing"
     * @param domain   e.g. "algebra"
     * @param difficulty 1-7
     * @param correctAnswer "A", "B", "C", or "D"
     * @return the generated question UUID
     */
    public UUID insertMcqQuestion(String externalId, String section, String domain,
                                   int difficulty, String correctAnswer) {
        UUID qId = UUID.randomUUID();
        jdbc.update("""
                INSERT INTO questions
                  (id, external_id, section, domain, skill, difficulty, question_type,
                   question_stem, option_a, option_b, option_c, option_d,
                   pool, status, source)
                VALUES (?, ?, ?, ?, ?, ?, 'mcq',
                        'What is 2 + 2?', 'A) 3', 'B) 4', 'C) 5', 'D) 6',
                        'both', 'approved', 'ai_generated')
                """,
                qId, externalId, section, domain, "test_skill", (short) difficulty);

        jdbc.update("""
                INSERT INTO question_answers (id, question_id, correct_answer)
                VALUES (?, ?, ?)
                """,
                UUID.randomUUID(), qId, correctAnswer);

        return qId;
    }

    /**
     * Insert a minimal approved SPR question and its answer.
     */
    public UUID insertSprQuestion(String externalId, String section, String domain,
                                   int difficulty, String correctAnswer) {
        UUID qId = UUID.randomUUID();
        jdbc.update("""
                INSERT INTO questions
                  (id, external_id, section, domain, skill, difficulty, question_type,
                   question_stem, spr_min, spr_max,
                   pool, status, source)
                VALUES (?, ?, ?, ?, ?, ?, 'spr',
                        'Solve for x: x + 3 = 7', 4, 4,
                        'both', 'approved', 'ai_generated')
                """,
                qId, externalId, section, domain, "test_skill", (short) difficulty);

        jdbc.update("""
                INSERT INTO question_answers (id, question_id, correct_answer)
                VALUES (?, ?, ?)
                """,
                UUID.randomUUID(), qId, correctAnswer);

        return qId;
    }

    /**
     * Delete all test data inserted during a test.
     * Call this in @AfterEach to keep tests isolated.
     */
    public void deleteAllTestData() {
        jdbc.update("DELETE FROM session_answers");
        jdbc.update("DELETE FROM sessions");
        jdbc.update("DELETE FROM question_answers");
        jdbc.update("DELETE FROM questions");
    }
}
