#!/usr/bin/env python3
"""
Render deployment script for ElevenLabs Auth API Server
"""
import os
import uvicorn

def create_safe_api_app():
    """Create API app with error handling"""
    try:
        from src.auth.server.api import app
        
        # Sử dụng Supabase thay vì Render PostgreSQL
        database_url = os.environ.get('DATABASE_URL', 'supabase')
        
        print(f"✅ API app imported successfully")
        print(f"🗄️  Database: Supabase")
        
        # Initialize Supabase database
        try:
            from src.auth.database.factory import get_database_manager
            
            print("🗄️  Initializing Supabase database...")
            db = get_database_manager()
            
            if db.init_database():
                print("✅ Supabase database initialized successfully!")
            else:
                print("⚠️  Supabase database init failed, continuing...")
        except Exception as e:
            print(f"⚠️  Database init error: {e}")
            print("Continuing with API startup...")
        
        return app
        
    except Exception as e:
        print(f"❌ Error creating API app: {e}")
        # Return basic FastAPI app if import fails
        from fastapi import FastAPI
        app = FastAPI(title="ElevenLabs Auth API (Error)")
        
        @app.get("/")
        def health():
            return {"status": "error", "message": str(e), "service": "auth_api"}
            
        @app.get("/health")
        def health_check():
            return {"status": "error", "message": str(e)}
            
        return app

def main():
    print("🚀 Starting ElevenLabs Auth API Server...")
    
    # Create app with error handling
    app = create_safe_api_app()
    
    # Get port from environment (Render uses PORT env var)
    port = int(os.environ.get("PORT", 8000))
    
    print(f"🌐 Starting Auth API on port {port}")
    print(f"📋 API Documentation: https://backend-elevenlab.onrender.com/docs")
    print(f"🔗 Health Check: https://backend-elevenlab.onrender.com/health")
    
    # Start the server
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port,
        log_level="info"
    )

if __name__ == "__main__":
    main() 