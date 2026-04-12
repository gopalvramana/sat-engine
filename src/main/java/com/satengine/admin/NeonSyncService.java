package com.satengine.admin;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import javax.sql.DataSource;
import java.math.BigDecimal;
import java.sql.*;

/**
 * Syncs approved questions from the local (primary) datasource to Neon.
 * <p>
 * Tables synced (approved only):
 *   questions           — upsert on external_id
 *   question_answers    — upsert on question_id (resolved via external_id)
 *   question_reviews    — upsert on question_id (resolved via external_id)
 */
@Slf4j
@Service
public class NeonSyncService {

    private final DataSource primaryDataSource;

    @Value("${neon.jdbc.url:}")      private String neonUrl;
    @Value("${neon.jdbc.username:}") private String neonUsername;
    @Value("${neon.jdbc.password:}") private String neonPassword;

    public NeonSyncService(DataSource primaryDataSource) {
        this.primaryDataSource = primaryDataSource;
    }

    // ── Public entry point ────────────────────────────────────────────────

    public void sync() {
        if (neonUrl == null || neonUrl.isBlank()) {
            throw new IllegalStateException(
                    "neon.jdbc.url is not configured. Add it to application.yml (neon.jdbc.url/username/password).");
        }

        log.info("═".repeat(60));
        log.info(" Neon Sync — approved questions → Neon");
        log.info("═".repeat(60));

        try (Connection src = primaryDataSource.getConnection();
             Connection dst = DriverManager.getConnection(neonUrl, neonUsername, neonPassword)) {

            dst.setAutoCommit(false);

            int questions = syncQuestions(src, dst);
            int answers   = syncAnswers(src, dst);
            int reviews   = syncReviews(src, dst);

            dst.commit();

            log.info("─".repeat(60));
            log.info(" ✓ Sync complete — {} questions  {} answers  {} reviews",
                    questions, answers, reviews);

        } catch (SQLException e) {
            log.error("Sync failed: {}", e.getMessage(), e);
            throw new RuntimeException("Sync failed: " + e.getMessage(), e);
        }
    }

    // ── Questions ─────────────────────────────────────────────────────────

    private int syncQuestions(Connection src, Connection dst) throws SQLException {
        log.info("  Syncing questions...");

        String select = """
                SELECT external_id, section, domain, skill, difficulty, question_type,
                       question_stem, option_a, option_b, option_c, option_d,
                       spr_min, spr_max, explanation_short, explanation_steps,
                       trap_category, trap_explanation, core_concept, prerequisites,
                       animation, pool, passage_text, passage_source, diagram,
                       calculator_ok, source, generated_at, status, skill_key,
                       scenario_tag, wrong_answer_explanations, choice_explanations
                FROM questions
                WHERE status = 'approved'
                """;

        String upsert = """
                INSERT INTO questions (
                    external_id, section, domain, skill, difficulty, question_type,
                    question_stem, option_a, option_b, option_c, option_d,
                    spr_min, spr_max, explanation_short, explanation_steps,
                    trap_category, trap_explanation, core_concept, prerequisites,
                    animation, pool, passage_text, passage_source, diagram,
                    calculator_ok, source, generated_at, status, skill_key,
                    scenario_tag, wrong_answer_explanations, choice_explanations
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT (external_id) DO UPDATE SET
                    section                    = EXCLUDED.section,
                    domain                     = EXCLUDED.domain,
                    skill                      = EXCLUDED.skill,
                    difficulty                 = EXCLUDED.difficulty,
                    question_type              = EXCLUDED.question_type,
                    question_stem              = EXCLUDED.question_stem,
                    option_a                   = EXCLUDED.option_a,
                    option_b                   = EXCLUDED.option_b,
                    option_c                   = EXCLUDED.option_c,
                    option_d                   = EXCLUDED.option_d,
                    spr_min                    = EXCLUDED.spr_min,
                    spr_max                    = EXCLUDED.spr_max,
                    explanation_short          = EXCLUDED.explanation_short,
                    explanation_steps          = EXCLUDED.explanation_steps,
                    trap_category              = EXCLUDED.trap_category,
                    trap_explanation           = EXCLUDED.trap_explanation,
                    core_concept               = EXCLUDED.core_concept,
                    prerequisites              = EXCLUDED.prerequisites,
                    animation                  = EXCLUDED.animation,
                    pool                       = EXCLUDED.pool,
                    passage_text               = EXCLUDED.passage_text,
                    passage_source             = EXCLUDED.passage_source,
                    diagram                    = EXCLUDED.diagram,
                    calculator_ok              = EXCLUDED.calculator_ok,
                    source                     = EXCLUDED.source,
                    generated_at               = EXCLUDED.generated_at,
                    status                     = EXCLUDED.status,
                    skill_key                  = EXCLUDED.skill_key,
                    scenario_tag               = EXCLUDED.scenario_tag,
                    wrong_answer_explanations  = EXCLUDED.wrong_answer_explanations,
                    choice_explanations        = EXCLUDED.choice_explanations
                """;

        int count = 0;
        try (PreparedStatement sel = src.prepareStatement(select);
             PreparedStatement ins = dst.prepareStatement(upsert);
             ResultSet rs = sel.executeQuery()) {

            while (rs.next()) {
                String externalId = rs.getString("external_id");
                ins.setString(1,  externalId);
                ins.setString(2,  rs.getString("section"));
                ins.setString(3,  rs.getString("domain"));
                ins.setString(4,  rs.getString("skill"));
                ins.setShort(5,   rs.getShort("difficulty"));
                ins.setString(6,  rs.getString("question_type"));
                ins.setString(7,  rs.getString("question_stem"));
                ins.setString(8,  rs.getString("option_a"));
                ins.setString(9,  rs.getString("option_b"));
                ins.setString(10, rs.getString("option_c"));
                ins.setString(11, rs.getString("option_d"));
                setBigDecimalOrNull(ins, 12, rs.getBigDecimal("spr_min"));
                setBigDecimalOrNull(ins, 13, rs.getBigDecimal("spr_max"));
                ins.setString(14, rs.getString("explanation_short"));
                setJsonb(ins, 15, rs.getString("explanation_steps"));
                ins.setString(16, rs.getString("trap_category"));
                ins.setString(17, rs.getString("trap_explanation"));
                setJsonb(ins, 18, rs.getString("core_concept"));
                setJsonb(ins, 19, rs.getString("prerequisites"));
                setJsonb(ins, 20, rs.getString("animation"));
                ins.setString(21, rs.getString("pool"));
                ins.setString(22, rs.getString("passage_text"));
                ins.setString(23, rs.getString("passage_source"));
                setJsonb(ins, 24, rs.getString("diagram"));
                ins.setBoolean(25, rs.getBoolean("calculator_ok"));
                ins.setString(26, rs.getString("source"));
                setTimestampOrNull(ins, 27, rs.getTimestamp("generated_at"));
                ins.setString(28, rs.getString("status"));
                ins.setString(29, rs.getString("skill_key"));
                ins.setString(30, rs.getString("scenario_tag"));
                setJsonb(ins, 31, rs.getString("wrong_answer_explanations"));
                setJsonb(ins, 32, rs.getString("choice_explanations"));

                ins.addBatch();
                count++;

                if (count % 50 == 0) {
                    ins.executeBatch();
                    log.info("  → {} questions synced...", count);
                }
            }
            if (count % 50 != 0 || count == 0) ins.executeBatch();
        }

        log.info("  ✓ {} questions upserted", count);
        return count;
    }

    // ── Question Answers ──────────────────────────────────────────────────

    private int syncAnswers(Connection src, Connection dst) throws SQLException {
        log.info("  Syncing question_answers...");

        String select = """
                SELECT q.external_id, qa.correct_answer
                FROM question_answers qa
                JOIN questions q ON qa.question_id = q.id
                WHERE q.status = 'approved'
                """;

        // Resolve question_id in Neon by external_id
        String upsert = """
                INSERT INTO question_answers (question_id, correct_answer)
                SELECT q.id, ?
                FROM questions q
                WHERE q.external_id = ?
                ON CONFLICT (question_id) DO UPDATE SET
                    correct_answer = EXCLUDED.correct_answer
                """;

        int count = 0;
        try (PreparedStatement sel = src.prepareStatement(select);
             PreparedStatement ins = dst.prepareStatement(upsert);
             ResultSet rs = sel.executeQuery()) {

            while (rs.next()) {
                ins.setString(1, rs.getString("correct_answer"));
                ins.setString(2, rs.getString("external_id"));
                ins.addBatch();
                count++;
            }
            ins.executeBatch();
        }

        log.info("  ✓ {} answers upserted", count);
        return count;
    }

    // ── Question Reviews ──────────────────────────────────────────────────

    private int syncReviews(Connection src, Connection dst) throws SQLException {
        log.info("  Syncing question_reviews...");

        String select = """
                SELECT q.external_id, qr.pass, qr.confidence, qr.solved_answer,
                       qr.issues, qr.notes, qr.model, qr.checked_at
                FROM question_reviews qr
                JOIN questions q ON qr.question_id = q.id
                WHERE q.status = 'approved'
                """;

        String upsert = """
                INSERT INTO question_reviews (question_id, pass, confidence, solved_answer, issues, notes, model, checked_at)
                SELECT q.id, ?, ?, ?, ?, ?, ?, ?
                FROM questions q
                WHERE q.external_id = ?
                ON CONFLICT (question_id) DO UPDATE SET
                    pass         = EXCLUDED.pass,
                    confidence   = EXCLUDED.confidence,
                    solved_answer= EXCLUDED.solved_answer,
                    issues       = EXCLUDED.issues,
                    notes        = EXCLUDED.notes,
                    model        = EXCLUDED.model,
                    checked_at   = EXCLUDED.checked_at
                """;

        int count = 0;
        try (PreparedStatement sel = src.prepareStatement(select);
             PreparedStatement ins = dst.prepareStatement(upsert);
             ResultSet rs = sel.executeQuery()) {

            while (rs.next()) {
                ins.setBoolean(1,    rs.getBoolean("pass"));
                setBigDecimalOrNull(ins, 2, rs.getBigDecimal("confidence"));
                ins.setString(3,     rs.getString("solved_answer"));
                setJsonb(ins, 4,     rs.getString("issues"));
                ins.setString(5,     rs.getString("notes"));
                ins.setString(6,     rs.getString("model"));
                setTimestampOrNull(ins, 7, rs.getTimestamp("checked_at"));
                ins.setString(8,     rs.getString("external_id"));
                ins.addBatch();
                count++;
            }
            ins.executeBatch();
        }

        log.info("  ✓ {} reviews upserted", count);
        return count;
    }

    // ── JDBC helpers ──────────────────────────────────────────────────────

    /** Sets a JSONB parameter: null → SQL NULL, non-null → string with Types.OTHER (PostgreSQL auto-casts). */
    private void setJsonb(PreparedStatement ps, int idx, String json) throws SQLException {
        if (json == null) {
            ps.setNull(idx, Types.OTHER);
        } else {
            ps.setObject(idx, json, Types.OTHER);
        }
    }

    private void setBigDecimalOrNull(PreparedStatement ps, int idx, BigDecimal v) throws SQLException {
        if (v == null) ps.setNull(idx, Types.NUMERIC);
        else ps.setBigDecimal(idx, v);
    }

    private void setTimestampOrNull(PreparedStatement ps, int idx, Timestamp ts) throws SQLException {
        if (ts == null) ps.setNull(idx, Types.TIMESTAMP_WITH_TIMEZONE);
        else ps.setTimestamp(idx, ts);
    }
}
