#!/usr/bin/env python3
"""
Test script to check imports step by step
"""
import os
import sys
import traceback

# Set environment variables
os.environ.setdefault('DATABASE_TYPE', 'supabase')
os.environ.setdefault('SUPABASE_URL', 'https://wjkejklrtrhubbljfrdz.supabase.co')
os.environ.setdefault('SUPABASE_ANON_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Indqa2Vqa2xydHJodWJibGpmcmR6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTQ5NjQyNjAsImV4cCI6MjA3MDU0MDI2MH0.M8iaT_F2nk_HpnjXh0gdiKwFGb8ed3z1RU0myWSK4kg')
os.environ.setdefault('VERCEL', 'true')

def test_import(module_name, description):
    """Test importing a specific module"""
    print(f"\n🔍 Testing: {description}")
    try:
        module = __import__(module_name, fromlist=['*'])
        print(f"✅ Success: {module_name}")
        return True
    except Exception as e:
        print(f"❌ Failed: {module_name}")
        print(f"   Error: {e}")
        print(f"   Traceback: {traceback.format_exc()}")
        return False

def main():
    print("🧪 Testing imports step by step...")
    
    # Test basic imports
    test_import('fastapi', 'FastAPI')
    test_import('uvicorn', 'Uvicorn')
    test_import('supabase', 'Supabase')
    
    # Test our modules
    test_import('src.auth.utils.logger', 'Logger utility')
    test_import('src.auth.database.factory', 'Database factory')
    test_import('src.auth.database.supabase_manager', 'Supabase manager')
    test_import('src.auth.server.api', 'API server')
    
    print("\n🎯 Import test completed!")

if __name__ == "__main__":
    main()
