# 🚀 Hướng dẫn Deploy Backend lên Render với Supabase

## ✅ **MỤC TIÊU**
Deploy backend lên Render để admin dashboard có thể kết nối đến Supabase database.

## 📋 **TRƯỚC KHI DEPLOY**

### 1. ✅ **Kiểm tra Supabase đã sẵn sàng**
- Supabase project: `https://wjkejklrtrhubbljfrdz.supabase.co`
- Database schema đã được tạo và import dữ liệu
- API key đã được cấu hình

### 2. ✅ **Kiểm tra code đã được sửa**
- `admin_main.py` - Sử dụng Supabase
- `render-admin-deploy.py` - Sử dụng Supabase  
- `render-api-deploy.py` - Sử dụng Supabase
- `src/auth/database/factory.py` - Factory pattern hoạt động

---

## 🚀 **BƯỚC 1: DEPLOY ADMIN BACKEND**

### Trên Render Dashboard:
1. **Nhấn "New +"** → **"Web Service"**
2. **Connect Repository**: Chọn GitHub repo của bạn
3. **Name**: `elevenlabs-admin-backend`
4. **Environment**: `Python 3`
5. **Root Directory**: `my-backend` ⚠️ **QUAN TRỌNG**
6. **Build Command**: `pip install -r requirements.txt`
7. **Start Command**: `python render-admin-deploy.py`

### Environment Variables:
```env
DATABASE_TYPE=supabase
SUPABASE_URL=https://wjkejklrtrhubbljfrdz.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Indqa2Vqa2xydHJodWJibGpmcmR6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTQ5NjQyNjAsImV4cCI6MjA3MDU0MDI2MH0.M8iaT_F2nk_HpnjXh0gdiKwFGb8ed3z1RU0myWSK4kg
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
```

**Kết quả:** Admin Dashboard sẽ chạy tại `https://elevenlabs-admin-backend.onrender.com`

---

## 🚀 **BƯỚC 2: DEPLOY AUTH API**

### Trên Render Dashboard:
1. **Nhấn "New +"** → **"Web Service"**
2. **Connect Repository**: Chọn GitHub repo của bạn
3. **Name**: `elevenlabs-auth-api`
4. **Environment**: `Python 3`
5. **Root Directory**: `my-backend` ⚠️ **QUAN TRỌNG**
6. **Build Command**: `pip install -r requirements.txt`
7. **Start Command**: `python render-api-deploy.py`

### Environment Variables:
```env
DATABASE_TYPE=supabase
SUPABASE_URL=https://wjkejklrtrhubbljfrdz.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Indqa2Vqa2xydHJodWJibGpmcmR6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTQ5NjQyNjAsImV4cCI6MjA3MDU0MDI2MH0.M8iaT_F2nk_HpnjXh0gdiKwFGb8ed3z1RU0myWSK4kg
```

**Kết quả:** Auth API sẽ chạy tại `https://elevenlabs-auth-api.onrender.com`

---

## 🧪 **BƯỚC 3: TEST SAU KHI DEPLOY**

### 1. **Test Admin Dashboard:**
```bash
# Truy cập admin dashboard
https://elevenlabs-admin-backend.onrender.com

# Login với:
Username: admin
Password: admin123
```

### 2. **Test Auth API:**
```bash
# Health check
https://elevenlabs-auth-api.onrender.com/health

# API documentation
https://elevenlabs-auth-api.onrender.com/docs

# Test login endpoint
curl -X POST "https://elevenlabs-auth-api.onrender.com/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"test123","device_info":{"fingerprint":"test"}}'
```

### 3. **Test Database Connection:**
- Admin dashboard sẽ hiển thị users từ Supabase
- Auth API sẽ xác thực users từ Supabase
- Tất cả operations sẽ được lưu vào Supabase

---

## 🔧 **BƯỚC 4: CẬP NHẬT MAIN APP**

Sau khi deploy thành công, cập nhật main app để sử dụng API mới:

### Cập nhật URLs trong main app:
```python
# Thay đổi từ localhost thành Render URLs
AUTH_API_URL = "https://elevenlabs-auth-api.onrender.com"
ADMIN_URL = "https://elevenlabs-admin-backend.onrender.com"
```

### Hoặc sử dụng script update:
```bash
python update_backend_url.py https://elevenlabs-auth-api.onrender.com
```

---

## 🗂️ **CẤU TRÚC HỆ THỐNG SAU DEPLOY**

```
ElevenLabs Main App
        ↓
   Auth API (Render) ← Admin Dashboard (Render)
        ↓
   Supabase Database
```

1. **Main App** gọi Auth API trên Render
2. **Auth API** kết nối Supabase để xác thực
3. **Admin Dashboard** quản lý users qua Supabase
4. **Tất cả** đều sử dụng cùng 1 Supabase database

---

## ⚠️ **LƯU Ý QUAN TRỌNG**

### 1. **Environment Variables**
- Đảm bảo set đúng `DATABASE_TYPE=supabase`
- Copy chính xác `SUPABASE_URL` và `SUPABASE_ANON_KEY`

### 2. **Root Directory**
- Phải set `my-backend` (không phải root của repo)
- Đảm bảo `requirements.txt` có trong `my-backend/`

### 3. **Database Schema**
- Supabase đã có đầy đủ schema và dữ liệu
- Không cần tạo bảng thủ công

### 4. **CORS Settings**
- Render services sẽ tự động handle CORS
- Main app có thể gọi API từ Render

---

## 🆘 **TROUBLESHOOTING**

### Nếu Admin Dashboard không load:
1. Kiểm tra environment variables
2. Kiểm tra logs trong Render dashboard
3. Test Supabase connection

### Nếu Auth API lỗi:
1. Kiểm tra `DATABASE_TYPE=supabase`
2. Verify Supabase credentials
3. Test database connection

### Nếu Main App không kết nối:
1. Update API URLs
2. Kiểm tra CORS settings
3. Test API endpoints

---

## 📊 **MONITORING**

### Render Dashboard:
- Health checks tự động
- Logs real-time
- Performance metrics

### Supabase Dashboard:
- Database queries
- API usage
- Real-time subscriptions

---

## 🎉 **HOÀN THÀNH**

Sau khi deploy thành công:
- ✅ Admin dashboard chạy trên Render
- ✅ Auth API chạy trên Render  
- ✅ Cả 2 đều kết nối Supabase
- ✅ Main app có thể sử dụng backend mới
- ✅ Hệ thống hoàn toàn cloud-based

Generated on: 2025-08-12
