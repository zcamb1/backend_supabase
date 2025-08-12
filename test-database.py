#!/usr/bin/env python3
"""
Test script để kiểm tra database connection
"""

import sys
from src.auth.database.manager import AuthDatabaseManager

def test_connection():
    print("🔍 Testing database connection...")
    print("=" * 50)
    
    # Test connection with correct credentials
    db = AuthDatabaseManager(
        host="dpg-d21hsaidbo4c73e6ghe0-a",
        port=5432,
        database="elevenlabs_auth_db_l1le",
        username="elevenlabs_auth_db_user",
        password="Dta5busSXW4WPPaasBVvjtyTXT2fXU9t"
    )
    
    try:
        conn = db.get_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            
            print("✅ Connection successful!")
            print(f"📊 PostgreSQL version: {version}")
            print(f"🗄️  Database: {db.database}")
            print(f"🔗 Host: {db.host}")
            return True
        else:
            print("❌ Connection failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_init_database():
    print("\n🔧 Testing database initialization...")
    print("=" * 50)
    
    db = AuthDatabaseManager(
        host="dpg-d21hsaidbo4c73e6ghe0-a",
        port=5432,
        database="elevenlabs_auth_db_l1le",
        username="elevenlabs_auth_db_user",
        password="Dta5busSXW4WPPaasBVvjtyTXT2fXU9t"
    )
    
    try:
        if db.init_database():
            print("✅ Database tables created/verified successfully!")
            return True
        else:
            print("❌ Database initialization failed!")
            return False
            
    except Exception as e:
        print(f"❌ Init error: {e}")
        return False

def create_test_user():
    print("\n👤 Creating test user...")
    print("=" * 50)
    
    db = AuthDatabaseManager(
        host="dpg-d21hsaidbo4c73e6ghe0-a",
        port=5432,
        database="elevenlabs_auth_db_l1le",
        username="elevenlabs_auth_db_user",
        password="Dta5busSXW4WPPaasBVvjtyTXT2fXU9t"
    )
    
    try:
        # Check if user exists first
        if db.user_exists("testuser"):
            print("⚠️  Test user already exists!")
            return True
            
        user_id = db.create_user(
            username="testuser",
            password="test123",
            account_type="trial"
        )
        
        if user_id:
            print(f"✅ Test user created! ID: {user_id}")
            print("👤 Username: testuser")
            print("🔑 Password: test123")
            print("📦 Account: trial")
            return True
        else:
            print("❌ Failed to create test user!")
            return False
            
    except Exception as e:
        print(f"❌ User creation error: {e}")
        return False

def main():
    print("🚀 ElevenLabs Database Test")
    print("Database: elevenlabs_auth_db_l1le")
    print("Host: dpg-d21hsaidbo4c73e6ghe0-a")
    print("=" * 50)
    
    success = True
    
    # Test connection
    if not test_connection():
        success = False
    
    # Test database init
    if not test_init_database():
        success = False
    
    # Create test user
    if not create_test_user():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 ALL TESTS PASSED!")
        print("\n📋 Next steps:")
        print("1. Deploy Admin Backend on Render")
        print("2. Deploy Auth API on Render") 
        print("3. Test admin dashboard")
        print("4. Update main application")
    else:
        print("❌ SOME TESTS FAILED!")
        print("Please check database credentials and connection.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 