#!/usr/bin/env python3
"""
Supabase Configuration
"""
import os

# Supabase Configuration
SUPABASE_URL = "https://wjkejklrtrhubbljfrdz.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Indqa2Vqa2xydHJodWJibGpmcmR6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTQ5NjQyNjAsImV4cCI6MjA3MDU0MDI2MH0.M8iaT_F2nk_HpnjXh0gdiKwFGb8ed3z1RU0myWSK4kg"

# Set environment variables
os.environ['SUPABASE_URL'] = SUPABASE_URL
os.environ['SUPABASE_ANON_KEY'] = SUPABASE_ANON_KEY

# Admin Configuration
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# Application Configuration
APP_ENV = "development"
DEBUG = True
