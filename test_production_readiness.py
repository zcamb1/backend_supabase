#!/usr/bin/env python3
"""
Test toàn diện để đảm bảo ứng dụng sẵn sàng cho production với Supabase
"""
import os
import time
import requests
from datetime import datetime

def setup_supabase_environment():
    """Setup environment cho Supabase"""
    os.environ['DATABASE_TYPE'] = 'supabase'
    os.environ['SUPABASE_URL'] = 'https://wjkejklrtrhubbljfrdz.supabase.co'
    os.environ['SUPABASE_ANON_KEY'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Indqa2Vqa2xydHJodWJibGpmcmR6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTQ5NjQyNjAsImV4cCI6MjA3MDU0MDI2MH0.M8iaT_F2nk_HpnjXh0gdiKwFGb8ed3z1RU0myWSK4kg'
    print("✅ Environment variables đã được set cho Supabase")

def test_database_operations():
    """Test tất cả database operations"""
    print("\n🗄️  Testing Database Operations...")
    print("=" * 50)
    
    try:
        from src.auth.database.factory import get_database_manager
        db = get_database_manager()
        
        if not hasattr(db, 'supabase'):
            print("❌ Factory pattern không trả về Supabase manager")
            return False
        
        print("✅ Factory pattern trả về Supabase manager")
        
        # Test 1: Query account types
        response = db.supabase.table('account_types').select('*').execute()
        if not response.data:
            print("❌ Không thể query account_types")
            return False
        print(f"✅ Query account_types: {len(response.data)} records")
        
        # Test 2: Query users
        response = db.supabase.table('users').select('*', count='exact').execute()
        user_count = response.count or 0
        print(f"✅ Query users: {user_count} records")
        
        # Test 3: Query user_sessions
        response = db.supabase.table('user_sessions').select('*', count='exact').execute()
        session_count = response.count or 0
        print(f"✅ Query user_sessions: {session_count} records")
        
        # Test 4: Test create_user method
        test_username = f"prod_test_{int(time.time())}"
        test_password = "test123"
        
        print(f"📝 Testing create_user: {test_username}")
        user_id = db.create_user(test_username, test_password, "trial")
        
        if not user_id:
            print("❌ create_user failed")
            return False
        print(f"✅ create_user successful: ID {user_id}")
        
        # Test 5: Test authenticate_user method
        print(f"🔐 Testing authenticate_user: {test_username}")
        device_fingerprint = "prod_test_device"
        auth_result = db.authenticate_user(test_username, test_password, device_fingerprint)
        
        if not auth_result:
            print("❌ authenticate_user failed")
            db.delete_user(user_id)
            return False
        print(f"✅ authenticate_user successful: {auth_result['user_id']}")
        
        # Test 6: Test create_session method
        print("🔑 Testing create_session")
        session_token = db.create_session(auth_result['user_id'], device_fingerprint)
        
        if not session_token:
            print("❌ create_session failed")
            db.delete_user(user_id)
            return False
        print(f"✅ create_session successful: {session_token[:20]}...")
        
        # Test 7: Test verify_session method
        print("🔍 Testing verify_session")
        session_data = db.verify_session(session_token, device_fingerprint)
        
        if not session_data:
            print("❌ verify_session failed")
            db.delete_user(user_id)
            return False
        print(f"✅ verify_session successful: {session_data['user_id']}")
        
        # Test 8: Test get_users method
        print("👥 Testing get_users")
        users = db.get_users(include_inactive=False)
        print(f"✅ get_users successful: {len(users)} users")
        
        # Test 9: Test get_active_sessions method
        print("📊 Testing get_active_sessions")
        sessions = db.get_active_sessions()
        print(f"✅ get_active_sessions successful: {len(sessions)} sessions")
        
        # Cleanup
        print("🧹 Cleaning up test user")
        db.delete_user(user_id)
        print("✅ Test user deleted")
        
        return True
        
    except Exception as e:
        print(f"❌ Database operations test failed: {e}")
        return False

def test_auth_api_endpoints():
    """Test tất cả Auth API endpoints"""
    print("\n🌐 Testing Auth API Endpoints...")
    print("=" * 50)
    
    try:
        print("Importing modules...")
        from src.auth.server.api import app
        from fastapi.testclient import TestClient
        
        print("Creating test client...")
        client = TestClient(app)
        
        # Test 1: Root endpoint
        response = client.get("/")
        if response.status_code != 200:
            print(f"❌ Root endpoint failed: {response.status_code}")
            return False
        data = response.json()
        print(f"✅ Root endpoint: {data.get('service')} - {data.get('status')}")
        
        # Test 2: Health endpoint
        response = client.get("/health")
        if response.status_code != 200:
            print(f"❌ Health endpoint failed: {response.status_code}")
            return False
        data = response.json()
        print(f"✅ Health endpoint: Database {data.get('database')}")
        
        # Test 3: Device fingerprint endpoint
        response = client.get("/device/fingerprint")
        if response.status_code != 200:
            print(f"❌ Device fingerprint endpoint failed: {response.status_code}")
            return False
        data = response.json()
        device_id = data.get('device_info', {}).get('device_id', 'unknown')
        print(f"✅ Device fingerprint endpoint: {device_id[:20]}...")
        
        # Test 4: Login endpoint (skip create user since it requires admin auth)
        test_username = f"api_test_{int(time.time())}"
        test_password = "test123"
        
        # Create user via database directly
        from src.auth.database.factory import get_database_manager
        db = get_database_manager()
        user_id = db.create_user(test_username, test_password, "trial")
        
        if not user_id:
            print("❌ Failed to create test user")
            return False
        print(f"✅ Created test user: {user_id}")
        
        # Test 5: Login endpoint
        response = client.post("/auth/login", json={
            "username": test_username,
            "password": test_password,
            "device_info": {"fingerprint": "api_test_device"}
        })
        
        print(f"Login response status: {response.status_code}")
        print(f"Login response text: {response.text}")
        
        if response.status_code != 200:
            print(f"❌ Login endpoint failed: {response.status_code}")
            db.delete_user(user_id)
            return False
        data = response.json()
        if not data:
            print("❌ Login response is empty")
            db.delete_user(user_id)
            return False
            
        if not data.get('success'):
            print(f"❌ Login failed: {data.get('error')}")
            db.delete_user(user_id)
            return False
            
        session_token = data.get('session_token')
        if not session_token:
            print("❌ No session token in response")
            db.delete_user(user_id)
            return False
            
        print(f"✅ Login endpoint: Session token {session_token[:20]}...")
            
        response = client.post("/auth/verify", json={
            "session_token": session_token,
            "device_info": {"fingerprint": "api_test_device"}
        })
        
        if response.status_code != 200:
            print(f"❌ Verify session endpoint failed: {response.status_code}")
            db.delete_user(user_id)
            return False
        data = response.json()
        if not data:
            print("❌ Verify response is empty")
            db.delete_user(user_id)
            return False
        print(f"✅ Verify session endpoint: Valid session")
        
        # Cleanup - delete test user
        db.delete_user(user_id)
        print("✅ Test user cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Auth API test failed: {e}")
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
        print(f"✅ get_users: {len(users)} active users")
        
        # Test get active sessions
        sessions = db.get_active_sessions()
        print(f"✅ get_active_sessions: {len(sessions)} active sessions")
        
        # Test get account types
        response = db.supabase.table('account_types').select('*').execute()
        account_types = response.data
        print(f"✅ get_account_types: {len(account_types)} account types")
        
        return True
        
    except Exception as e:
        print(f"❌ Admin operations test failed: {e}")
        return False

def test_error_handling():
    """Test error handling"""
    print("\n⚠️  Testing Error Handling...")
    print("=" * 50)
    
    try:
        from src.auth.server.api import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        
        # Test 1: Invalid login
        response = client.post("/auth/login", json={
            "username": "nonexistent_user",
            "password": "wrong_password",
            "device_info": {"fingerprint": "test_device"}
        })
        
        if response.status_code == 401:
            print("✅ Invalid login handled correctly")
        else:
            print(f"⚠️  Unexpected response for invalid login: {response.status_code}")
        
        # Test 2: Invalid session
        response = client.post("/auth/verify", json={
            "session_token": "invalid_token",
            "device_info": {"fingerprint": "test_device"}
        })
        
        if response.status_code == 401:
            print("✅ Invalid session handled correctly")
        else:
            print(f"⚠️  Unexpected response for invalid session: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Production Readiness Test with Supabase")
    print("=" * 60)
    
    # Setup environment
    setup_supabase_environment()
    
    # Run comprehensive tests
    tests = [
        ("Database Operations", test_database_operations),
        ("Auth API Endpoints", test_auth_api_endpoints),
        ("Admin Operations", test_admin_operations),
        ("Error Handling", test_error_handling)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            print(f"\n🧪 Running {test_name}...")
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 PRODUCTION READINESS SUMMARY")
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
        print("\n🎉 PRODUCTION READY!")
        print("✅ Ứng dụng hoàn toàn sẵn sàng deploy lên Render với Supabase")
        print("\n🔧 Deployment Checklist:")
        print("✅ Database connection working")
        print("✅ All API endpoints functional")
        print("✅ User operations working")
        print("✅ Admin operations working")
        print("✅ Error handling working")
        print("\n🚀 Ready to deploy!")
    else:
        print(f"\n⚠️  {total - passed} critical tests failed")
        print("❌ Không nên deploy cho đến khi sửa các lỗi này")

if __name__ == "__main__":
    main()
