import uvicorn
import os

# Create admin app with error handling
def create_safe_admin_app():
    try:
        from src.auth.admin.web_interface import create_admin_app
        
        # Sử dụng Supabase thay vì Render PostgreSQL
        database_url = os.environ.get('DATABASE_URL', 'supabase')
        
        admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
        admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
        
        print("✅ Creating admin app...")
        
        # Initialize database FIRST
        try:
            from src.auth.database.factory import get_database_manager
            
            # Sử dụng factory pattern để tạo database manager
            db_manager = get_database_manager()
            
            print("🗄️  Initializing database tables...")
            if db_manager.init_database():
                print("✅ Database tables created successfully!")
            else:
                print("⚠️  Database init failed, but continuing...")
                
        except Exception as db_error:
            print(f"⚠️  Database init error: {db_error}")
            print("Continuing with app creation...")
        
        app = create_admin_app(
            database_url=database_url,
            admin_username=admin_username,
            admin_password=admin_password
        )
        print("✅ Admin app created successfully")
        return app
        
    except Exception as e:
        print(f"❌ Error creating admin app: {e}")
        # Return basic FastAPI app if admin fails
        from fastapi import FastAPI
        app = FastAPI(title="ElevenLabs Admin (Error)")
        
        @app.get("/")
        def health():
            return {"status": "error", "message": str(e), "service": "admin"}
            
        @app.get("/health")
        def health_check():
            return {"status": "error", "message": str(e)}
            
        return app

app = create_safe_admin_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print(f"🚀 Starting Admin on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port) 