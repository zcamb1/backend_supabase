-- Disable RLS temporarily for data import
ALTER TABLE users DISABLE ROW LEVEL SECURITY;
ALTER TABLE user_sessions DISABLE ROW LEVEL SECURITY;
ALTER TABLE auth_events DISABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs DISABLE ROW LEVEL SECURITY;
ALTER TABLE admin_users DISABLE ROW LEVEL SECURITY;
ALTER TABLE account_types DISABLE ROW LEVEL SECURITY;

-- Clear existing data (optional - only if you want to start fresh)
-- TRUNCATE TABLE auth_events CASCADE;
-- TRUNCATE TABLE user_sessions CASCADE;
-- TRUNCATE TABLE users CASCADE;
-- TRUNCATE TABLE admin_users CASCADE;
-- TRUNCATE TABLE audit_logs CASCADE;
-- DELETE FROM account_types WHERE id > 2; -- Keep default trial/paid types
