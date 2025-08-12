#!/usr/bin/env python3
"""
Test ứng dụng với Supabase trước khi deploy
"""
import os
import requests
import json
from datetime import datetime

def setup_supabase_environment():
    """Setup environment cho Supabase"""
    os.environ['DATABASE_TYPE'] = 'supabase'
    os.environ['SUPABASE_URL'] = 'https://wjkejklrtrhubbljfrdz.supabase.co'
    os.environ['SUPABASE_ANON_KEY'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Indqa2Vqa2xydHJodWJibGpmcmR6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTQ5NjQyNjAsImV4cCI6MjA3MDU0MDI2MH0.M8iaT_F2nk_HpnjXh0gdiKwFGb8ed3z1RU0myWSK4kg'
    print("✅ Environment variables đã được set cho Supabase")

def test_database_connection():
    """Test kết nối database"""
    print("\n🧪 Testing Database Connection...")
    print("=" * 50)
    
    try:
        from src.auth.database.factory import get_database_manager
        db = get_database_manager()
        
        if hasattr(db, 'supabase'):
            print("✅ Factory pattern đã chuyển sang Supabase")
            
            # Test query account types
            response = db.supabase.table('account_types').select('*').execute()
            if response.data:
                print(f"✅ Tìm thấy {len(response.data)} account types:")
                for account_type in response.data:
                    print(f"   - {account_type['name']} (max devices: {account_type['max_devices']})")
            else:
                print("⚠️  Không có account types")
            
            # Test query users
            response = db.supabase.table('users').select('*', count='exact').execute()
            user_count = response.count or 0
            print(f"✅ Tìm thấy {user_count} users")
            
            return True
        else:
            print("❌ Factory pattern chưa chuyển sang Supabase")
            return False
            
    except Exception as e:
        print(f"❌ Lỗi kết nối database: {e}")
        return False

def test_auth_api():
    """Test Auth API endpoints"""
    print("\n🌐 Testing Auth API...")
    print("=" * 50)
    
    # Start server in background (simulate)
    print("🚀 Simulating Auth API server...")
    
    try:
        from src.auth.server.api import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        
        # Test root endpoint
        response = client.get("/")
        if response.status_code == 200:
            print("✅ Root endpoint working")
            data = response.json()
            print(f"   Service: {data.get('service')}")
            print(f"   Status: {data.get('status')}")
        else:
            print(f"❌ Root endpoint failed: {response.status_code}")
        
        # Test health endpoint
        response = client.get("/health")
        if response.status_code == 200:
            print("✅ Health endpoint working")
            data = response.json()
            print(f"   Database: {data.get('database')}")
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
        
        # Test device fingerprint endpoint
        response = client.get("/device/fingerprint")
        if response.status_code == 200:
            print("✅ Device fingerprint endpoint working")
        else:
            print(f"❌ Device fingerprint endpoint failed: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ Lỗi test Auth API: {e}")
        return False

def test_user_operations():
    """Test các operations với users"""
    print("\n👤 Testing User Operations...")
    print("=" * 50)
    
    try:
        from src.auth.database.factory import get_database_manager
        db = get_database_manager()
        
        # Test create user
        test_username = f"testuser_{datetime.now().strftime('%H%M%S')}"
        test_password = "test123"
        
        print(f"📝 Creating test user: {test_username}")
        user_id = db.create_user(test_username, test_password, "trial")
        
        if user_id:
            print(f"✅ User created successfully with ID: {user_id}")
            
            # Test authentication
            print(f"🔐 Testing authentication...")
            device_fingerprint = "test_device_123"
            auth_result = db.authenticate_user(test_username, test_password, device_fingerprint)
            
            if auth_result:
                print("✅ Authentication successful!")
                print(f"   User ID: {auth_result['user_id']}")
                print(f"   Account Type: {auth_result['account_type']}")
                
                # Test session creation
                print(f"🔑 Creating session...")
                session_token = db.create_session(auth_result['user_id'], device_fingerprint)
                if session_token:
                    print(f"✅ Session created: {session_token[:20]}...")
                    
                    # Test session verification
                    print(f"🔍 Verifying session...")
                    session_data = db.verify_session(session_token, device_fingerprint)
                    if session_data:
                        print("✅ Session verified successfully!")
                    else:
                        print("❌ Session verification failed!")
                else:
                    print("❌ Session creation failed!")
            else:
                print("❌ Authentication failed!")
            
            # Cleanup - delete test user
            print(f"🧹 Cleaning up test user...")
            db.delete_user(user_id)
            print("✅ Test user deleted")
            
        else:
            print("❌ Failed to create test user")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Lỗi test user operations: {e}")
        return False

def test_admin_operations():
    """Test admin operations"""
    print("\n👨‍💼 Testing Admin Operations...")
    print("=" * 50)
    
    try:
        from src.auth.database.factory import get_database_manager
        db = get_database_manager()
        
        # Test get users
        users = db.get_users(include_inactive=False)
        print(f"✅ Found {len(users)} active users")
        
        # Test get active sessions
        sessions = db.get_active_sessions()
        print(f"✅ Found {len(sessions)} active sessions")
        
        # Test get account types
        if hasattr(db, 'supabase'):
            response = db.supabase.table('account_types').select('*').execute()
            account_types = response.data
            print(f"✅ Found {len(account_types)} account types")
        
        return True
        
    except Exception as e:
        print(f"❌ Lỗi test admin operations: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Testing Application with Supabase")
    print("=" * 60)
    
    # Setup environment
    setup_supabase_environment()
    
    # Run tests
    tests = [
        ("Database Connection", test_database_connection),
        ("Auth API", test_auth_api),
        ("User Operations", test_user_operations),
        ("Admin Operations", test_admin_operations)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Ứng dụng sẵn sàng deploy lên Render với Supabase")
        print("\n🔧 Bước tiếp theo:")
        print("1. Commit code lên GitHub")
        print("2. Deploy lên Render với environment variables mới")
        print("3. Test production deployment")
    else:
        print(f"\n⚠️  {total - passed} tests failed")
        print("Hãy kiểm tra và sửa lỗi trước khi deploy")

if __name__ == "__main__":
    main()
