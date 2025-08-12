#!/usr/bin/env python3
"""
Script để export dữ liệu từ Render PostgreSQL database và chuẩn bị cho Supabase
"""
import psycopg2
import psycopg2.extras
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any
import subprocess
import urllib.parse

class RenderToSupabaseExporter:
    def __init__(self):
        # Render PostgreSQL connection details
        self.render_config = {
            'host': 'dpg-d21hsaidbo4c73e6ghe0-a.singapore-postgres.render.com',
            'port': 5432,
            'database': 'elevenlabs_auth_db_l1le',
            'username': 'elevenlabs_auth_db_user',
            'password': 'Dta5busSXW4WPPaasBVvjtyTXT2fXU9t'
        }
        
        # Output directory
        self.output_dir = 'supabase_migration'
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Timestamp for file naming
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
    def get_connection(self):
        """Kết nối đến Render PostgreSQL database"""
        try:
            conn = psycopg2.connect(
                host=self.render_config['host'],
                port=self.render_config['port'],
                database=self.render_config['database'],
                user=self.render_config['username'],
                password=self.render_config['password']
            )
            print(f"✅ Kết nối thành công đến Render PostgreSQL database")
            return conn
        except Exception as e:
            print(f"❌ Lỗi kết nối database: {e}")
            return None
    
    def get_table_list(self, conn):
        """Lấy danh sách tất cả tables trong database"""
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """)
            tables = [row[0] for row in cursor.fetchall()]
            cursor.close()
            return tables
        except Exception as e:
            print(f"❌ Lỗi lấy danh sách tables: {e}")
            return []
    
    def export_table_data(self, conn, table_name: str) -> Dict[str, Any]:
        """Export dữ liệu từ một table"""
        try:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            # Lấy schema của table
            cursor.execute(f"""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = '{table_name}' 
                AND table_schema = 'public'
                ORDER BY ordinal_position
            """)
            schema = cursor.fetchall()
            
            # Lấy dữ liệu
            cursor.execute(f"SELECT * FROM {table_name}")
            data = cursor.fetchall()
            
            # Convert to list of dicts
            table_data = []
            for row in data:
                row_dict = {}
                for key, value in row.items():
                    if isinstance(value, datetime):
                        row_dict[key] = value.isoformat()
                    else:
                        row_dict[key] = value
                table_data.append(row_dict)
            
            cursor.close()
            
            return {
                'table_name': table_name,
                'schema': [dict(col) for col in schema],
                'data': table_data,
                'row_count': len(table_data)
            }
            
        except Exception as e:
            print(f"❌ Lỗi export table {table_name}: {e}")
            return None
    
    def export_all_data(self):
        """Export tất cả dữ liệu từ database"""
        print("🚀 Bắt đầu export dữ liệu từ Render PostgreSQL...")
        
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            # Lấy danh sách tables
            tables = self.get_table_list(conn)
            print(f"📋 Tìm thấy {len(tables)} tables: {', '.join(tables)}")
            
            all_data = {}
            total_rows = 0
            
            # Export từng table
            for table_name in tables:
                print(f"📤 Đang export table: {table_name}")
                table_data = self.export_table_data(conn, table_name)
                
                if table_data:
                    all_data[table_name] = table_data
                    total_rows += table_data['row_count']
                    print(f"   ✅ {table_data['row_count']} rows exported")
                else:
                    print(f"   ❌ Failed to export {table_name}")
            
            # Lưu dữ liệu JSON
            json_file = os.path.join(self.output_dir, f'render_export_{self.timestamp}.json')
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(all_data, f, indent=2, ensure_ascii=False)
            
            print(f"\n✅ Export hoàn thành!")
            print(f"📁 File: {json_file}")
            print(f"📊 Tổng cộng: {len(tables)} tables, {total_rows} rows")
            
            return True
            
        except Exception as e:
            print(f"❌ Lỗi export: {e}")
            return False
        finally:
            conn.close()
    
    def create_sql_dump(self):
        """Tạo SQL dump file sử dụng pg_dump"""
        print("\n🗄️  Tạo SQL dump file...")
        
        # Tạo connection string
        conn_string = f"postgresql://{self.render_config['username']}:{self.render_config['password']}@{self.render_config['host']}:{self.render_config['port']}/{self.render_config['database']}"
        
        # Tên file output
        sql_file = os.path.join(self.output_dir, f'render_dump_{self.timestamp}.sql')
        
        try:
            # Sử dụng pg_dump command
            cmd = [
                'pg_dump',
                '--verbose',
                '--clean',
                '--no-owner',
                '--no-privileges',
                '--data-only',  # Chỉ export data, không export schema
                f'--file={sql_file}',
                conn_string
            ]
            
            print(f"🔄 Đang chạy: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ SQL dump tạo thành công: {sql_file}")
                return sql_file
            else:
                print(f"❌ Lỗi pg_dump: {result.stderr}")
                return None
                
        except FileNotFoundError:
            print("❌ pg_dump không tìm thấy. Hãy cài đặt PostgreSQL client tools.")
            return None
        except Exception as e:
            print(f"❌ Lỗi tạo SQL dump: {e}")
            return None
    
    def create_supabase_import_script(self):
        """Tạo script để import vào Supabase"""
        print("\n🔧 Tạo Supabase import script...")
        
        script_content = f'''#!/usr/bin/env python3
"""
# Supabase Import Script
# Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
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
                print(f"✅ Imported {{len(data)}} rows vào table {{table_name}}")
                return True
            else:
                print(f"ℹ️  Table {{table_name}} không có dữ liệu")
                return True
        except Exception as e:
            print(f"❌ Lỗi import table {{table_name}}: {{e}}")
            return False
    
    def import_from_json(self, json_file: str):
        """Import dữ liệu từ JSON file"""
        print(f"🚀 Bắt đầu import từ {{json_file}}")
        
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        success_count = 0
        total_tables = len(data)
        
        for table_name, table_data in data.items():
            print(f"📤 Đang import table: {{table_name}}")
            if self.import_table_data(table_name, table_data['data']):
                success_count += 1
        
        print(f"\\n✅ Import hoàn thành: {{success_count}}/{{total_tables}} tables")

# HƯỚNG DẪN SỬ DỤNG:
# 1. Cài đặt supabase-py: pip install supabase
# 2. Thay đổi SUPABASE_URL và SUPABASE_KEY bên dưới
# 3. Chạy script này

if __name__ == "__main__":
    # ⚠️  THAY ĐỔI THÔNG TIN NÀY
    SUPABASE_URL = "your_supabase_url_here"
    SUPABASE_KEY = "your_supabase_anon_key_here"
    
    # Khởi tạo importer
    importer = SupabaseImporter(SUPABASE_URL, SUPABASE_KEY)
    
    # Import dữ liệu
    json_file = "render_export_{self.timestamp}.json"
    importer.import_from_json(json_file)
'''
        
        script_file = os.path.join(self.output_dir, f'supabase_import_{self.timestamp}.py')
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        print(f"✅ Supabase import script tạo thành công: {script_file}")
        return script_file
    
    def create_migration_guide(self):
        """Tạo hướng dẫn migration"""
        guide_content = f'''# 🚀 Hướng dẫn Migration từ Render PostgreSQL sang Supabase

## 📋 Tổng quan
- **Nguồn**: Render PostgreSQL Database
- **Đích**: Supabase PostgreSQL
- **Thời gian tạo**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📁 Files đã tạo
1. `render_export_{self.timestamp}.json` - Dữ liệu JSON
2. `render_dump_{self.timestamp}.sql` - SQL dump file
3. `supabase_import_{self.timestamp}.py` - Script import

## 🔧 Bước 1: Chuẩn bị Supabase
1. Tạo project mới trên Supabase
2. Lấy URL và API key từ Settings > API
3. Tạo các tables cần thiết (có thể dùng SQL Editor)

## 🔧 Bước 2: Import dữ liệu
### Phương pháp 1: Sử dụng Python script
```bash
# Cài đặt dependencies
pip install supabase

# Chỉnh sửa thông tin trong supabase_import_{self.timestamp}.py
# Chạy script
python supabase_import_{self.timestamp}.py
```

### Phương pháp 2: Sử dụng SQL dump
1. Mở Supabase SQL Editor
2. Copy nội dung từ render_dump_{self.timestamp}.sql
3. Paste và chạy

## 🔧 Bước 3: Cập nhật ứng dụng
1. Thay đổi connection string trong config
2. Test kết nối
3. Verify dữ liệu

## ⚠️  Lưu ý quan trọng
- Backup dữ liệu trước khi migration
- Test trên môi trường dev trước
- Kiểm tra constraints và indexes
- Update application code nếu cần

## 🆘 Troubleshooting
- Nếu có lỗi foreign key: Disable triggers tạm thời
- Nếu có lỗi unique constraint: Xử lý duplicate data
- Nếu có lỗi data type: Convert data types phù hợp

## 📞 Hỗ trợ
Nếu gặp vấn đề, hãy kiểm tra:
1. Supabase connection settings
2. Table schemas compatibility
3. Data format issues
'''
        
        guide_file = os.path.join(self.output_dir, f'migration_guide_{self.timestamp}.md')
        with open(guide_file, 'w', encoding='utf-8') as f:
            f.write(guide_content)
        
        print(f"✅ Migration guide tạo thành công: {guide_file}")
        return guide_file
    
    def run_full_export(self):
        """Chạy toàn bộ quá trình export"""
        print("🎯 Bắt đầu quá trình export từ Render sang Supabase...")
        print("=" * 60)
        
        # 1. Export JSON data
        if not self.export_all_data():
            print("❌ Export JSON data thất bại")
            return False
        
        # 2. Tạo SQL dump
        sql_file = self.create_sql_dump()
        
        # 3. Tạo Supabase import script
        script_file = self.create_supabase_import_script()
        
        # 4. Tạo migration guide
        guide_file = self.create_migration_guide()
        
        print("\n" + "=" * 60)
        print("🎉 HOÀN THÀNH EXPORT!")
        print("=" * 60)
        print(f"📁 Output directory: {self.output_dir}")
        print(f"📄 Files đã tạo:")
        print(f"   - render_export_{self.timestamp}.json")
        if sql_file:
            print(f"   - render_dump_{self.timestamp}.sql")
        print(f"   - supabase_import_{self.timestamp}.py")
        print(f"   - migration_guide_{self.timestamp}.md")
        print(f"\n📖 Đọc migration_guide_{self.timestamp}.md để biết cách import vào Supabase")
        
        return True

def main():
    """Main function"""
    exporter = RenderToSupabaseExporter()
    exporter.run_full_export()

if __name__ == "__main__":
    main()
