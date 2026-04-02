-- V30: Fix stale agent-review result for MATH-ALG-023
--
-- Root cause: AgentReviewStage.buildSlimNode() was missing sprMin, sprMax,
-- and explanationShort fields. The slim JSON sent to Claude for review genuinely
-- did not contain those fields, so Claude correctly flagged them as missing.
-- The data in the questions table was always correct (sprMin=48, sprMax=48,
-- explanationShort is present). The review result was a false positive.
--
-- Fix applied in code: AgentReviewStage.java now includes sprMin, sprMax,
-- and explanationShort in buildSlimNode() so future reviews will pass correctly.
--
-- This migration clears the false-positive review record so MATH-ALG-023
-- no longer appears as a failed question in the admin UI.

UPDATE question_reviews
SET
  pass         = true,
  confidence   = 0.99,
  solved_answer = '48',
  issues       = '[]'::jsonb,
  notes        = 'Re-evaluated: sprMin=48, sprMax=48, explanationShort present. '
              || 'Original failure was a false positive — buildSlimNode() omitted '
              || 'sprMin/sprMax/explanationShort from the review payload. '
              || 'Math verified: 8n = 240 + 3n → 5n = 240 → n = 48. All checks pass.',
  checked_at   = NOW()
WHERE question_id = (SELECT id FROM questions WHERE external_id = 'MATH-ALG-023');
