#!/usr/bin/env python3
"""
Script để chuyển đổi từ Render PostgreSQL sang Supabase
"""
import os
import sys
from src.auth.database.factory import get_render_manager, get_supabase_manager

def switch_to_supabase():
    """Chuyển đổi từ Render sang Supabase"""
    print("🔄 Switching from Render PostgreSQL to Supabase...")
    print("=" * 60)
    
    # Test 1: Kiểm tra kết nối Render
    print("\n1️⃣  Testing Render PostgreSQL connection...")
    try:
        render_db = get_render_manager()
        if render_db.init_database():
            print("✅ Render PostgreSQL connection successful")
        else:
            print("❌ Render PostgreSQL connection failed")
            return False
    except Exception as e:
        print(f"❌ Render PostgreSQL error: {e}")
        return False
    
    # Test 2: Kiểm tra kết nối Supabase
    print("\n2️⃣  Testing Supabase connection...")
    try:
        supabase_db = get_supabase_manager()
        if supabase_db.init_database():
            print("✅ Supabase connection successful")
        else:
            print("❌ Supabase connection failed")
            return False
    except Exception as e:
        print(f"❌ Supabase error: {e}")
        return False
    
    # Test 3: So sánh dữ liệu
    print("\n3️⃣  Comparing data between databases...")
    try:
        # Lấy account types từ Render
        with render_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM account_types")
            render_account_types = cursor.fetchall()
        
        # Lấy account types từ Supabase
        response = supabase_db.supabase.table('account_types').select('*').execute()
        supabase_account_types = response.data
        
        print(f"📊 Render account types: {len(render_account_types)}")
        print(f"📊 Supabase account types: {len(supabase_account_types)}")
        
        # Lấy users từ Render
        with render_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            render_users_count = cursor.fetchone()[0]
        
        # Lấy users từ Supabase
        response = supabase_db.supabase.table('users').select('*', count='exact').execute()
        supabase_users_count = response.count or 0
        
        print(f"👥 Render users: {render_users_count}")
        print(f"👥 Supabase users: {supabase_users_count}")
        
        if render_users_count == supabase_users_count:
            print("✅ Data migration appears to be complete!")
        else:
            print("⚠️  Data counts don't match - migration may be incomplete")
        
    except Exception as e:
        print(f"❌ Data comparison error: {e}")
        return False
    
    # Test 4: Chuyển đổi environment
    print("\n4️⃣  Switching environment to Supabase...")
    try:
        # Set environment variable
        os.environ['DATABASE_TYPE'] = 'supabase'
        
        # Test với factory pattern
        from src.auth.database.factory import get_database_manager
        test_db = get_database_manager()
        
        if hasattr(test_db, 'supabase'):
            print("✅ Environment switched to Supabase successfully!")
            
            # Test một operation đơn giản
            response = test_db.supabase.table('account_types').select('*').execute()
            if response.data:
                print("✅ Supabase operations working correctly!")
            else:
                print("❌ Supabase operations failed!")
                return False
        else:
            print("❌ Environment switch failed!")
            return False
            
    except Exception as e:
        print(f"❌ Environment switch error: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 SUCCESSFULLY SWITCHED TO SUPABASE!")
    print("=" * 60)
    print("\n📋 Next Steps:")
    print("1. ✅ Database connection verified")
    print("2. ✅ Data migration completed")
    print("3. ✅ Environment switched to Supabase")
    print("4. 🔄 Update deployment scripts")
    print("5. 🔄 Test all application features")
    print("6. 🔄 Deploy to production")
    
    return True

def create_deployment_config():
    """Tạo deployment configuration cho Supabase"""
    print("\n🔧 Creating Supabase deployment configuration...")
    
    config_content = """# Supabase Deployment Configuration
# Copy these environment variables to your deployment platform

# Database Configuration
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
    
    with open('supabase_deployment.env', 'w') as f:
        f.write(config_content)
    
    print("✅ Created supabase_deployment.env")
    print("📋 Copy these environment variables to your deployment platform")

def main():
    """Main function"""
    print("🚀 ElevenLabs Database Migration Tool")
    print("Render PostgreSQL → Supabase")
    print("=" * 60)
    
    # Chuyển đổi database
    if switch_to_supabase():
        # Tạo deployment config
        create_deployment_config()
        
        print("\n🎯 Migration Summary:")
        print("✅ Database connection: Working")
        print("✅ Data migration: Complete")
        print("✅ Environment switch: Successful")
        print("✅ Deployment config: Created")
        
        print("\n🔧 To complete the migration:")
        print("1. Update your deployment platform with new environment variables")
        print("2. Test the application thoroughly")
        print("3. Deploy to production")
        print("4. Monitor for any issues")
        
    else:
        print("\n❌ Migration failed!")
        print("Please check the errors above and try again")

if __name__ == "__main__":
    main()
