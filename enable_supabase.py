#!/usr/bin/env python3
"""
Script đơn giản để chuyển từ Render PostgreSQL sang Supabase
"""
import os

def enable_supabase():
    """Chuyển đổi sang Supabase"""
    print("🔄 Chuyển đổi sang Supabase...")
    print("=" * 50)
    
    # Set environment variables để sử dụng Supabase
    os.environ['DATABASE_TYPE'] = 'supabase'
    os.environ['SUPABASE_URL'] = 'https://wjkejklrtrhubbljfrdz.supabase.co'
    os.environ['SUPABASE_ANON_KEY'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Indqa2Vqa2xydHJodWJibGpmcmR6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTQ5NjQyNjAsImV4cCI6MjA3MDU0MDI2MH0.M8iaT_F2nk_HpnjXh0gdiKwFGb8ed3z1RU0myWSK4kg'
    
    print("✅ Đã set DATABASE_TYPE=supabase")
    print("✅ Đã set SUPABASE_URL và SUPABASE_ANON_KEY")
    print("✅ Ứng dụng sẽ tự động sử dụng Supabase thay vì Render PostgreSQL")
    
    # Test kết nối Supabase
    try:
        from src.auth.database.factory import get_database_manager
        db = get_database_manager()
        
        if hasattr(db, 'supabase'):
            print("✅ Factory pattern đã chuyển sang Supabase thành công!")
            
            # Test query đơn giản
            response = db.supabase.table('account_types').select('*').execute()
            if response.data:
                print(f"✅ Kết nối Supabase thành công! Tìm thấy {len(response.data)} account types")
                return True
            else:
                print("⚠️  Kết nối thành công nhưng không có dữ liệu")
                return True
        else:
            print("❌ Factory pattern chưa chuyển sang Supabase")
            return False
            
    except Exception as e:
        print(f"❌ Lỗi kết nối Supabase: {e}")
        return False

def create_deployment_env():
    """Tạo file .env cho deployment"""
    print("\n🔧 Tạo file deployment environment...")
    
    env_content = """# Supabase Configuration cho Deployment
DATABASE_TYPE=supabase
SUPABASE_URL=https://wjkejklrtrhubbljfrdz.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Indqa2Vqa2xydHJodWJibGpmcmR6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTQ5NjQyNjAsImV4cCI6MjA3MDU0MDI2MH0.M8iaT_F2nk_HpnjXh0gdiKwFGb8ed3z1RU0myWSK4kg

# Admin Configuration
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123

# Application Configuration
APP_ENV=production
DEBUG=false
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("✅ Đã tạo file .env")
    print("📋 Copy các environment variables này vào Render.com")

def main():
    """Main function"""
    print("🚀 Chuyển đổi sang Supabase")
    print("=" * 50)
    
    if enable_supabase():
        create_deployment_env()
        
        print("\n🎉 HOÀN THÀNH CHUYỂN ĐỔI!")
        print("=" * 50)
        print("✅ Database: Đã chuyển sang Supabase")
        print("✅ Factory Pattern: Hoạt động")
        print("✅ Environment: Đã cấu hình")
        print("✅ Deployment Config: Đã tạo")
        
        print("\n🔧 Bước tiếp theo:")
        print("1. Copy environment variables từ file .env vào Render.com")
        print("2. Deploy lại ứng dụng trên Render")
        print("3. Test kết nối và chức năng")
        
        print("\n📋 Environment Variables cho Render:")
        print("DATABASE_TYPE=supabase")
        print("SUPABASE_URL=https://wjkejklrtrhubbljfrdz.supabase.co")
        print("SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
        
    else:
        print("\n❌ Chuyển đổi thất bại!")
        print("Hãy kiểm tra lại cấu hình Supabase")

if __name__ == "__main__":
    main()
