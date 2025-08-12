#!/usr/bin/env python3
"""
Supabase Database Manager cho ElevenLabs Authentication System
Thay thế PostgreSQL manager để sử dụng Supabase
"""
import os
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import threading

from supabase import create_client, Client
from ..utils.logger import get_logger, LoggedOperation

class SupabaseDatabaseManager:
    """Quản lý database Supabase cho authentication system"""
    
    def __init__(self, 
                 supabase_url: str = None,
                 supabase_key: str = None):
        
        # Lấy credentials từ environment hoặc parameters
        self.supabase_url = supabase_url or os.environ.get('SUPABASE_URL')
        self.supabase_key = supabase_key or os.environ.get('SUPABASE_ANON_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Supabase URL và Key phải được cung cấp")
        
        # Khởi tạo Supabase client với options để tránh proxy error
        try:
            self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        except TypeError as e:
            if "proxy" in str(e):
                # Fallback: create client without proxy options
                from supabase import create_client as create_client_simple
                self.supabase: Client = create_client_simple(self.supabase_url, self.supabase_key)
            else:
                raise
        self.lock = threading.Lock()
        # Use simple logger on Vercel
        if os.environ.get('VERCEL'):
            from src.auth.utils.logger import get_simple_logger
            self.logger = get_simple_logger("supabase_db")
        else:
            self.logger = get_logger("supabase_db")
        
        with LoggedOperation("Initialize Supabase Database Manager", self.logger):
            self._test_connection()
    
    def _test_connection(self):
        """Test kết nối đến Supabase"""
        try:
            # Test bằng cách query account_types
            response = self.supabase.table('account_types').select('*').limit(1).execute()
            self.logger.info("✅ Supabase connection successful")
            return True
        except Exception as e:
            self.logger.error(f"❌ Supabase connection failed: {e}")
            raise
    
    def init_database(self) -> bool:
        """Khởi tạo database tables (đã được tạo qua SQL schema)"""
        try:
            with LoggedOperation("Initialize Database Tables", self.logger):
                
                # Kiểm tra các tables đã tồn tại
                tables_to_check = ['account_types', 'users', 'user_sessions', 'admin_users', 'audit_logs', 'auth_events']
                
                for table in tables_to_check:
                    try:
                        response = self.supabase.table(table).select('*').limit(1).execute()
                        self.logger.info(f"✅ Table {table} exists")
                    except Exception as e:
                        self.logger.error(f"❌ Table {table} not found: {e}")
                        return False
                
                # Kiểm tra account types
                response = self.supabase.table('account_types').select('*').execute()
                if not response.data:
                    self.logger.warning("⚠️  No account types found, creating defaults...")
                    self._create_default_account_types()
                
                # Kiểm tra admin user
                response = self.supabase.table('admin_users').select('*').execute()
                if not response.data:
                    self.logger.warning("⚠️  No admin users found, creating default admin...")
                    self._create_default_admin()
                
                self.logger.info("✅ Database initialization completed")
                return True
                
        except Exception as e:
            self.logger.error(f"❌ Database initialization failed: {e}")
            return False
    
    def _create_default_account_types(self):
        """Tạo default account types"""
        try:
            account_types = [
                {'name': 'trial', 'max_devices': 1, 'duration_days': 30},
                {'name': 'paid', 'max_devices': 3, 'duration_days': 365}
            ]
            
            for account_type in account_types:
                self.supabase.table('account_types').insert(account_type).execute()
            
            self.logger.info("✅ Default account types created")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to create account types: {e}")
    
    def _create_default_admin(self):
        """Tạo default admin user"""
        try:
            # Password: admin123
            admin_hash = hashlib.sha256('admin123'.encode()).hexdigest()
            
            admin_user = {
                'username': 'admin',
                'password_hash': admin_hash,
                'is_active': True
            }
            
            self.supabase.table('admin_users').insert(admin_user).execute()
            self.logger.info("✅ Default admin user created (admin/admin123)")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to create admin user: {e}")
    
    def create_user(self, username: str, password: str, account_type: str = 'trial', 
                   device_fingerprint: str = None, duration_days: int = None) -> Optional[int]:
        """Tạo user mới"""
        try:
            with LoggedOperation(f"Create User: {username}", self.logger):
                
                # Hash password
                password_hash = hashlib.sha256(password.encode()).hexdigest()
                
                # Lấy account type ID
                response = self.supabase.table('account_types').select('id').eq('name', account_type).execute()
                if not response.data:
                    self.logger.error(f"❌ Account type '{account_type}' not found")
                    return None
                
                account_type_id = response.data[0]['id']
                
                # Tạo user data
                user_data = {
                    'username': username,
                    'password_hash': password_hash,
                    'account_type_id': account_type_id,
                    'device_fingerprint': device_fingerprint,
                    'is_active': True
                }
                
                # Insert user
                response = self.supabase.table('users').insert(user_data).execute()
                
                if response.data:
                    user_id = response.data[0]['id']
                    self.logger.info(f"✅ User created: {username} (ID: {user_id})")
                    
                    # Log event
                    self.log_auth_event('USER_CREATED', username, device_fingerprint, True, f"Account type: {account_type}")
                    
                    return user_id
                else:
                    self.logger.error(f"❌ Failed to create user: {username}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"❌ Create user error: {e}")
            return None
    
    def user_exists(self, username: str) -> bool:
        """Kiểm tra user có tồn tại không"""
        try:
            response = self.supabase.table('users').select('id').eq('username', username).execute()
            return len(response.data) > 0
        except Exception as e:
            self.logger.error(f"❌ Check user exists error: {e}")
            return False
    
    def authenticate_user(self, username: str, password: str, device_fingerprint: str) -> Optional[Dict]:
        """Xác thực user và kiểm tra device"""
        try:
            with LoggedOperation(f"Authenticate User: {username}", self.logger):
                
                # Hash password
                password_hash = hashlib.sha256(password.encode()).hexdigest()
                
                # Query user với account type và expires_at
                response = self.supabase.table('users').select(
                    'id, username, account_type_id, device_fingerprint, is_active, expires_at, account_types!inner(name)'
                ).eq('username', username).eq('password_hash', password_hash).execute()
                
                if not response.data:
                    self.log_auth_event('LOGIN_FAILED', username, device_fingerprint, False, "Invalid credentials")
                    return {'success': False, 'error': 'Invalid credentials'}
                
                user = response.data[0]
                
                # Kiểm tra user active
                if not user['is_active']:
                    self.log_auth_event('LOGIN_FAILED', username, device_fingerprint, False, "Account inactive")
                    return {'success': False, 'error': 'Account inactive'}
                
                # Kiểm tra expiry
                if user['expires_at']:
                    expires_at = datetime.fromisoformat(user['expires_at'].replace('Z', '+00:00'))
                    if datetime.now(expires_at.tzinfo) > expires_at:
                        return {'success': False, 'error': 'Account expired'}
                
                # Kiểm tra device binding
                if user['device_fingerprint']:
                    if user['device_fingerprint'] != device_fingerprint:
                        self.log_auth_event('LOGIN_FAILED', username, device_fingerprint, False, "Account is bound to another device")
                        return {'success': False, 'error': 'Account is bound to another device'}
                else:
                    # Bind device on first login
                    self.supabase.table('users').update({
                        'device_fingerprint': device_fingerprint,
                        'updated_at': datetime.now().isoformat()
                    }).eq('id', user['id']).execute()
                    self.logger.info(f"🔒 Device fingerprint bound to user {username}: {device_fingerprint}")
                
                # Log successful login
                self.log_auth_event('LOGIN_SUCCESS', username, device_fingerprint, True)
                
                return {
                    'success': True,
                    'user_id': user['id'],
                    'username': user['username'],
                    'account_type': user['account_types']['name'],
                    'expires_at': user['expires_at'] if user['expires_at'] else None
                }
                
        except Exception as e:
            self.logger.error(f"❌ Authentication error: {e}")
            return {'success': False, 'error': 'Database error'}
    
    def create_session(self, user_id: int, device_fingerprint: str, duration_hours: int = 24) -> Optional[str]:
        """Tạo session cho user"""
        try:
            with LoggedOperation(f"Create Session for User: {user_id}", self.logger):
                
                # Tạo session token
                session_token = secrets.token_urlsafe(32)
                expires_at = (datetime.now() + timedelta(hours=duration_hours)).isoformat()
                
                session_data = {
                    'user_id': user_id,
                    'session_token': session_token,
                    'device_fingerprint': device_fingerprint,
                    'is_active': True,
                    'expires_at': expires_at
                }
                
                # Insert session
                response = self.supabase.table('user_sessions').insert(session_data).execute()
                
                if response.data:
                    self.logger.info(f"✅ Session created for user {user_id}")
                    return session_token
                else:
                    self.logger.error(f"❌ Failed to create session for user {user_id}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"❌ Create session error: {e}")
            return None
    
    def verify_session(self, session_token: str, device_fingerprint: str) -> Optional[Dict]:
        """Xác thực session"""
        try:
            with LoggedOperation(f"Verify Session: {session_token[:8]}...", self.logger):
                
                # Query session với user info
                response = self.supabase.table('user_sessions').select(
                    'id, user_id, device_fingerprint, is_active, expires_at, users!inner(id, username, account_type_id, is_active)'
                ).eq('session_token', session_token).execute()
                
                if not response.data:
                    return None
                
                session = response.data[0]
                user = session['users']
                
                # Kiểm tra session active
                if not session['is_active']:
                    return None
                
                # Kiểm tra device fingerprint
                if session['device_fingerprint'] != device_fingerprint:
                    return None
                
                # Kiểm tra expiration
                expires_at = datetime.fromisoformat(session['expires_at'].replace('Z', '+00:00'))
                if expires_at < datetime.now(expires_at.tzinfo):
                    # Session expired, deactivate
                    self.supabase.table('user_sessions').update({'is_active': False}).eq('id', session['id']).execute()
                    return None
                
                # Kiểm tra user active
                if not user['is_active']:
                    return None
                
                # Update last activity
                self.supabase.table('user_sessions').update({
                    'last_activity': datetime.now().isoformat()
                }).eq('id', session['id']).execute()
                
                return {
                    'user_id': user['id'],
                    'username': user['username'],
                    'account_type_id': user['account_type_id']
                }
                
        except Exception as e:
            self.logger.error(f"❌ Verify session error: {e}")
            return None
    
    def revoke_session(self, session_token: str) -> bool:
        """Thu hồi session"""
        try:
            with LoggedOperation(f"Revoke Session: {session_token[:8]}...", self.logger):
                
                response = self.supabase.table('user_sessions').update({
                    'is_active': False
                }).eq('session_token', session_token).execute()
                
                if response.data:
                    self.logger.info(f"✅ Session revoked: {session_token[:8]}...")
                    return True
                else:
                    self.logger.warning(f"⚠️  Session not found: {session_token[:8]}...")
                    return False
                    
        except Exception as e:
            self.logger.error(f"❌ Revoke session error: {e}")
            return False
    
    def get_active_sessions(self) -> List[Dict]:
        """Lấy danh sách active sessions"""
        try:
            response = self.supabase.table('user_sessions').select(
                'id, user_id, session_token, device_fingerprint, created_at, last_activity, expires_at, users!inner(username)'
            ).eq('is_active', True).execute()
            
            sessions = []
            for row in response.data:
                sessions.append({
                    'id': row['id'],
                    'user_id': row['user_id'],
                    'username': row['users']['username'],
                    'session_token': row['session_token'][:8] + '...',
                    'device_fingerprint': row['device_fingerprint'][:8] + '...',
                    'created_at': row['created_at'],
                    'last_activity': row['last_activity'],
                    'expires_at': row['expires_at']
                })
            
            return sessions
            
        except Exception as e:
            self.logger.error(f"❌ Get active sessions error: {e}")
            return []
    
    def get_users(self, include_inactive: bool = False) -> List[Dict]:
        """Lấy danh sách users"""
        try:
            query = self.supabase.table('users').select(
                'id, username, account_type_id, device_fingerprint, is_active, created_at, updated_at, account_types!inner(name)'
            )
            
            if not include_inactive:
                query = query.eq('is_active', True)
            
            response = query.execute()
            
            users = []
            for row in response.data:
                users.append({
                    'id': row['id'],
                    'username': row['username'],
                    'account_type': row['account_types']['name'],
                    'device_fingerprint': row['device_fingerprint'][:8] + '...' if row['device_fingerprint'] else None,
                    'is_active': row['is_active'],
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at']
                })
            
            return users
            
        except Exception as e:
            self.logger.error(f"❌ Get users error: {e}")
            return []
    
    def delete_user(self, user_id: int) -> bool:
        """Xóa user"""
        try:
            with LoggedOperation(f"Delete User: {user_id}", self.logger):
                
                # Get user info before deletion
                response = self.supabase.table('users').select('username').eq('id', user_id).execute()
                if not response.data:
                    return False
                
                username = response.data[0]['username']
                
                # Delete user (sessions will be deleted automatically due to CASCADE)
                response = self.supabase.table('users').delete().eq('id', user_id).execute()
                
                if response.data:
                    self.logger.info(f"✅ User deleted: {username} (ID: {user_id})")
                    self.log_auth_event('USER_DELETED', username, None, True, f"Deleted by admin")
                    return True
                else:
                    self.logger.error(f"❌ Failed to delete user: {user_id}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"❌ Delete user error: {e}")
            return False
    
    def log_auth_event(self, event_type: str, username: str = None, device_fingerprint: str = None, 
                      success: bool = False, details: str = None, ip_address: str = None) -> bool:
        """Log authentication event"""
        try:
            event_data = {
                'event_type': event_type,
                'username': username,
                'device_fingerprint': device_fingerprint,
                'success': success,
                'details': details,
                'timestamp': datetime.now().isoformat()
            }
            
            # Log to auth_events table
            self.supabase.table('auth_events').insert(event_data).execute()
            
            # Also log to audit_logs for security events
            if event_type in ['LOGIN_FAILED', 'SECURITY_VIOLATION', 'USER_DELETED']:
                self.supabase.table('audit_logs').insert(event_data).execute()
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Log auth event error: {e}")
            return False


# Factory function để tạo Supabase manager
def create_supabase_manager(supabase_url: str = None, supabase_key: str = None) -> SupabaseDatabaseManager:
    """Tạo Supabase database manager"""
    return SupabaseDatabaseManager(supabase_url, supabase_key)


# Test function
if __name__ == "__main__":
    print("🧪 Testing Supabase Database Manager...")
    
    # Test với environment variables
    try:
        db_manager = SupabaseDatabaseManager()
        
        # Test connection
        print("✅ Supabase connection successful")
        
        # Test init database
        if db_manager.init_database():
            print("✅ Database initialization successful")
        else:
            print("❌ Database initialization failed")
        
        # Test get users
        users = db_manager.get_users()
        print(f"📊 Found {len(users)} users")
        
        # Test get active sessions
        sessions = db_manager.get_active_sessions()
        print(f"📊 Found {len(sessions)} active sessions")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        print("Hãy kiểm tra SUPABASE_URL và SUPABASE_ANON_KEY environment variables")
