"""
Session module cho ElevenLabs Authentication System
Local session management với encryption và caching
"""

from .manager import (
    SessionManager,
    create_session_manager,
    quick_login,
    is_user_authenticated,
    get_current_user,
    logout_user
)

__all__ = [
    "SessionManager",
    "create_session_manager",
    "quick_login", 
    "is_user_authenticated",
    "get_current_user",
    "logout_user"
] 