#!/usr/bin/env python3
"""
Admin User Manager cho ElevenLabs Authentication System
Management utilities cho admin interface để handle user operations
"""

import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import json

from ..database.manager import AuthDatabaseManager
from ..utils.logger import get_logger, log_auth_event, log_security_event, LoggedOperation

class AdminUserManager:
    """
    User management utilities cho admin interface
    """
    
    def __init__(self, db_manager: AuthDatabaseManager):
        self.db_manager = db_manager
        self.logger = get_logger("admin_user_manager")
    
    def get_total_users(self) -> int:
        """Get total number of users"""
        try:
            with LoggedOperation("Get Total Users Count", self.logger):
                with self.db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM users WHERE is_active = true")
                    count = cursor.fetchone()[0]
                    return count
                    
        except Exception as e:
            self.logger.error(f"Failed to get total users: {e}")
            return 0
    
    def get_users_by_account_type(self, account_type: str) -> int:
        """Get count of users by account type"""
        try:
            with LoggedOperation(f"Get {account_type} Users Count", self.logger):
                with self.db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT COUNT(*) FROM users u
                        JOIN account_types at ON u.account_type_id = at.id
                        WHERE at.name = %s AND u.is_active = true
                    """, (account_type,))
                    count = cursor.fetchone()[0]
                    return count
                    
        except Exception as e:
            self.logger.error(f"Failed to get {account_type} users count: {e}")
            return 0
    
    def get_active_sessions_count(self) -> int:
        """Get count of currently active sessions"""
        try:
            with LoggedOperation("Get Active Sessions Count", self.logger):
                with self.db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    # Sessions active within last 24 hours
                    cutoff_time = datetime.now() - timedelta(hours=24)
                    cursor.execute("""
                        SELECT COUNT(*) FROM user_sessions 
                        WHERE last_activity > %s AND is_active = true
                    """, (cutoff_time,))
                    count = cursor.fetchone()[0]
                    return count
                    
        except Exception as e:
            self.logger.error(f"Failed to get active sessions count: {e}")
            return 0
    
    def get_all_users(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get all users with pagination"""
        try:
            with LoggedOperation(f"Get All Users (limit={limit}, offset={offset})", self.logger):
                with self.db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT 
                            u.id, u.username, u.device_fingerprint, u.created_at, u.updated_at,
                            u.is_active, at.name as account_type, u.expires_at
                        FROM users u
                        JOIN account_types at ON u.account_type_id = at.id
                        ORDER BY u.created_at DESC
                        LIMIT %s OFFSET %s
                    """, (limit, offset))
                    
                    users = []
                    for row in cursor.fetchall():
                        users.append({
                            'id': row[0],
                            'username': row[1],
                            'device_fingerprint': row[2],
                            'created_at': row[3],
                            'updated_at': row[4],
                            'is_active': row[5],
                            'account_type': row[6],
                            'expires_at': row[7]
                        })
                    
                    return users
                    
        except Exception as e:
            self.logger.error(f"Failed to get all users: {e}")
            return []
    
    def get_account_types(self) -> List[Dict[str, Any]]:
        """Get all available account types"""
        try:
            with LoggedOperation("Get Account Types", self.logger):
                with self.db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT id, name, duration_days, max_devices, features
                        FROM account_types
                        ORDER BY name
                    """)
                    
                    account_types = []
                    for row in cursor.fetchall():
                        account_types.append({
                            'id': row[0],
                            'name': row[1],
                            'duration_days': row[2],
                            'max_devices': row[3],
                            'features': row[4]
                        })
                    
                    return account_types
                    
        except Exception as e:
            self.logger.error(f"Failed to get account types: {e}")
            return []
    
    def create_user(self, username: str, password: str, account_type: str = 'trial') -> Optional[int]:
        """Create new user via admin interface"""
        try:
            with LoggedOperation(f"Admin Create User: {username}", self.logger):
                self.logger.info(f"Creating user: {username} with account type: {account_type}")
                
                # Check if user already exists
                if self.db_manager.user_exists(username):
                    self.logger.warning(f"User already exists: {username}")
                    return None
                
                user_id = self.db_manager.create_user(username, password, account_type)
                
                if user_id:
                    self.logger.info(f"User created successfully: {username} (ID: {user_id})")
                    # Log auth event
                    self.db_manager.log_auth_event(
                        "USER_CREATED", 
                        username, 
                        None, 
                        True, 
                        f"User created by admin with {account_type} account"
                    )
                else:
                    self.logger.warning(f"Failed to create user: {username} - database returned None")
                    
                return user_id
                    
        except Exception as e:
            self.logger.error(f"Failed to create user {username}: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return None
    
    def update_user_account_type(self, user_id: int, account_type: str) -> bool:
        """Update user account type"""
        try:
            with LoggedOperation(f"Update User {user_id} Account Type: {account_type}", self.logger):
                with self.db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    # Get account type ID
                    cursor.execute("SELECT id FROM account_types WHERE name = %s", (account_type,))
                    account_type_row = cursor.fetchone()
                    if not account_type_row:
                        return False
                    
                    account_type_id = account_type_row[0]
                    
                    # Update user
                    cursor.execute("""
                        UPDATE users 
                        SET account_type_id = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (account_type_id, user_id))
                    
                    success = cursor.rowcount > 0
                    conn.commit()
                    cursor.close()
                    conn.close()
                    
                    if success:
                        # Log auth event
                        self.db_manager.log_auth_event(
                            "USER_UPDATED", 
                            f"user_{user_id}", 
                            None, 
                            True, 
                            f"Account type changed to {account_type}"
                        )
                    
                    return success
                    
        except Exception as e:
            self.logger.error(f"Failed to update user {user_id} account type: {e}")
            return False
    
    def update_user_full(self, user_id: int, username: str, password: str = None, account_type: str = 'trial') -> bool:
        """Update user with username, password (optional), and account type"""
        try:
            with LoggedOperation(f"Update User Full {user_id}: {username}", self.logger):
                self.logger.info(f"Updating user {user_id}: username={username}, account_type={account_type}, password={'set' if password else 'unchanged'}")
                
                conn = self.db_manager.get_connection()
                if not conn:
                    self.logger.error("Failed to get database connection")
                    return False
                
                try:
                    cursor = conn.cursor()
                    
                    # Check if username already exists (and it's not the current user)
                    cursor.execute("SELECT id FROM users WHERE username = %s AND id != %s", (username, user_id))
                    if cursor.fetchone():
                        self.logger.warning(f"Username {username} already exists for another user")
                        cursor.close()
                        conn.close()
                        return False
                    
                    # Get account type ID
                    cursor.execute("SELECT id FROM account_types WHERE name = %s", (account_type,))
                    account_type_row = cursor.fetchone()
                    if not account_type_row:
                        self.logger.warning(f"Invalid account type: {account_type}")
                        cursor.close()
                        conn.close()
                        return False
                    
                    account_type_id = account_type_row[0]
                    
                    # Build update query based on whether password is provided
                    if password:
                        # Update with new password
                        password_hash = hashlib.sha256(password.encode()).hexdigest()
                        cursor.execute("""
                            UPDATE users 
                            SET username = %s, password_hash = %s, account_type_id = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                        """, (username, password_hash, account_type_id, user_id))
                        self.logger.info(f"Updated user {user_id} with new password")
                    else:
                        # Update without changing password
                        cursor.execute("""
                            UPDATE users 
                            SET username = %s, account_type_id = %s, updated_at = CURRENT_TIMESTAMP
                            WHERE id = %s
                        """, (username, account_type_id, user_id))
                        self.logger.info(f"Updated user {user_id} without changing password")
                    
                    success = cursor.rowcount > 0
                    self.logger.info(f"User update affected {cursor.rowcount} rows")
                    
                    conn.commit()
                    cursor.close()
                    conn.close()
                    
                    if success:
                        # Log auth event
                        self.db_manager.log_auth_event(
                            "USER_UPDATED_FULL", 
                            username, 
                            None, 
                            True, 
                            f"User {user_id} updated: username, account_type={account_type}" + (", password" if password else "")
                        )
                        self.logger.info(f"User {user_id} updated successfully: {username}")
                    else:
                        self.logger.warning(f"No rows affected when updating user ID: {user_id}")
                    
                    return success
                
                except Exception as db_error:
                    self.logger.error(f"Database error in update_user_full: {db_error}")
                    if conn:
                        conn.rollback()
                        conn.close()
                    raise
                    
        except Exception as e:
            self.logger.error(f"Failed to update user {user_id} full: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    def delete_user(self, user_id: int) -> bool:
        """Delete user (HARD DELETE - permanently remove from database)"""
        try:
            with LoggedOperation(f"Hard Delete User: {user_id}", self.logger):
                self.logger.info(f"Attempting to permanently delete user ID: {user_id}")
                
                conn = self.db_manager.get_connection()
                if not conn:
                    self.logger.error("Failed to get database connection")
                    return False
                
                try:
                    cursor = conn.cursor()
                    
                    # Get username for logging BEFORE deletion
                    cursor.execute("SELECT username, is_active FROM users WHERE id = %s", (user_id,))
                    user_row = cursor.fetchone()
                    if not user_row:
                        self.logger.warning(f"User ID {user_id} not found for deletion")
                        cursor.close()
                        conn.close()
                        return False
                        
                    username, current_status = user_row
                    self.logger.info(f"Found user to permanently delete: {username} (ID: {user_id}, status: {current_status})")
                    
                    # Log the deletion event BEFORE actual deletion
                    self.db_manager.log_auth_event(
                        "USER_PERMANENTLY_DELETED", 
                        username, 
                        None, 
                        True, 
                        f"User permanently deleted by admin"
                    )
                    
                    # HARD DELETE: Remove all sessions first (foreign key constraint)
                    cursor.execute("DELETE FROM user_sessions WHERE user_id = %s", (user_id,))
                    session_delete_count = cursor.rowcount
                    self.logger.info(f"Deleted {session_delete_count} user sessions")
                    
                    # HARD DELETE: Remove user completely from database
                    cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
                    user_delete_count = cursor.rowcount
                    self.logger.info(f"User deletion affected {user_delete_count} rows")
                    
                    success = user_delete_count > 0
                    conn.commit()
                    cursor.close()
                    conn.close()
                    
                    if success:
                        self.logger.warning(f"User permanently deleted from database: {username} (ID: {user_id})")
                        self.logger.warning(f"Deleted records: {user_delete_count} user, {session_delete_count} sessions")
                    else:
                        self.logger.warning(f"No rows affected when deleting user ID: {user_id}")
                    
                    return success
                
                except Exception as db_error:
                    self.logger.error(f"Database error in delete_user: {db_error}")
                    if conn:
                        conn.rollback()
                        conn.close()
                    raise
                    
        except Exception as e:
            self.logger.error(f"Failed to permanently delete user {user_id}: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            # Ensure connection is closed properly
            try:
                if 'conn' in locals() and conn:
                    conn.close()
            except:
                pass
            return False
    
    def toggle_user_status(self, user_id: int) -> bool:
        """Toggle user active status"""
        try:
            with LoggedOperation(f"Toggle User Status: {user_id}", self.logger):
                self.logger.info(f"Attempting to toggle status for user ID: {user_id}")
                
                conn = self.db_manager.get_connection()
                if not conn:
                    self.logger.error("Failed to get database connection")
                    return False
                
                try:
                    cursor = conn.cursor()
                    
                    # Get current status and username
                    cursor.execute("SELECT is_active, username FROM users WHERE id = %s", (user_id,))
                    user_row = cursor.fetchone()
                    if not user_row:
                        self.logger.warning(f"User ID {user_id} not found for status toggle")
                        cursor.close()
                        conn.close()
                        return False
                    
                    current_status, username = user_row
                    new_status = not current_status
                    self.logger.info(f"Toggling user {username} (ID: {user_id}) from {current_status} to {new_status}")
                    
                    # Update status
                    cursor.execute("""
                        UPDATE users 
                        SET is_active = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (new_status, user_id))
                    
                    success = cursor.rowcount > 0
                    self.logger.info(f"Status toggle affected {cursor.rowcount} rows")
                    
                    conn.commit()
                    cursor.close()
                    conn.close()
                    
                    if success:
                        status_text = "activated" if new_status else "deactivated"
                        self.logger.info(f"User status successfully changed: {username} is now {status_text}")
                        # Log auth event
                        self.db_manager.log_auth_event(
                            "USER_STATUS_CHANGED", 
                            username, 
                            None, 
                            True, 
                            f"User {status_text} by admin"
                        )
                    else:
                        self.logger.warning(f"No rows affected when toggling status for user ID: {user_id}")
                    
                    return success
                
                except Exception as db_error:
                    self.logger.error(f"Database error in toggle_user_status: {db_error}")
                    if conn:
                        conn.rollback()
                        conn.close()
                    raise
                    
        except Exception as e:
            self.logger.error(f"Failed to toggle user {user_id} status: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            # Ensure connection is closed properly
            try:
                if 'conn' in locals() and conn:
                    conn.close()
            except:
                pass
            return False
    
    def get_user_device_details(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get comprehensive device details for a user"""
        try:
            with LoggedOperation(f"Get User Device Details: {user_id}", self.logger):
                conn = self.db_manager.get_connection()
                if not conn:
                    self.logger.error("Failed to get database connection")
                    return None
                
                try:
                    cursor = conn.cursor()
                    
                    # Get user basic info
                    cursor.execute("""
                        SELECT u.username, u.device_fingerprint, u.created_at, u.is_active
                        FROM users u WHERE u.id = %s
                    """, (user_id,))
                    
                    user_row = cursor.fetchone()
                    if not user_row:
                        self.logger.warning(f"User {user_id} not found")
                        return None
                    
                    # Safe unpacking with error handling
                    try:
                        username, device_fingerprint, created_at, is_active = user_row
                    except ValueError as ve:
                        self.logger.error(f"Database schema mismatch in user query: {ve}, row: {user_row}")
                        return None
                    
                    # Get device info (from device fingerprint)
                    device_info = {
                        'device_id': device_fingerprint,
                        'platform': 'Unknown',  # Would need to parse/store this separately
                        'first_seen': created_at.strftime('%Y-%m-%d %H:%M:%S') if created_at else 'N/A',
                        'is_active': is_active
                    }
                    
                    # Get active sessions for this user
                    cursor.execute("""
                        SELECT session_token, device_fingerprint, created_at, 
                               last_activity, expires_at, is_active
                        FROM user_sessions 
                        WHERE user_id = %s AND is_active = true
                        ORDER BY last_activity DESC
                    """, (user_id,))
                    
                    active_sessions = []
                    for session_row in cursor.fetchall():
                        try:
                            active_sessions.append({
                                'session_token': session_row[0] if len(session_row) > 0 else 'N/A',
                                'device_fingerprint': session_row[1] if len(session_row) > 1 else 'N/A',
                                'created_at': session_row[2].strftime('%Y-%m-%d %H:%M:%S') if len(session_row) > 2 and session_row[2] else 'N/A',
                                'last_activity': session_row[3].strftime('%Y-%m-%d %H:%M:%S') if len(session_row) > 3 and session_row[3] else 'N/A',
                                'expires_at': session_row[4].strftime('%Y-%m-%d %H:%M:%S') if len(session_row) > 4 and session_row[4] else 'N/A',
                                'is_active': session_row[5] if len(session_row) > 5 else False
                            })
                        except Exception as e:
                            self.logger.warning(f"Error processing session row: {e}, row: {session_row}")
                            continue
                    
                    # Get session statistics
                    cursor.execute("""
                        SELECT COUNT(*) as total_sessions,
                               MAX(last_activity) as last_activity
                        FROM user_sessions 
                        WHERE user_id = %s
                    """, (user_id,))
                    
                    stats_row = cursor.fetchone()
                    if stats_row and len(stats_row) >= 2:
                        device_info['total_sessions'] = stats_row[0] if stats_row[0] is not None else 0
                        device_info['last_activity'] = stats_row[1].strftime('%Y-%m-%d %H:%M:%S') if stats_row[1] else 'N/A'
                    else:
                        device_info['total_sessions'] = 0
                        device_info['last_activity'] = 'N/A'
                    
                    # Get login history from audit logs (adapted to current schema)
                    cursor.execute("""
                        SELECT created_at, action, details, ip_address
                        FROM audit_logs 
                        WHERE details::text LIKE %s
                        AND (action LIKE '%LOGIN%' OR action LIKE '%AUTH%' OR action LIKE '%USER%')
                        ORDER BY created_at DESC
                        LIMIT 20
                    """, (f'%{username}%',))
                    
                    login_history = []
                    for history_row in cursor.fetchall():
                        try:
                            if len(history_row) >= 4:
                                # Extract details from JSONB
                                details = history_row[2] if len(history_row) > 2 and history_row[2] else {}
                                login_history.append({
                                    'timestamp': history_row[0].strftime('%Y-%m-%d %H:%M:%S') if history_row[0] else 'N/A',
                                    'event_type': history_row[1] if len(history_row) > 1 else 'Unknown',
                                    'success': True,  # Assume success for admin logs
                                    'ip_address': str(history_row[3]) if len(history_row) > 3 and history_row[3] else 'N/A',
                                    'details': str(details) if details else 'Admin action'
                                })
                        except Exception as e:
                            self.logger.warning(f"Error processing history row: {e}, row: {history_row}")
                            continue
                    
                    cursor.close()
                    conn.close()
                    
                    return {
                        'device_info': device_info,
                        'active_sessions': active_sessions,
                        'login_history': login_history,
                        'username': username
                    }
                
                except Exception as db_error:
                    self.logger.error(f"Database error in get_user_device_details: {db_error}")
                    if conn:
                        conn.close()
                    raise
                    
        except Exception as e:
            self.logger.error(f"Failed to get user device details {user_id}: {e}")
            return None
    
    def revoke_user_session(self, session_token: str) -> bool:
        """Revoke a specific user session"""
        try:
            with LoggedOperation(f"Revoke User Session: {session_token[:12]}...", self.logger):
                conn = self.db_manager.get_connection()
                if not conn:
                    self.logger.error("Failed to get database connection")
                    return False
                
                try:
                    cursor = conn.cursor()
                    
                    # Get session info before revoking
                    cursor.execute("""
                        SELECT us.user_id, u.username 
                        FROM user_sessions us
                        JOIN users u ON us.user_id = u.id
                        WHERE us.session_token = %s
                    """, (session_token,))
                    
                    session_row = cursor.fetchone()
                    if not session_row:
                        self.logger.warning(f"Session {session_token} not found")
                        cursor.close()
                        conn.close()
                        return False
                    
                    user_id, username = session_row
                    
                    # Revoke the session
                    cursor.execute("""
                        UPDATE user_sessions 
                        SET is_active = false, updated_at = CURRENT_TIMESTAMP
                        WHERE session_token = %s
                    """, (session_token,))
                    
                    success = cursor.rowcount > 0
                    conn.commit()
                    cursor.close()
                    conn.close()
                    
                    if success:
                        self.logger.info(f"Session revoked successfully: {session_token[:12]}... for user {username}")
                        # Log auth event
                        self.db_manager.log_auth_event(
                            "SESSION_REVOKED_BY_ADMIN", 
                            username, 
                            None, 
                            True, 
                            f"Session revoked by admin"
                        )
                    else:
                        self.logger.warning(f"No rows affected when revoking session {session_token}")
                    
                    return success
                
                except Exception as db_error:
                    self.logger.error(f"Database error in revoke_user_session: {db_error}")
                    if conn:
                        conn.rollback()
                        conn.close()
                    raise
                    
        except Exception as e:
            self.logger.error(f"Failed to revoke session {session_token}: {e}")
            return False
    
    def search_users(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search users by username or email"""
        try:
            with LoggedOperation(f"Search Users: {query}", self.logger):
                with self.db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    search_pattern = f"%{query}%"
                    cursor.execute("""
                        SELECT 
                            u.id, u.username, u.email, u.created_at, u.last_login,
                            u.is_active, at.name as account_type
                        FROM users u
                        JOIN account_types at ON u.account_type_id = at.id
                        WHERE (u.username ILIKE %s OR u.email ILIKE %s)
                        ORDER BY u.last_login DESC
                        LIMIT %s
                    """, (search_pattern, search_pattern, limit))
                    
                    users = []
                    for row in cursor.fetchall():
                        users.append({
                            'id': row[0],
                            'username': row[1],
                            'email': row[2],
                            'created_at': row[3],
                            'last_login': row[4],
                            'is_active': row[5],
                            'account_type': row[6]
                        })
                    
                    return users
                    
        except Exception as e:
            self.logger.error(f"Failed to search users: {e}")
            return []
    
    def get_user_details(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed user information"""
        try:
            with LoggedOperation(f"Get User Details: {user_id}", self.logger):
                with self.db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    # Get user info
                    cursor.execute("""
                        SELECT 
                            u.id, u.username, u.email, u.created_at, u.last_login,
                            u.is_active, at.name as account_type, at.description,
                            at.max_devices, at.session_duration_hours
                        FROM users u
                        JOIN account_types at ON u.account_type_id = at.id
                        WHERE u.id = %s
                    """, (user_id,))
                    
                    user_row = cursor.fetchone()
                    if not user_row:
                        return None
                    
                    # Get user sessions
                    cursor.execute("""
                        SELECT device_fingerprint, created_at, last_activity, is_active
                        FROM user_sessions
                        WHERE user_id = %s
                        ORDER BY last_activity DESC
                        LIMIT 10
                    """, (user_id,))
                    
                    sessions = []
                    for session_row in cursor.fetchall():
                        sessions.append({
                            'device_fingerprint': session_row[0][:8] + '...',
                            'created_at': session_row[1],
                            'last_activity': session_row[2],
                            'is_active': session_row[3]
                        })
                    
                    # Get recent audit logs
                    cursor.execute("""
                        SELECT event_type, details, timestamp
                        FROM audit_logs
                        WHERE user_id = %s
                        ORDER BY timestamp DESC
                        LIMIT 20
                    """, (user_id,))
                    
                    audit_logs = []
                    for log_row in cursor.fetchall():
                        audit_logs.append({
                            'event_type': log_row[0],
                            'details': log_row[1],
                            'timestamp': log_row[2]
                        })
                    
                    return {
                        'id': user_row[0],
                        'username': user_row[1],
                        'email': user_row[2],
                        'created_at': user_row[3],
                        'last_login': user_row[4],
                        'is_active': user_row[5],
                        'account_type': user_row[6],
                        'account_description': user_row[7],
                        'max_devices': user_row[8],
                        'session_duration_hours': user_row[9],
                        'sessions': sessions,
                        'audit_logs': audit_logs
                    }
                    
        except Exception as e:
            self.logger.error(f"Failed to get user details: {e}")
            return None
    

    
    def update_user_account_type(self, user_id: int, new_account_type: str) -> Tuple[bool, str]:
        """Update user account type"""
        try:
            with LoggedOperation(f"Update User Account Type: {user_id} -> {new_account_type}", self.logger):
                with self.db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    # Get current user info
                    cursor.execute("SELECT username FROM users WHERE id = %s", (user_id,))
                    user_row = cursor.fetchone()
                    if not user_row:
                        return False, "User not found"
                    
                    username = user_row[0]
                    
                    # Get account type ID
                    cursor.execute("SELECT id FROM account_types WHERE name = %s", (new_account_type,))
                    account_type_row = cursor.fetchone()
                    if not account_type_row:
                        return False, "Invalid account type"
                    
                    account_type_id = account_type_row[0]
                    
                    # Update user account type
                    cursor.execute("""
                        UPDATE users 
                        SET account_type_id = %s 
                        WHERE id = %s
                    """, (account_type_id, user_id))
                    
                    conn.commit()
                    
                    # Log the change
                    log_auth_event(
                        "ADMIN_ACCOUNT_TYPE_CHANGED", 
                        username, 
                        "admin_interface", 
                        True, 
                        f"Account type changed to {new_account_type} by admin"
                    )
                    
                    self.logger.info(f"Account type updated for user {username}: {new_account_type}")
                    return True, f"Account type updated to {new_account_type}"
                    
        except Exception as e:
            self.logger.error(f"Failed to update account type for user {user_id}: {e}")
            return False, f"Error updating account type: {e}"
    
    def deactivate_user(self, user_id: int, reason: str = "Admin action") -> Tuple[bool, str]:
        """Deactivate user account"""
        try:
            with LoggedOperation(f"Deactivate User: {user_id}", self.logger):
                with self.db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    # Get user info
                    cursor.execute("SELECT username FROM users WHERE id = %s", (user_id,))
                    user_row = cursor.fetchone()
                    if not user_row:
                        return False, "User not found"
                    
                    username = user_row[0]
                    
                    # Deactivate user
                    cursor.execute("""
                        UPDATE users 
                        SET is_active = false 
                        WHERE id = %s
                    """, (user_id,))
                    
                    # Deactivate all sessions
                    cursor.execute("""
                        UPDATE user_sessions 
                        SET is_active = false 
                        WHERE user_id = %s
                    """, (user_id,))
                    
                    conn.commit()
                    
                    # Log the action
                    log_security_event(
                        "ADMIN_USER_DEACTIVATED", 
                        "HIGH", 
                        f"User {username} deactivated by admin. Reason: {reason}"
                    )
                    
                    self.logger.warning(f"User deactivated: {username} (Reason: {reason})")
                    return True, f"User {username} deactivated successfully"
                    
        except Exception as e:
            self.logger.error(f"Failed to deactivate user {user_id}: {e}")
            return False, f"Error deactivating user: {e}"
    
    def reactivate_user(self, user_id: int) -> Tuple[bool, str]:
        """Reactivate user account"""
        try:
            with LoggedOperation(f"Reactivate User: {user_id}", self.logger):
                with self.db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    # Get user info
                    cursor.execute("SELECT username FROM users WHERE id = %s", (user_id,))
                    user_row = cursor.fetchone()
                    if not user_row:
                        return False, "User not found"
                    
                    username = user_row[0]
                    
                    # Reactivate user
                    cursor.execute("""
                        UPDATE users 
                        SET is_active = true 
                        WHERE id = %s
                    """, (user_id,))
                    
                    conn.commit()
                    
                    # Log the action
                    log_auth_event(
                        "ADMIN_USER_REACTIVATED", 
                        username, 
                        "admin_interface", 
                        True, 
                        "User reactivated by admin"
                    )
                    
                    self.logger.info(f"User reactivated: {username}")
                    return True, f"User {username} reactivated successfully"
                    
        except Exception as e:
            self.logger.error(f"Failed to reactivate user {user_id}: {e}")
            return False, f"Error reactivating user: {e}"
    
    def revoke_user_sessions(self, user_id: int) -> Tuple[bool, str]:
        """Revoke all active sessions for a user"""
        try:
            with LoggedOperation(f"Revoke User Sessions: {user_id}", self.logger):
                with self.db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    # Get user info
                    cursor.execute("SELECT username FROM users WHERE id = %s", (user_id,))
                    user_row = cursor.fetchone()
                    if not user_row:
                        return False, "User not found"
                    
                    username = user_row[0]
                    
                    # Count active sessions
                    cursor.execute("""
                        SELECT COUNT(*) FROM user_sessions 
                        WHERE user_id = %s AND is_active = true
                    """, (user_id,))
                    active_sessions = cursor.fetchone()[0]
                    
                    # Revoke all sessions
                    cursor.execute("""
                        UPDATE user_sessions 
                        SET is_active = false 
                        WHERE user_id = %s
                    """, (user_id,))
                    
                    conn.commit()
                    
                    # Log the action
                    log_security_event(
                        "ADMIN_SESSIONS_REVOKED", 
                        "MEDIUM", 
                        f"All sessions revoked for user {username} by admin ({active_sessions} sessions)"
                    )
                    
                    self.logger.info(f"Sessions revoked for user {username}: {active_sessions} sessions")
                    return True, f"Revoked {active_sessions} active sessions for {username}"
                    
        except Exception as e:
            self.logger.error(f"Failed to revoke sessions for user {user_id}: {e}")
            return False, f"Error revoking sessions: {e}"
    
    def get_user_statistics(self) -> Dict[str, Any]:
        """Get comprehensive user statistics"""
        try:
            with LoggedOperation("Get User Statistics", self.logger):
                with self.db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    stats = {}
                    
                    # Total users by account type
                    cursor.execute("""
                        SELECT at.name, COUNT(u.id) 
                        FROM account_types at
                        LEFT JOIN users u ON at.id = u.account_type_id AND u.is_active = true
                        GROUP BY at.name
                    """)
                    stats['users_by_type'] = dict(cursor.fetchall())
                    
                    # Users created in last 30 days
                    cursor.execute("""
                        SELECT COUNT(*) FROM users 
                        WHERE created_at >= NOW() - INTERVAL '30 days'
                    """)
                    stats['new_users_30_days'] = cursor.fetchone()[0]
                    
                    # Users logged in last 7 days
                    cursor.execute("""
                        SELECT COUNT(DISTINCT user_id) FROM user_sessions 
                        WHERE last_activity >= NOW() - INTERVAL '7 days'
                    """)
                    stats['active_users_7_days'] = cursor.fetchone()[0]
                    
                    # Average sessions per user
                    cursor.execute("""
                        SELECT AVG(session_count) FROM (
                            SELECT user_id, COUNT(*) as session_count
                            FROM user_sessions
                            GROUP BY user_id
                        ) subq
                    """)
                    avg_sessions = cursor.fetchone()[0]
                    stats['avg_sessions_per_user'] = float(avg_sessions) if avg_sessions else 0.0
                    
                    return stats
                    
        except Exception as e:
            self.logger.error(f"Failed to get user statistics: {e}")
            return {}


# Test function
if __name__ == "__main__":
    from ..database.manager import AuthDatabaseManager
    
    print("🔧 Testing AdminUserManager...")
    
    # Initialize components
    db_manager = AuthDatabaseManager()
    user_manager = AdminUserManager(db_manager)
    
    # Test basic operations
    print(f"Total users: {user_manager.get_total_users()}")
    print(f"Active sessions: {user_manager.get_active_sessions_count()}")
    print(f"Trial users: {user_manager.get_users_by_account_type('trial')}")
    print(f"Paid users: {user_manager.get_users_by_account_type('paid')}")
    
    # Test user statistics
    stats = user_manager.get_user_statistics()
    print(f"User statistics: {stats}")
    
    print("✅ AdminUserManager test completed!") 