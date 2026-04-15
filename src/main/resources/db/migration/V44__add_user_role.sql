-- Add role column to users table
ALTER TABLE users ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'STUDENT';

-- Seed admin user
UPDATE users SET role = 'ADMIN' WHERE email = 'gopalvramana@gmail.com';
