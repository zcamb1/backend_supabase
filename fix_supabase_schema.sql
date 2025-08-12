-- Fix Supabase Schema to match manager.py
-- Run this in Supabase SQL Editor

-- Fix users table
ALTER TABLE users DROP COLUMN IF EXISTS login_count;
ALTER TABLE users DROP COLUMN IF EXISTS last_login;
ALTER TABLE users ADD COLUMN IF NOT EXISTS device_fingerprint VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS expires_at TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT true;

-- Reset sequences to avoid duplicate key errors (only if table has data)
SELECT setval('auth_events_id_seq', (SELECT COALESCE(MAX(id), 1) FROM auth_events));
SELECT setval('users_id_seq', (SELECT COALESCE(MAX(id), 1) FROM users));
SELECT setval('user_sessions_id_seq', (SELECT COALESCE(MAX(id), 1) FROM user_sessions));
SELECT setval('admin_users_id_seq', (SELECT COALESCE(MAX(id), 1) FROM admin_users));
SELECT setval('audit_logs_id_seq', (SELECT COALESCE(MAX(id), 1) FROM audit_logs));

-- Verify schema
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'users' 
AND table_schema = 'public'
ORDER BY ordinal_position;
