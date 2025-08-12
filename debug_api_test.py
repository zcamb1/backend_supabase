#!/usr/bin/env python3
"""
Debug API test để tìm lỗi
"""
import os
from fastapi.testclient import TestClient

def setup_supabase_environment():
    """Setup environment cho Supabase"""
    os.environ['DATABASE_TYPE'] = 'supabase'
    os.environ['SUPABASE_URL'] = 'https://wjkejklrtrhubbljfrdz.supabase.co'
    os.environ['SUPABASE_ANON_KEY'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Indqa2Vqa2xydHJodWJibGpmcmR6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTQ5NjQyNjAsImV4cCI6MjA3MDU0MDI2MH0.M8iaT_F2nk_HpnjXh0gdiKwFGb8ed3z1RU0myWSK4kg'

def debug_api():
    """Debug API endpoints"""
    print("🔍 Debugging Auth API...")
    print("=" * 50)
    
    setup_supabase_environment()
    
    try:
        from src.auth.server.api import app
        client = TestClient(app)
        
        # Test 1: Root endpoint
        print("Testing root endpoint...")
        response = client.get("/")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        # Test 2: Health endpoint
        print("\nTesting health endpoint...")
        response = client.get("/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        # Test 3: Device fingerprint endpoint
        print("\nTesting device fingerprint endpoint...")
        response = client.get("/device/fingerprint")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        # Test 4: Create user endpoint
        print("\nTesting create user endpoint...")
        response = client.post("/admin/users", json={
            "username": "debug_test_user",
            "password": "test123",
            "account_type": "trial"
        })
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Data: {data}")
            
            # Test 5: Login endpoint
            print("\nTesting login endpoint...")
            response = client.post("/auth/login", json={
                "username": "debug_test_user",
                "password": "test123",
                "device_info": {"fingerprint": "debug_device"}
            })
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Data: {data}")
                
                # Test 6: Verify session endpoint
                print("\nTesting verify session endpoint...")
                session_token = data.get('session_token')
                print(f"Session token: {session_token}")
                
                response = client.post("/auth/verify", json={
                    "session_token": session_token,
                    "device_info": {"fingerprint": "debug_device"}
                })
                print(f"Status: {response.status_code}")
                print(f"Response: {response.text}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_api()
