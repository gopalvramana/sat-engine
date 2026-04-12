-- Add picture (avatar URL) to users — populated from Google OAuth profile on login.
ALTER TABLE users ADD COLUMN IF NOT EXISTS picture TEXT;
