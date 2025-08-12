#!/usr/bin/env python3
"""
Test script để kiểm tra kết nối Supabase
"""
import os
import sys
from supabase import create_client, Client
from typing import Dict, Any

# Import config
sys.path.append('.')
from supabase_config import SUPABASE_URL, SUPABASE_ANON_KEY

def test_supabase_connection():
    """Test kết nối đến Supabase"""
    
    try:
        # Tạo client
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        
        # Test connection bằng cách query account_types
        response = supabase.table('account_types').select('*').execute()
        
        if response.data:
            print("✅ Kết nối Supabase thành công!")
            print(f"📊 Tìm thấy {len(response.data)} account types:")
            for account_type in response.data:
                print(f"   - {account_type['name']} (max devices: {account_type['max_devices']})")
            return True
        else:
            print("⚠️  Kết nối thành công nhưng không có dữ liệu")
            return True
            
    except Exception as e:
        print(f"❌ Lỗi kết nối Supabase: {e}")
        return False

def test_admin_user():
    """Test admin user"""
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        
        # Check admin user exists
        response = supabase.table('admin_users').select('*').eq('username', 'admin').execute()
        
        if response.data:
            print("✅ Admin user tồn tại")
            return True
        else:
            print("⚠️  Admin user chưa được tạo")
            return False
            
    except Exception as e:
        print(f"❌ Lỗi kiểm tra admin user: {e}")
        return False

def test_tables_structure():
    """Test cấu trúc tables"""
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        
        tables_to_check = [
            'account_types',
            'users', 
            'user_sessions',
            'admin_users',
            'audit_logs',
            'auth_events'
        ]
        
        print("🔍 Kiểm tra cấu trúc tables...")
        for table in tables_to_check:
            try:
                response = supabase.table(table).select('*').limit(1).execute()
                print(f"   ✅ Table {table} exists")
            except Exception as e:
                print(f"   ❌ Table {table} error: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Lỗi kiểm tra tables: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Supabase Connection...")
    print("=" * 50)
    
    # Test connection
    if test_supabase_connection():
        # Test admin user
        test_admin_user()
        
        # Test tables structure
        test_tables_structure()
        
        print("\n🎉 Supabase setup hoàn thành!")
        print("Bạn có thể tiếp tục import dữ liệu từ Render")
    else:
        print("\n❌ Supabase setup thất bại")
        print("Hãy kiểm tra lại connection settings")
