-- V6: NULL out Math-specific fields on all Reading & Writing questions.
--
-- Existing R&W questions were generated and enriched with the old Math pipeline,
-- which stamped trap_category = 'concept_gap' (EnrichStage default), and may have
-- populated explanation_steps, core_concept, prerequisites, animation.
-- These fields are meaningless for R&W and should be NULL.
-- The UI already hides them for R&W (isMath flag), but the DB should be clean too.

UPDATE questions
SET
    explanation_steps = NULL,
    trap_category     = NULL,
    trap_explanation  = NULL,
    core_concept      = NULL,
    prerequisites     = NULL,
    animation         = NULL
WHERE section = 'reading_writing';
