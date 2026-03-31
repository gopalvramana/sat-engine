-- V10: Reject RW-ALG-002 through RW-ALG-005 — same miscategorisation bug as V9
-- All five were generated with section=reading_writing + domain=algebra before
-- the sectionForDomain() fix was applied in GenerateStage.java.

UPDATE questions
SET status = 'rejected'
WHERE external_id IN ('RW-ALG-002', 'RW-ALG-003', 'RW-ALG-004', 'RW-ALG-005');
