
-- ElevenLabs Authentication System Database Schema
-- Generated on: 2025-08-12 09:28:12
-- IDENTICAL với cấu trúc hiện tại trên Render

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Account Types Table (CHÍNH XÁC với Render)
CREATE TABLE IF NOT EXISTS account_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    duration_days INTEGER DEFAULT NULL,
    max_devices INTEGER DEFAULT 1,
    features JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Users Table (CHÍNH XÁC với Render)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    account_type_id INTEGER REFERENCES account_types(id) DEFAULT 1,
    device_fingerprint VARCHAR(255),
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

-- User Sessions Table (CHÍNH XÁC với Render)
CREATE TABLE IF NOT EXISTS user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    device_fingerprint VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

-- Admin Users Table (CHÍNH XÁC với Render)
CREATE TABLE IF NOT EXISTS admin_users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

-- Audit Logs Table (CHÍNH XÁC với Render)
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    admin_id INTEGER REFERENCES admin_users(id),
    action VARCHAR(100) NOT NULL,
    target_type VARCHAR(50),
    target_id INTEGER,
    details JSONB,
    ip_address INET,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Auth Events Table (CHÍNH XÁC với Render)
CREATE TABLE IF NOT EXISTS auth_events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    username VARCHAR(50),
    device_fingerprint VARCHAR(255),
    success BOOLEAN DEFAULT FALSE,
    details TEXT,
    ip_address INET,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance (CHÍNH XÁC với Render)
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_device ON users(device_fingerprint);
CREATE INDEX IF NOT EXISTS idx_sessions_token ON user_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_admin ON audit_logs(admin_id);
CREATE INDEX IF NOT EXISTS idx_auth_events_type ON auth_events(event_type);
CREATE INDEX IF NOT EXISTS idx_auth_events_timestamp ON auth_events(timestamp);

-- Insert default account types (CHÍNH XÁC với Render)
INSERT INTO account_types (name, duration_days, max_devices, features)
VALUES 
    ('trial', 30, 1, '{"api_usage_limit": 1000}'),
    ('paid', NULL, 1, '{"api_usage_limit": null}')
ON CONFLICT (name) DO NOTHING;

-- Create admin user (password: admin123) - CHÍNH XÁC với Render
INSERT INTO admin_users (username, password_hash, is_active)
VALUES ('admin', 'a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3', true)
ON CONFLICT (username) DO NOTHING;

-- Create RLS (Row Level Security) policies cho Supabase
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE admin_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE auth_events ENABLE ROW LEVEL SECURITY;

-- Users can only see their own data
CREATE POLICY "Users can view own data" ON users
    FOR SELECT USING (auth.uid()::text = id::text);

CREATE POLICY "Users can update own data" ON users
    FOR UPDATE USING (auth.uid()::text = id::text);

-- Sessions policies
CREATE POLICY "Users can view own sessions" ON user_sessions
    FOR SELECT USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can insert own sessions" ON user_sessions
    FOR INSERT WITH CHECK (auth.uid()::text = user_id::text);

-- Admin can view all data (for admin interface)
CREATE POLICY "Admin can view all users" ON users
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM admin_users 
            WHERE username = current_user 
            AND is_active = true
        )
    );

CREATE POLICY "Admin can view all sessions" ON user_sessions
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM admin_users 
            WHERE username = current_user 
            AND is_active = true
        )
    );

CREATE POLICY "Admin can view all logs" ON audit_logs
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM admin_users 
            WHERE username = current_user 
            AND is_active = true
        )
    );

CREATE POLICY "Admin can view all events" ON auth_events
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM admin_users 
            WHERE username = current_user 
            AND is_active = true
        )
    );

-- Grant necessary permissions
GRANT USAGE ON SCHEMA public TO anon, authenticated;
GRANT ALL ON ALL TABLES IN SCHEMA public TO anon, authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO anon, authenticated;

-- Enable realtime for tables that need it
ALTER PUBLICATION supabase_realtime ADD TABLE users;
ALTER PUBLICATION supabase_realtime ADD TABLE user_sessions;
ALTER PUBLICATION supabase_realtime ADD TABLE audit_logs;
ALTER PUBLICATION supabase_realtime ADD TABLE auth_events;
