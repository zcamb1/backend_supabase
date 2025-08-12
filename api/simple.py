#!/usr/bin/env python3
"""
Simple API handler for testing without Supabase
"""
from fastapi import FastAPI
import os

app = FastAPI(title="ElevenLabs Auth API (Simple)")

@app.get("/")
def root():
    return {
        "message": "ElevenLabs Auth API is running!",
        "status": "simple_mode",
        "database": "none"
    }

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "database": "none",
        "environment": os.environ.get('VERCEL_ENV', 'unknown')
    }

@app.get("/test")
def test():
    return {
        "message": "Simple test endpoint working",
        "vercel": os.environ.get('VERCEL', 'false'),
        "vercel_env": os.environ.get('VERCEL_ENV', 'unknown')
    }

# Export for Vercel
handler = app
