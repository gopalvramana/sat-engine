-- Replace boolean reviewed with full status lifecycle
ALTER TABLE questions ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'generated';
UPDATE questions SET status = 'approved' WHERE reviewed = TRUE;
ALTER TABLE questions DROP COLUMN reviewed;
ALTER TABLE questions DROP COLUMN review_notes;
CREATE INDEX idx_questions_status ON questions(status);
