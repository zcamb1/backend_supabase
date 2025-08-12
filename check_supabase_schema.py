#!/usr/bin/env python3
"""
Kiểm tra schema Supabase để debug lỗi
"""
import os
from supabase import create_client, Client

def setup_supabase():
    """Setup Supabase client"""
    url = "https://wjkejklrtrhubbljfrdz.supabase.co"
    key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Indqa2Vqa2xydHJodWJibGpmcmR6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTQ5NjQyNjAsImV4cCI6MjA3MDU0MDI2MH0.M8iaT_F2nk_HpnjXh0gdiKwFGb8ed3z1RU0myWSK4kg"
    return create_client(url, key)

def check_table_schema(supabase: Client, table_name: str):
    """Kiểm tra schema của table"""
    print(f"\n🔍 Checking schema for table: {table_name}")
    print("=" * 50)
    
    try:
        # Query để lấy thông tin schema
        query = f"""
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns 
        WHERE table_name = '{table_name}' 
        AND table_schema = 'public'
        ORDER BY ordinal_position;
        """
        
        response = supabase.rpc('exec_sql', {'sql': query}).execute()
        
        if response.data:
            print(f"📋 Schema cho table '{table_name}':")
            for col in response.data:
                nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                default = f"DEFAULT {col['column_default']}" if col['column_default'] else ""
                print(f"   - {col['column_name']}: {col['data_type']} {nullable} {default}")
        else:
            print(f"❌ Không thể lấy schema cho table '{table_name}'")
            
    except Exception as e:
        print(f"❌ Lỗi khi kiểm tra schema: {e}")

def check_table_data(supabase: Client, table_name: str):
    """Kiểm tra dữ liệu của table"""
    print(f"\n📊 Checking data for table: {table_name}")
    print("=" * 50)
    
    try:
        response = supabase.table(table_name).select('*', count='exact').execute()
        count = response.count or 0
        print(f"✅ Tìm thấy {count} rows trong table '{table_name}'")
        
        if response.data and len(response.data) > 0:
            print("📝 Sample data:")
            for i, row in enumerate(response.data[:3]):  # Chỉ hiển thị 3 rows đầu
                print(f"   Row {i+1}: {row}")
        else:
            print("⚠️  Table không có dữ liệu")
            
    except Exception as e:
        print(f"❌ Lỗi khi kiểm tra dữ liệu: {e}")

def test_account_types_query(supabase: Client):
    """Test query account_types"""
    print(f"\n🧪 Testing account_types query")
    print("=" * 50)
    
    try:
        # Test 1: Query trực tiếp
        response = supabase.table('account_types').select('*').execute()
        print(f"✅ Direct query: Tìm thấy {len(response.data)} account types")
        
        # Test 2: Query với điều kiện name = 'trial'
        response = supabase.table('account_types').select('*').eq('name', 'trial').execute()
        print(f"✅ Query với name='trial': Tìm thấy {len(response.data)} results")
        
        if response.data:
            print(f"   Trial account: {response.data[0]}")
        
        # Test 3: Query với điều kiện name = 'paid'
        response = supabase.table('account_types').select('*').eq('name', 'paid').execute()
        print(f"✅ Query với name='paid': Tìm thấy {len(response.data)} results")
        
        if response.data:
            print(f"   Paid account: {response.data[0]}")
            
    except Exception as e:
        print(f"❌ Lỗi khi test account_types: {e}")

def main():
    """Main function"""
    print("🔍 Checking Supabase Schema and Data")
    print("=" * 60)
    
    supabase = setup_supabase()
    
    # Kiểm tra các tables chính
    tables = ['account_types', 'users', 'user_sessions', 'admin_users', 'audit_logs', 'auth_events']
    
    for table in tables:
        check_table_schema(supabase, table)
        check_table_data(supabase, table)
    
    # Test đặc biệt cho account_types
    test_account_types_query(supabase)
    
    print("\n" + "=" * 60)
    print("📋 SUMMARY")
    print("=" * 60)
    print("✅ Schema và dữ liệu đã được kiểm tra")
    print("🔧 Nếu có lỗi, hãy so sánh với schema trong src/auth/database/manager.py")

if __name__ == "__main__":
    main()
