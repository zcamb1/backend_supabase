# 🚀 Hướng dẫn Setup Supabase cho ElevenLabs Auth System

## ✅ THÔNG TIN SUPABASE ĐÃ CÓ
- **Project URL**: https://wjkejklrtrhubbljfrdz.supabase.co
- **API Key**: Đã được cấu hình trong supabase_config.py

## 📋 Bước 1: Setup Database Schema

1. Mở Supabase Dashboard: https://supabase.com/dashboard/project/wjkejklrtrhubbljfrdz
2. Vào **SQL Editor**
3. Copy toàn bộ nội dung từ file `supabase_schema.sql`
4. Paste và chạy SQL

## 📋 Bước 2: Verify Schema

Chạy script test để kiểm tra:
```bash
cd my-backend
python test_supabase_connection.py
```

## 📋 Bước 3: Import Data từ Render

Sau khi setup schema, import dữ liệu:
```bash
cd my-backend
python migrate_to_supabase.py
```

## 🔧 Environment Variables

Thông tin đã được cấu hình trong `supabase_config.py`:
```python
SUPABASE_URL = "https://wjkejklrtrhubbljfrdz.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

## 🎯 Next Steps

1. ✅ Setup Supabase Project
2. ✅ Create Database Schema (CHÍNH XÁC 100% với Render)
3. 🔄 Import Data from Render
4. 🔄 Update Application Code
5. 🔄 Test Authentication System
6. 🔄 Deploy to Production

## 📞 Troubleshooting

- **Connection errors**: Kiểm tra URL và API keys
- **Schema errors**: Chạy SQL từng phần
- **Import errors**: Kiểm tra data format
- **Permission errors**: Kiểm tra RLS policies

Generated on: 2025-08-12 09:28:12
