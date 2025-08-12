#!/usr/bin/env python3
"""
Sửa schema Supabase để khớp với manager.py
"""
import os
from supabase import create_client, Client

def setup_supabase():
    """Setup Supabase client"""
    url = "https://wjkejklrtrhubbljfrdz.supabase.co"
    key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Indqa2Vqa2xydHJodWJibGpmcmR6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTQ5NjQyNjAsImV4cCI6MjA3MDU0MDI2MH0.M8iaT_F2nk_HpnjXh0gdiKwFGb8ed3z1RU0myWSK4kg"
    return create_client(url, key)

def fix_users_table(supabase: Client):
    """Sửa bảng users để khớp với manager.py"""
    print("\n🔧 Fixing users table...")
    print("=" * 50)
    
    try:
        # SQL để sửa bảng users
        sql_commands = [
            # Xóa các cột không cần thiết
            "ALTER TABLE users DROP COLUMN IF EXISTS login_count;",
            "ALTER TABLE users DROP COLUMN IF EXISTS last_login;",
            
            # Đảm bảo các cột cần thiết tồn tại
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS device_fingerprint VARCHAR(255);",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS expires_at TIMESTAMP;",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT true;",
            
            # Reset sequence cho auth_events
            "SELECT setval('auth_events_id_seq', (SELECT COALESCE(MAX(id), 0) FROM auth_events));"
        ]
        
        for sql in sql_commands:
            print(f"Executing: {sql}")
            # Note: Supabase không hỗ trợ exec_sql trực tiếp, cần chạy trong SQL Editor
            print(f"⚠️  Cần chạy trong Supabase SQL Editor: {sql}")
        
        print("✅ Schema fix commands đã được tạo")
        print("📋 Copy các lệnh SQL trên vào Supabase SQL Editor và chạy")
        
        return True
        
    except Exception as e:
        print(f"❌ Lỗi khi fix schema: {e}")
        return False

def create_sql_script():
    """Tạo file SQL script để chạy trong Supabase"""
    print("\n📝 Creating SQL fix script...")
    print("=" * 50)
    
    sql_content = """-- Fix Supabase Schema to match manager.py
-- Run this in Supabase SQL Editor

-- Fix users table
ALTER TABLE users DROP COLUMN IF EXISTS login_count;
ALTER TABLE users DROP COLUMN IF EXISTS last_login;
ALTER TABLE users ADD COLUMN IF NOT EXISTS device_fingerprint VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS expires_at TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT true;

-- Reset sequences to avoid duplicate key errors
SELECT setval('auth_events_id_seq', (SELECT COALESCE(MAX(id), 0) FROM auth_events));
SELECT setval('users_id_seq', (SELECT COALESCE(MAX(id), 0) FROM users));
SELECT setval('user_sessions_id_seq', (SELECT COALESCE(MAX(id), 0) FROM user_sessions));
SELECT setval('admin_users_id_seq', (SELECT COALESCE(MAX(id), 0) FROM admin_users));
SELECT setval('audit_logs_id_seq', (SELECT COALESCE(MAX(id), 0) FROM audit_logs));

-- Verify schema
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'users' 
AND table_schema = 'public'
ORDER BY ordinal_position;
"""
    
    with open('fix_supabase_schema.sql', 'w') as f:
        f.write(sql_content)
    
    print("✅ Đã tạo file fix_supabase_schema.sql")
    print("📋 Copy nội dung file này vào Supabase SQL Editor và chạy")

def main():
    """Main function"""
    print("🔧 Fix Supabase Schema")
    print("=" * 60)
    
    supabase = setup_supabase()
    
    # Tạo SQL script
    create_sql_script()
    
    print("\n" + "=" * 60)
    print("📋 HƯỚNG DẪN")
    print("=" * 60)
    print("1. Mở Supabase Dashboard → SQL Editor")
    print("2. Copy nội dung từ file fix_supabase_schema.sql")
    print("3. Paste vào SQL Editor và click 'Run'")
    print("4. Sau khi chạy xong, test lại ứng dụng")
    print("\n🔧 Sau khi fix schema, chạy lại:")
    print("   py test_production_readiness.py")

if __name__ == "__main__":
    main()
