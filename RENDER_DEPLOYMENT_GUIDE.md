# 🚀 Hướng dẫn Deploy 2 Services còn lại trên Render

## ✅ ĐÃ HOÀN THÀNH
- **Database**: `elevenlabs-auth-db` ✅
- **Files đã sửa**: Tất cả database credentials ✅

---

## 🎯 **BƯỚC TIẾP THEO: Deploy 2 Backend Services**

### 1. 🔧 **Admin Backend Service** (elevenlabs-auth-backend)

**Trên Render Dashboard:**
1. Nhấn **"New +"** → **"Web Service"**
2. **Connect Repository**: Chọn GitHub repo của bạn
3. **Name**: `elevenlabs-auth-backend`
4. **Environment**: `Python 3`
5. **Root Directory**: `my-backend` ⚠️ **QUAN TRỌNG**
6. **Build Command**: `pip install -r requirements.txt`
7. **Start Command**: `python render-admin-deploy.py`

**Environment Variables:**
```env
DATABASE_URL=postgresql://elevenlabs_auth_db_user:Dta5busSXW4WPPaasBVvjtyTXT2fXU9t@dpg-d21hsaidbo4c73e6ghe0-a/elevenlabs_auth_db_l1le
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
```

**Kết quả:** Admin Dashboard sẽ chạy tại `https://elevenlabs-auth-backend.onrender.com`

---

### 2. 🌐 **Auth API Service** (backend-elevenlab-web)

**Trên Render Dashboard:**
1. Nhấn **"New +"** → **"Web Service"**
2. **Connect Repository**: Chọn GitHub repo của bạn
3. **Name**: `backend-elevenlab-web`
4. **Environment**: `Python 3`
5. **Root Directory**: `my-backend` ⚠️ **QUAN TRỌNG**
6. **Build Command**: `pip install -r requirements.txt`
7. **Start Command**: `python render-api-deploy.py`

**Environment Variables:**
```env
DATABASE_URL=postgresql://elevenlabs_auth_db_user:Dta5busSXW4WPPaasBVvjtyTXT2fXU9t@dpg-d21hsaidbo4c73e6ghe0-a/elevenlabs_auth_db_l1le
```

**Kết quả:** Auth API sẽ chạy tại `https://backend-elevenlab-web.onrender.com`

---

## 🗄️ **TRẢ LỜI: VỀ VIỆC TẠO BẢNG DATABASE**

### ❌ **KHÔNG CẦN TẠO THỦ CÔNG!**

Hệ thống sẽ **TỰ ĐỘNG** tạo tất cả bảng khi deploy lần đầu:

1. **`account_types`** - Loại tài khoản (trial, paid)
2. **`users`** - Thông tin users 
3. **`user_sessions`** - Phiên đăng nhập
4. **`user_devices`** - Thiết bị đã đăng nhập

### 🔄 **Quy trình tự động:**
```
1. Service khởi động → 2. Kết nối database → 3. Tạo bảng nếu chưa có → 4. Ready!
```

---

## 🎯 **SAU KHI DEPLOY XONG 2 SERVICES:**

### 1. **Test Admin Dashboard:**
- Truy cập: `https://elevenlabs-auth-backend.onrender.com`
- Login với: `admin` / `admin123`

### 2. **Test Auth API:**
- Health check: `https://backend-elevenlab-web.onrender.com/health`
- API docs: `https://backend-elevenlab-web.onrender.com/docs`

### 3. **Cập nhật Main App:**
Sửa auth URLs trong main app thành:
```python
AUTH_API_URL = "https://backend-elevenlab-web.onrender.com"
ADMIN_URL = "https://elevenlabs-auth-backend.onrender.com"
```

---

## 🔧 **CÁCH HỆ THỐNG HOẠT ĐỘNG:**

```
ElevenLabs Main App
        ↓
   Auth API Service ← Admin Dashboard
        ↓
   PostgreSQL Database
```

1. **Main App** gọi Auth API để login/logout users
2. **Admin Dashboard** quản lý users qua web interface  
3. **Cả 2** đều kết nối cùng 1 PostgreSQL database 