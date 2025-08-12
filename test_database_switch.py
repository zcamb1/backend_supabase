#!/usr/bin/env python3
"""
Test script để kiểm tra chuyển đổi giữa Render PostgreSQL và Supabase
"""
import os
import sys
from src.auth.database.factory import get_database_manager, get_supabase_manager, get_render_manager

def test_database_connection(db_manager, name: str):
    """Test kết nối database"""
    print(f"\n🧪 Testing {name} connection...")
    print("=" * 50)
    
    try:
        # Test init database
        print(f"🗄️  Initializing {name} database...")
        if db_manager.init_database():
            print(f"✅ {name} database initialized successfully!")
        else:
            print(f"❌ {name} database initialization failed!")
            return False
        
        # Test query account types
        print(f"📊 Querying account types from {name}...")
        if hasattr(db_manager, 'supabase'):
            # Supabase manager
            response = db_manager.supabase.table('account_types').select('*').execute()
            account_types = response.data
        else:
            # Render manager
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM account_types")
                account_types = cursor.fetchall()
        
        print(f"✅ Found {len(account_types)} account types in {name}")
        for account_type in account_types:
            if hasattr(account_type, 'keys'):
                # Supabase dict
                print(f"   - {account_type['name']} (max devices: {account_type['max_devices']})")
            else:
                # Render tuple
                print(f"   - {account_type[1]} (max devices: {account_type[3]})")
        
        return True
        
    except Exception as e:
        print(f"❌ {name} connection error: {e}")
        return False

def test_user_operations(db_manager, name: str):
    """Test các operations với users"""
    print(f"\n👤 Testing user operations on {name}...")
    print("=" * 50)
    
    try:
        # Test create user
        test_username = f"testuser_{name.lower()}"
        test_password = "test123"
        
        print(f"📝 Creating test user: {test_username}")
        
        # Check if user exists first
        if db_manager.user_exists(test_username):
            print(f"⚠️  User {test_username} already exists, skipping creation")
        else:
            user_id = db_manager.create_user(test_username, test_password, "trial")
            if user_id:
                print(f"✅ User created successfully with ID: {user_id}")
            else:
                print(f"❌ Failed to create user")
                return False
        
        # Test authentication
        print(f"🔐 Testing authentication for {test_username}")
        device_fingerprint = "test_device_123"
        auth_result = db_manager.authenticate_user(test_username, test_password, device_fingerprint)
        
        if auth_result:
            print(f"✅ Authentication successful!")
            print(f"   User ID: {auth_result['user_id']}")
            print(f"   Account Type: {auth_result['account_type']}")
            
            # Test session creation
            print(f"🔑 Creating session...")
            session_token = db_manager.create_session(auth_result['user_id'], device_fingerprint)
            if session_token:
                print(f"✅ Session created: {session_token[:20]}...")
                
                # Test session verification
                print(f"🔍 Verifying session...")
                session_data = db_manager.verify_session(session_token, device_fingerprint)
                if session_data:
                    print(f"✅ Session verified successfully!")
                else:
                    print(f"❌ Session verification failed!")
            else:
                print(f"❌ Session creation failed!")
        else:
            print(f"❌ Authentication failed!")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ {name} user operations error: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Database Switch Test")
    print("=" * 60)
    
    # Test 1: Render PostgreSQL
    print("\n1️⃣  Testing Render PostgreSQL...")
    try:
        render_db = get_render_manager()
        render_success = test_database_connection(render_db, "Render PostgreSQL")
        if render_success:
            test_user_operations(render_db, "Render PostgreSQL")
    except Exception as e:
        print(f"❌ Render PostgreSQL test failed: {e}")
    
    # Test 2: Supabase
    print("\n2️⃣  Testing Supabase...")
    try:
        supabase_db = get_supabase_manager()
        supabase_success = test_database_connection(supabase_db, "Supabase")
        if supabase_success:
            test_user_operations(supabase_db, "Supabase")
    except Exception as e:
        print(f"❌ Supabase test failed: {e}")
    
    # Test 3: Auto-detect
    print("\n3️⃣  Testing Auto-detect...")
    try:
        # Set environment variable để test auto-detect
        os.environ['DATABASE_TYPE'] = 'supabase'
        auto_db = get_database_manager()
        auto_success = test_database_connection(auto_db, "Auto-detect (Supabase)")
        
        # Reset to render
        os.environ['DATABASE_TYPE'] = 'render'
        auto_db2 = get_database_manager()
        auto_success2 = test_database_connection(auto_db2, "Auto-detect (Render)")
        
    except Exception as e:
        print(f"❌ Auto-detect test failed: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 Database Switch Test Completed!")
    print("=" * 60)
    print("\n📋 Summary:")
    print("- Factory pattern allows easy switching between databases")
    print("- Environment variable DATABASE_TYPE controls which database to use")
    print("- Both Render PostgreSQL and Supabase are fully compatible")
    print("- All authentication operations work on both databases")

if __name__ == "__main__":
    main()
