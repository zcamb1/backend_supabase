#!/usr/bin/env python3
"""
Vercel API handler for ElevenLabs Auth API
"""
import os
import sys

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set environment variables for Supabase
os.environ.setdefault('DATABASE_TYPE', 'supabase')
os.environ.setdefault('SUPABASE_URL', 'https://wjkejklrtrhubbljfrdz.supabase.co')
os.environ.setdefault('SUPABASE_ANON_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Indqa2Vqa2xydHJodWJibGpmcmR6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTQ5NjQyNjAsImV4cCI6MjA3MDU0MDI2MH0.M8iaT_F2nk_HpnjXh0gdiKwFGb8ed3z1RU0myWSK4kg')

# Import FastAPI app
from src.auth.server.api import app

# Export for Vercel
handler = app
