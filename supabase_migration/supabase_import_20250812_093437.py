#!/usr/bin/env python3
"""
# Supabase Import Script
# Generated on 2025-08-12 09:34:48
"""
import os
import json
from supabase import create_client, Client
from typing import Dict, Any, List

class SupabaseImporter:
    def __init__(self, supabase_url: str, supabase_key: str):
        self.supabase: Client = create_client(supabase_url, supabase_key)
        
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
    
    def import_from_json(self, json_file: str):
        """Import dữ liệu từ JSON file"""
        print(f"🚀 Bắt đầu import từ {json_file}")
        
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        success_count = 0
        total_tables = len(data)
        
        for table_name, table_data in data.items():
            print(f"📤 Đang import table: {table_name}")
            if self.import_table_data(table_name, table_data['data']):
                success_count += 1
        
        print(f"\n✅ Import hoàn thành: {success_count}/{total_tables} tables")

# HƯỚNG DẪN SỬ DỤNG:
# 1. Cài đặt supabase-py: pip install supabase
# 2. Thay đổi SUPABASE_URL và SUPABASE_KEY bên dưới
# 3. Chạy script này

if __name__ == "__main__":
    # Supabase Configuration
    SUPABASE_URL = "https://wjkejklrtrhubbljfrdz.supabase.co"
    SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Indqa2Vqa2xydHJodWJibGpmcmR6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTQ5NjQyNjAsImV4cCI6MjA3MDU0MDI2MH0.M8iaT_F2nk_HpnjXh0gdiKwFGb8ed3z1RU0myWSK4kg"
    
    # Khởi tạo importer
    importer = SupabaseImporter(SUPABASE_URL, SUPABASE_KEY)
    
    # Import dữ liệu
    json_file = "supabase_migration/render_export_20250812_093437.json"
    importer.import_from_json(json_file)
