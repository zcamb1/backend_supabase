#!/usr/bin/env python3
"""
Migration script từ Render PostgreSQL sang Supabase
"""
import os
import json
from datetime import datetime
from supabase import create_client, Client

def migrate_to_supabase():
    """Migrate dữ liệu từ Render export sang Supabase"""
    
    print("🚀 Bắt đầu migration từ Render sang Supabase...")
    print("=" * 60)
    
    # Kiểm tra environment variables
    supabase_url = os.environ.get('SUPABASE_URL')
    supabase_key = os.environ.get('SUPABASE_ANON_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Thiếu SUPABASE_URL hoặc SUPABASE_ANON_KEY")
        print("Hãy set environment variables trước khi chạy script")
        return False
    
    # Khởi tạo Supabase client
    try:
        supabase: Client = create_client(supabase_url, supabase_key)
        print("✅ Kết nối Supabase thành công")
    except Exception as e:
        print(f"❌ Lỗi kết nối Supabase: {e}")
        return False
    
    # Tìm file export JSON
    export_file = None
    for file in os.listdir('.'):
        if file.startswith('render_export_') and file.endswith('.json'):
            export_file = file
            break
    
    if not export_file:
        print("❌ Không tìm thấy file export JSON")
        print("Hãy chạy export_render_to_supabase.py trước")
        return False
    
    print(f"📁 Tìm thấy file export: {export_file}")
    
    # Đọc dữ liệu export
    try:
        with open(export_file, 'r', encoding='utf-8') as f:
            export_data = json.load(f)
        print(f"📊 Đọc được {len(export_data)} tables")
    except Exception as e:
        print(f"❌ Lỗi đọc file export: {e}")
        return False
    
    # Migration order (để tránh foreign key conflicts)
    migration_order = [
        'account_types',
        'admin_users', 
        'users',
        'user_sessions',
        'audit_logs',
        'auth_events'
    ]
    
    success_count = 0
    total_tables = len(migration_order)
    
    for table_name in migration_order:
        if table_name not in export_data:
            print(f"⚠️  Table {table_name} không có trong export data")
            continue
        
        print(f"📤 Đang migrate table: {table_name}")
        
        try:
            table_data = export_data[table_name]
            data_to_insert = table_data['data']
            
            if not data_to_insert:
                print(f"   ℹ️  Table {table_name} không có dữ liệu")
                success_count += 1
                continue
            
            # Xử lý dữ liệu trước khi insert
            processed_data = []
            for row in data_to_insert:
                processed_row = {}
                for key, value in row.items():
                    # Xử lý datetime fields
                    if key in ['created_at', 'updated_at', 'last_login', 'timestamp', 'expires_at', 'last_activity']:
                        if value and isinstance(value, str):
                            # Convert to ISO format nếu cần
                            processed_row[key] = value
                        else:
                            processed_row[key] = None
                    else:
                        processed_row[key] = value
                processed_data.append(processed_row)
            
            # Insert data vào Supabase
            response = supabase.table(table_name).insert(processed_data).execute()
            
            if response.data:
                print(f"   ✅ Migrated {len(response.data)} rows")
                success_count += 1
            else:
                print(f"   ❌ Failed to migrate {table_name}")
                
        except Exception as e:
            print(f"   ❌ Lỗi migrate {table_name}: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 MIGRATION HOÀN THÀNH!")
    print("=" * 60)
    print(f"📊 Kết quả: {success_count}/{total_tables} tables migrated")
    
    if success_count == total_tables:
        print("✅ Tất cả tables đã được migrate thành công!")
        print("\n🔧 Bước tiếp theo:")
        print("1. Test kết nối: python test_supabase_connection.py")
        print("2. Cập nhật application để sử dụng Supabase")
        print("3. Deploy lên production")
    else:
        print("⚠️  Một số tables migration thất bại")
        print("Hãy kiểm tra logs và thử lại")
    
    return success_count == total_tables

def verify_migration():
    """Verify dữ liệu đã được migrate"""
    
    print("\n🔍 Verifying migration...")
    
    supabase_url = os.environ.get('SUPABASE_URL')
    supabase_key = os.environ.get('SUPABASE_ANON_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Không thể verify - thiếu environment variables")
        return False
    
    try:
        supabase: Client = create_client(supabase_url, supabase_key)
        
        # Check các tables chính
        tables_to_check = [
            ('account_types', 'Account Types'),
            ('users', 'Users'),
            ('user_sessions', 'User Sessions'),
            ('admin_users', 'Admin Users'),
            ('auth_events', 'Auth Events')
        ]
        
        for table_name, display_name in tables_to_check:
            try:
                response = supabase.table(table_name).select('*').execute()
                count = len(response.data) if response.data else 0
                print(f"✅ {display_name}: {count} records")
            except Exception as e:
                print(f"❌ {display_name}: Error - {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

if __name__ == "__main__":
    print("🔄 ElevenLabs Database Migration Tool")
    print("=" * 60)
    
    # Chạy migration
    if migrate_to_supabase():
        # Verify migration
        verify_migration()
    else:
        print("❌ Migration thất bại")
