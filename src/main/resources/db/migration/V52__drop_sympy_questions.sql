-- ============================================================
-- V52: Drop old sympy_questions + sympy_question_answers tables
-- ============================================================
-- All 565 rows verified in sat_questions (V50 migration).
-- Template/variant backfilled from mathObject.params (V51).
-- Java code fully migrated to SatQuestion + SatQuestionRepository.
-- SymPyQuestion, SymPyQuestionAnswer entities deleted from codebase.
-- ============================================================

DROP TABLE IF EXISTS sympy_question_answers;
DROP TABLE IF EXISTS sympy_questions;
