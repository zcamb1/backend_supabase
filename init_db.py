#!/usr/bin/env python3
"""
Initialize database tables for ElevenLabs Authentication System
"""

from src.auth.database.manager import AuthDatabaseManager

if __name__ == "__main__":
    print("🚀 ElevenLabs Database Initialization")
    print("=" * 50)
    
    # Use production database credentials
    db = AuthDatabaseManager(
        host="dpg-d21hsaidbo4c73e6ghe0-a",
        port=5432,
        database="elevenlabs_auth_db_l1le",
        username="elevenlabs_auth_db_user",
        password="Dta5busSXW4WPPaasBVvjtyTXT2fXU9t"
    )
    
    print("🗄️  Creating database tables...")
    print("📋 Tables to create: users, user_sessions, account_types, admin_users, audit_logs, auth_events")
    
    if db.init_database():
        print("✅ Database initialized successfully!")
        print("🎉 All tables created and ready to use!")
        
        # Create test user
        print("\n👤 Creating test user...")
        try:
            if not db.user_exists("testuser"):
                user_id = db.create_user("testuser", "test123", "trial")
                if user_id:
                    print(f"✅ Test user created: testuser / test123 (ID: {user_id})")
                else:
                    print("⚠️  Failed to create test user")
            else:
                print("⚠️  Test user already exists")
        except Exception as e:
            print(f"⚠️  Test user creation error: {e}")
            
    else:
        print("❌ Database initialization failed!")
        exit(1) 