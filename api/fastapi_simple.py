#!/usr/bin/env python3
"""
Simple FastAPI app for testing
"""
from fastapi import FastAPI
import os

app = FastAPI(title="ElevenLabs Auth API (Simple)")

@app.get("/")
def root():
    return {
        "message": "FastAPI app working!",
        "status": "simple_mode",
        "database": "none",
        "vercel": os.environ.get('VERCEL', 'false')
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
        "message": "FastAPI test endpoint working",
        "vercel": os.environ.get('VERCEL', 'false'),
        "vercel_env": os.environ.get('VERCEL_ENV', 'unknown')
    }

# Export for Vercel
handler = app
