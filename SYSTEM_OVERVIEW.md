# 🏗️ ElevenLabs Authentication System - Tổng quan hệ thống

## 📋 **MỤC ĐÍCH CỦA `my-backend/`**

Thư mục này chứa **AUTHENTICATION SYSTEM** hoàn chỉnh cho ElevenLabs Tool, bao gồm:

### 🔧 **2 SERVICE CHÍNH:**

#### 1. 🎯 **Admin Web Interface** (`admin_main.py`)
- **Chức năng**: Dashboard web để quản lý users
- **Port**: 10000
- **URL sau deploy**: `https://elevenlabs-auth-backend.onrender.com`
- **Features**:
  - 👥 Tạo/sửa/xóa users
  - 📊 Thống kê và analytics  
  - 🔍 Monitor system health
  - 📱 Quản lý sessions và devices

#### 2. 🌐 **Auth API Server** (`src/auth/server/api.py`)
- **Chức năng**: API endpoints cho main app
- **Port**: 8000  
- **URL sau deploy**: `https://backend-elevenlab-web.onrender.com`
- **Features**:
  - 🔐 Login/logout endpoints
  - ✅ Session verification
  - 👤 User management API
  - 📋 Health checks

---

## 🔄 **LUỒNG HOẠT ĐỘNG**

```
📱 Main ElevenLabs App
         ↓ (login request)
🌐 Auth API Server (backend-elevenlab-web.onrender.com)
         ↓ (check credentials)
🗄️  PostgreSQL Database (elevenlabs_auth_db_l1le)
         ↓ (return session token)
📱 Main App (lưu session, sử dụng API)

👨‍💼 Admin 
         ↓ (manage users)
🎯 Admin Interface (elevenlabs-auth-backend.onrender.com)
         ↓ (CRUD operations)
🗄️  PostgreSQL Database
```

---

## 🗄️ **DATABASE CONNECTION**

### ✅ **ĐÃ ĐƯỢC CẤU HÌNH SẴN:**
- **Host**: `dpg-d21hsaidbo4c73e6ghe0-a`
- **Database**: `elevenlabs_auth_db_l1le`
- **Username**: `elevenlabs_auth_db_user`
- **Password**: `Dta5busSXW4WPPaasBVvjtyTXT2fXU9t`

### 🔄 **AUTO-INITIALIZATION:**
Khi service start lần đầu, system sẽ **TỰ ĐỘNG**:
1. Kết nối database
2. Tạo tất cả tables cần thiết
3. Insert default data (account types)
4. Sẵn sàng phục vụ

---

## 📊 **DATABASE SCHEMA TỰ ĐỘNG TẠO**

```sql
-- Loại tài khoản
account_types (id, name, duration_days, max_devices, features)

-- Thông tin users  
users (id, username, password_hash, account_type_id, device_fingerprint, expires_at, created_at, is_active)

-- Phiên đăng nhập
user_sessions (id, user_id, session_token, device_fingerprint, expires_at, created_at, last_activity, is_active)

-- Admin accounts
admin_users (id, username, password_hash, created_at, last_login, is_active)

-- Audit logs
audit_logs (id, admin_id, action, target_type, target_id, details, ip_address, created_at)

-- Analytics events
auth_events (id, event_type, username, device_fingerprint, success, details, ip_address, timestamp)
```

---

## 🚀 **DEPLOYMENT TRÊN RENDER**

### **Service 1: Admin Backend**
```yaml
Name: elevenlabs-auth-backend
Root Directory: my-backend
Build: pip install -r requirements.txt  
Start: python admin_main.py
Environment:
  DATABASE_URL: postgresql://elevenlabs_auth_db_user:Dta5busSXW4WPPaasBVvjtyTXT2fXU9t@dpg-d21hsaidbo4c73e6ghe0-a/elevenlabs_auth_db_l1le
  ADMIN_USERNAME: admin
  ADMIN_PASSWORD: admin123
```

### **Service 2: Auth API**
```yaml
Name: backend-elevenlab-web  
Root Directory: my-backend
Build: pip install -r requirements.txt
Start: uvicorn src.auth.server.api:app --host 0.0.0.0 --port $PORT
Environment:
  DATABASE_URL: postgresql://elevenlabs_auth_db_user:Dta5busSXW4WPPaasBVvjtyTXT2fXU9t@dpg-d21hsaidbo4c73e6ghe0-a/elevenlabs_auth_db_l1le
```

---

## 🧪 **TEST HỆ THỐNG**

### **Trước khi deploy:**
```bash
cd my-backend
python test-database.py
python init_db.py
```

### **Sau khi deploy:**
1. 🎯 Test Admin: `https://elevenlabs-auth-backend.onrender.com/admin/dashboard`
2. 🌐 Test API: `https://backend-elevenlab-web.onrender.com/docs`
3. 💓 Health check: `https://backend-elevenlab-web.onrender.com/health`

---

## 🔗 **TÍCH HỢP VỚI MAIN APP**

### **Cập nhật trong Main ElevenLabs Tool:**

```python
# Thay localhost:8000 bằng URL mới:
AUTH_API_URL = "https://backend-elevenlab-web.onrender.com"

# Login request:
response = requests.post(f"{AUTH_API_URL}/auth/login", {
    "username": "user", 
    "password": "pass"
})

# Verify session:
response = requests.post(f"{AUTH_API_URL}/auth/verify", {
    "session_token": "token"
})
```

---

## 🔐 **SECURITY FEATURES**

- 🔒 **Device Binding**: Mỗi account chỉ dùng được 1 device
- ⏰ **Session Timeout**: 24 giờ tự động logout
- 🛡️ **Password Hashing**: SHA256 hashing
- 📱 **Device Fingerprinting**: Unique device identification
- 🔍 **Audit Logging**: Track tất cả admin actions
- 📊 **Analytics**: Monitor login patterns

---

## ❓ **CÂU HỎI THƯỜNG GẶP**

### **Q: Có cần tạo bảng thủ công không?**
A: ❌ KHÔNG! System tự động tạo tất cả khi start lần đầu.

### **Q: Database credentials ở đâu?**  
A: ✅ Đã cấu hình sẵn trong tất cả files với thông tin mới.

### **Q: Main app kết nối như thế nào?**
A: 🔗 Main app gọi Auth API endpoints để login/verify users.

### **Q: Admin dashboard để làm gì?**
A: 👨‍💼 Quản lý users, xem analytics, monitor system health.

### **Q: Có an toàn không?**
A: 🛡️ Có đầy đủ security features: device binding, session timeout, audit logs.

---

**🎯 TÓM LẠI: Hệ thống hoạt động hoàn toàn tự động, chỉ cần deploy 2 services lên Render và cập nhật API URL trong main app!** 