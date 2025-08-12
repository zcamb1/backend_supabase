#!/usr/bin/env python3
"""
Fixed Import Script with correct order
"""
import os
import json
from supabase import create_client, Client
from typing import Dict, Any, List

class FixedSupabaseImporter:
    def __init__(self, supabase_url: str, supabase_key: str):
        self.supabase: Client = create_client(supabase_url, supabase_key)
        
    def clear_table_data(self, table_name: str):
        """Clear existing data from table"""
        try:
            self.supabase.table(table_name).delete().neq('id', 0).execute()
            print(f"🗑️  Cleared table {table_name}")
            return True
        except Exception as e:
            print(f"⚠️  Could not clear {table_name}: {e}")
            return False
    
    def import_table_data(self, table_name: str, data: List[Dict[str, Any]]):
        """Import dữ liệu vào Supabase table"""
        try:
            if data:
                result = self.supabase.table(table_name).insert(data).execute()
                print(f"✅ Imported {len(data)} rows vào table {table_name}")
                return True
            else:
                print(f"ℹ️  Table {table_name} không có dữ liệu")
                return True
        except Exception as e:
            print(f"❌ Lỗi import table {table_name}: {e}")
            return False
    
    def import_with_correct_order(self, json_file: str):
        """Import dữ liệu theo thứ tự đúng để tránh foreign key errors"""
        print(f"🚀 Bắt đầu import từ {json_file}")
        
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Thứ tự import đúng (từ ít dependency đến nhiều dependency)
        import_order = [
            'account_types',  # No dependencies
            'users',          # Depends on account_types
            'admin_users',    # No dependencies  
            'user_sessions',  # Depends on users
            'auth_events',    # No dependencies
            'audit_logs'      # Depends on admin_users
        ]
        
        success_count = 0
        total_tables = len(import_order)
        
        for table_name in import_order:
            if table_name in data:
                print(f"\n📤 Đang import table: {table_name}")
                
                # Clear existing data first (except account_types)
                if table_name != 'account_types':
                    self.clear_table_data(table_name)
                
                if self.import_table_data(table_name, data[table_name]['data']):
                    success_count += 1
            else:
                print(f"⚠️  Table {table_name} không tìm thấy trong export data")
        
        print(f"\n✅ Import hoàn thành: {success_count}/{total_tables} tables")

if __name__ == "__main__":
    # Supabase Configuration
    SUPABASE_URL = "https://wjkejklrtrhubbljfrdz.supabase.co"
    SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Indqa2Vqa2xydHJodWJibGpmcmR6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTQ5NjQyNjAsImV4cCI6MjA3MDU0MDI2MH0.M8iaT_F2nk_HpnjXh0gdiKwFGb8ed3z1RU0myWSK4kg"
    
    # Khởi tạo importer
    importer = FixedSupabaseImporter(SUPABASE_URL, SUPABASE_KEY)
    
    # Import dữ liệu
    json_file = "supabase_migration/render_export_20250812_093437.json"
    importer.import_with_correct_order(json_file)
