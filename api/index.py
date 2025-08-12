#!/usr/bin/env python3
"""
Vercel API handler for ElevenLabs Auth API
"""
import os
import sys
import traceback

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# Set environment variables for Supabase
os.environ.setdefault('DATABASE_TYPE', 'supabase')
os.environ.setdefault('SUPABASE_URL', 'https://wjkejklrtrhubbljfrdz.supabase.co')
os.environ.setdefault('SUPABASE_ANON_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Indqa2Vqa2xydHJodWJibGpmcmR6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTQ5NjQyNjAsImV4cCI6MjA3MDU0MDI2MH0.M8iaT_F2nk_HpnjXh0gdiKwFGb8ed3z1RU0myWSK4kg')
os.environ.setdefault('VERCEL', 'true')

try:
    # Import FastAPI app
    from src.auth.server.api import app
    print("✅ Successfully imported FastAPI app")
except Exception as e:
    print(f"❌ Error importing app: {e}")
    print(f"Traceback: {traceback.format_exc()}")
    
    # Create a simple error app
    from fastapi import FastAPI
    app = FastAPI(title="ElevenLabs Auth API (Error)")
    
    @app.get("/")
    def root():
        return {"error": "Import failed", "details": str(e), "traceback": traceback.format_exc()}
    
    @app.get("/health")
    def health():
        return {"status": "error", "message": str(e)}
    
    @app.get("/test")
    def test():
        return {"message": "Simple test endpoint working"}

# Export for Vercel
handler = app
