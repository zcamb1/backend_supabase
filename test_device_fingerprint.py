#!/usr/bin/env python3
"""
Test device fingerprint logic
"""
import os
import time

def setup_supabase_environment():
    """Setup environment cho Supabase"""
    os.environ['DATABASE_TYPE'] = 'supabase'
    os.environ['SUPABASE_URL'] = 'https://wjkejklrtrhubbljfrdz.supabase.co'
    os.environ['SUPABASE_ANON_KEY'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Indqa2Vqa2xydHJodWJibGpmcmR6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTQ5NjQyNjAsImV4cCI6MjA3MDU0MDI2MH0.M8iaT_F2nk_HpnjXh0gdiKwFGb8ed3z1RU0myWSK4kg'

def test_device_fingerprint():
    """Test device fingerprint logic"""
    print("🔒 Testing Device Fingerprint Logic...")
    print("=" * 50)
    
    setup_supabase_environment()
    
    try:
        from src.auth.database.factory import get_database_manager
        db = get_database_manager()
        
        # Test 1: Tạo user mới
        test_username = f"fingerprint_test_{int(time.time())}"
        test_password = "test123"
        device_1 = "device_fingerprint_1"
        device_2 = "device_fingerprint_2"
        
        print(f"📝 Creating test user: {test_username}")
        user_id = db.create_user(test_username, test_password, "trial")
        
        if not user_id:
            print("❌ Failed to create test user")
            return
        
        print(f"✅ User created: {user_id}")
        
        # Test 2: Login lần đầu với device_1
        print(f"\n🔐 Testing first login with device_1: {device_1}")
        auth_result = db.authenticate_user(test_username, test_password, device_1)
        
        if auth_result and auth_result.get('success'):
            print("✅ First login successful")
            
            # Kiểm tra device_fingerprint đã được lưu chưa
            response = db.supabase.table('users').select('device_fingerprint').eq('id', user_id).execute()
            saved_fingerprint = response.data[0]['device_fingerprint']
            print(f"📱 Saved device fingerprint: {saved_fingerprint}")
            
            if saved_fingerprint == device_1:
                print("✅ Device fingerprint correctly saved")
            else:
                print("❌ Device fingerprint not saved correctly")
        else:
            print("❌ First login failed")
            if auth_result:
                print(f"   Error: {auth_result.get('error')}")
            db.delete_user(user_id)
            return
        
        # Test 3: Login lần 2 với cùng device_1 (nên thành công)
        print(f"\n🔐 Testing second login with same device_1: {device_1}")
        auth_result = db.authenticate_user(test_username, test_password, device_1)
        
        if auth_result and auth_result.get('success'):
            print("✅ Second login with same device successful")
        else:
            print("❌ Second login with same device failed")
            if auth_result:
                print(f"   Error: {auth_result.get('error')}")
        
        # Test 4: Login với device_2 khác (nên thất bại)
        print(f"\n🔐 Testing login with different device_2: {device_2}")
        auth_result = db.authenticate_user(test_username, test_password, device_2)
        
        if not auth_result or not auth_result.get('success'):
            print("✅ Login with different device correctly blocked")
            if auth_result:
                print(f"   Error: {auth_result.get('error')}")
        else:
            print("❌ Login with different device should have been blocked")
        
        # Test 5: Kiểm tra audit logs
        print(f"\n📊 Checking audit logs...")
        response = db.supabase.table('auth_events').select('*').eq('username', test_username).order('timestamp', desc=True).execute()
        
        for event in response.data[:5]:  # 5 events gần nhất
            print(f"  - {event['event_type']}: {event['success']} - {event.get('details', '')}")
        
        # Cleanup
        print(f"\n🧹 Cleaning up test user...")
        db.delete_user(user_id)
        print("✅ Test completed")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_device_fingerprint()
