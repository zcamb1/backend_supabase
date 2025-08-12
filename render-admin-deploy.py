#!/usr/bin/env python3
"""
Render deployment script for ElevenLabs Admin Backend
"""
import os
import sys
from src.auth.admin.web_interface import create_admin_app
import uvicorn

def main():
    print("🚀 Starting ElevenLabs Admin Backend...")
    
    # Sử dụng Supabase thay vì Render PostgreSQL
    database_url = os.environ.get('DATABASE_URL', 'supabase')
    
    # Get admin credentials from environment or use defaults
    admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
    admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
    
    print(f"📊 Admin Username: {admin_username}")
    print(f"🗄️  Database: Supabase")
    
    # Create FastAPI app
    app = create_admin_app(
        database_url=database_url,
        admin_username=admin_username,
        admin_password=admin_password
    )
    
    # Initialize database on startup
    try:
        from src.auth.database.factory import get_database_manager
        
        print("🔧 Initializing Supabase database...")
        db_manager = get_database_manager()
        
        if db_manager.init_database():
            print("✅ Supabase database initialized successfully!")
        else:
            print("❌ Supabase database initialization failed!")
            
    except Exception as e:
        print(f"⚠️  Database initialization error: {e}")
        print("Continuing with app startup...")
    
    # Get port from environment (Render uses PORT env var)
    port = int(os.environ.get("PORT", 10000))
    
    print(f"🌐 Starting Admin Interface on port {port}")
    print(f"🔗 Dashboard: https://elevenlabs-auth-backend.onrender.com/admin/dashboard")
    
    # Start the server
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port,
        log_level="info"
    )

if __name__ == "__main__":
    main() 