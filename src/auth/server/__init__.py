"""
Server module cho ElevenLabs Authentication System
FastAPI authentication server và API endpoints
"""

from .api import app, run_server

__all__ = ["app", "run_server"] 