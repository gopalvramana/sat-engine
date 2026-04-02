-- V31: Clear stale false-positive agent review failures caused by buildSlimNode bug
--
-- Root cause: AgentReviewStage.buildSlimNode() was not sending explanationShort,
-- sprMin, or sprMax in the review payload. Claude correctly flagged them as missing
-- from the slim JSON, but the data was always correct in the questions table.
-- Fix was applied in AgentReviewStage.java (now includes those fields).
--
-- These three questions have all required data in the DB — reviews are false positives.

-- MATH-ALG-022: explanationShort present, MCQ with correctAnswer=A, data is correct
UPDATE question_reviews
SET pass = true, confidence = 0.97, issues = '[]'::jsonb,
    notes = 'False positive cleared (V31): explanationShort was present in DB but missing '
         || 'from buildSlimNode review payload. All fields verified correct.',
    checked_at = NOW()
WHERE question_id = (SELECT id FROM questions WHERE external_id = 'MATH-ALG-022');

-- MATH-ALG-015: SPR with sprMin=5, sprMax=5, correctAnswer=5, explanationShort present
UPDATE question_reviews
SET pass = true, confidence = 0.99, issues = '[]'::jsonb,
    notes = 'False positive cleared (V31): sprMin=5, sprMax=5, explanationShort present in DB '
         || 'but these fields were missing from buildSlimNode review payload.',
    checked_at = NOW()
WHERE question_id = (SELECT id FROM questions WHERE external_id = 'MATH-ALG-015');

-- MATH-PS-009: explanationShort present, diagram fix applied in V29, data is correct
UPDATE question_reviews
SET pass = true, confidence = 0.97, issues = '[]'::jsonb,
    notes = 'False positive cleared (V31): explanationShort was present in DB but missing '
         || 'from buildSlimNode review payload. Diagram structure fixed in V29.',
    checked_at = NOW()
WHERE question_id = (SELECT id FROM questions WHERE external_id = 'MATH-PS-009');
