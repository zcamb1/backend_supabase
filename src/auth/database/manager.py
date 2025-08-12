import psycopg2
import psycopg2.extras
import json
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import threading

class AuthDatabaseManager:
    """Quản lý database PostgreSQL cho authentication system"""
    
    def __init__(self, 
                 host: str = "dpg-d21hsaidbo4c73e6ghe0-a",
                 port: int = 5432,
                 database: str = "elevenlabs_auth_db_l1le",
                 username: str = "elevenlabs_auth_db_user",
                 password: str = "Dta5busSXW4WPPaasBVvjtyTXT2fXU9t"):
        self.host = host
        self.port = port
        self.database = database
        self.username = username
        self.password = password
        self.lock = threading.Lock()
        self._connection_pool = []
        
    def get_connection(self):
        """Lấy database connection"""
        try:
            return psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.username,
                password=self.password,
                cursor_factory=psycopg2.extras.DictCursor
            )
        except psycopg2.Error as e:
            print(f"Database connection error: {e}")
            return None
    
    def init_database(self):
        """Khởi tạo database và các bảng"""
        with self.lock:
            conn = self.get_connection()
            if not conn:
                return False
                
            try:
                cursor = conn.cursor()
                
                # Bảng account types
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS account_types (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(50) UNIQUE NOT NULL,
                        duration_days INTEGER DEFAULT NULL,
                        max_devices INTEGER DEFAULT 1,
                        features JSONB DEFAULT '{}',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Insert default account types
                cursor.execute('''
                    INSERT INTO account_types (name, duration_days, max_devices, features)
                    VALUES 
                        ('trial', 30, 1, '{"api_usage_limit": 1000}'),
                        ('paid', NULL, 1, '{"api_usage_limit": null}')
                    ON CONFLICT (name) DO NOTHING
                ''')
                
                # Bảng users
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        username VARCHAR(50) UNIQUE NOT NULL,
                        password_hash VARCHAR(255) NOT NULL,
                        account_type_id INTEGER REFERENCES account_types(id) DEFAULT 1,
                        device_fingerprint VARCHAR(255),
                        expires_at TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_active BOOLEAN DEFAULT true
                    )
                ''')
                
                # Bảng sessions
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_sessions (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                        session_token VARCHAR(255) UNIQUE NOT NULL,
                        device_fingerprint VARCHAR(255) NOT NULL,
                        expires_at TIMESTAMP NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_active BOOLEAN DEFAULT true
                    )
                ''')
                
                # Bảng admin users
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS admin_users (
                        id SERIAL PRIMARY KEY,
                        username VARCHAR(50) UNIQUE NOT NULL,
                        password_hash VARCHAR(255) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_login TIMESTAMP,
                        is_active BOOLEAN DEFAULT true
                    )
                ''')
                
                # Bảng audit logs
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS audit_logs (
                        id SERIAL PRIMARY KEY,
                        admin_id INTEGER REFERENCES admin_users(id),
                        action VARCHAR(100) NOT NULL,
                        target_type VARCHAR(50),
                        target_id INTEGER,
                        details JSONB,
                        ip_address INET,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Bảng auth events cho analytics
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS auth_events (
                        id SERIAL PRIMARY KEY,
                        event_type VARCHAR(50) NOT NULL,
                        username VARCHAR(50),
                        device_fingerprint VARCHAR(255),
                        success BOOLEAN DEFAULT FALSE,
                        details TEXT,
                        ip_address INET,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Indexes for performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_device ON users(device_fingerprint)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_token ON user_sessions(session_token)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_user ON user_sessions(user_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_admin ON audit_logs(admin_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_auth_events_type ON auth_events(event_type)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_auth_events_timestamp ON auth_events(timestamp)')
                
                conn.commit()
                cursor.close()
                conn.close()
                return True
                
            except psycopg2.Error as e:
                print(f"Database initialization error: {e}")
                if conn:
                    conn.rollback()
                    conn.close()
                return False
    
    def create_user(self, username: str, password: str, account_type: str = 'trial', 
                   device_fingerprint: str = None, duration_days: int = None) -> Optional[int]:
        """Tạo user mới"""
        with self.lock:
            conn = self.get_connection()
            if not conn:
                return None
                
            try:
                cursor = conn.cursor()
                
                # Hash password
                password_hash = hashlib.sha256(password.encode()).hexdigest()
                
                # Get account type
                cursor.execute('SELECT id, duration_days FROM account_types WHERE name = %s', (account_type,))
                account_type_data = cursor.fetchone()
                if not account_type_data:
                    return None
                
                account_type_id = account_type_data['id']
                default_duration = account_type_data['duration_days']
                
                # Calculate expiry
                expires_at = None
                if duration_days or default_duration:
                    days = duration_days or default_duration
                    expires_at = datetime.now() + timedelta(days=days)
                
                # Insert user
                cursor.execute('''
                    INSERT INTO users (username, password_hash, account_type_id, device_fingerprint, expires_at)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                ''', (username, password_hash, account_type_id, device_fingerprint, expires_at))
                
                user_id = cursor.fetchone()['id']
                conn.commit()
                cursor.close()
                conn.close()
                return user_id
                
            except psycopg2.Error as e:
                print(f"Create user error: {e}")
                if conn:
                    conn.rollback()
                    conn.close()
                return None
    
    def user_exists(self, username: str) -> bool:
        """Check if user exists by username"""
        conn = self.get_connection()
        if not conn:
            return False
            
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM users WHERE username = %s', (username,))
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            return result is not None
            
        except psycopg2.Error as e:
            print(f"User exists check error: {e}")
            if conn:
                conn.close()
            return False
    
    def authenticate_user(self, username: str, password: str, device_fingerprint: str) -> Optional[Dict]:
        """Xác thực user và kiểm tra device"""
        with self.lock:
            conn = self.get_connection()
            if not conn:
                return None
                
            try:
                cursor = conn.cursor()
                
                # Hash password for comparison
                password_hash = hashlib.sha256(password.encode()).hexdigest()
                
                # Get user info with account type
                cursor.execute('''
                    SELECT u.id, u.username, u.password_hash, u.device_fingerprint, 
                           u.expires_at, u.is_active, at.name as account_type, at.max_devices
                    FROM users u
                    JOIN account_types at ON u.account_type_id = at.id
                    WHERE u.username = %s AND u.is_active = true
                ''', (username,))
                
                user = cursor.fetchone()
                if not user or user['password_hash'] != password_hash:
                    return {'success': False, 'error': 'Invalid credentials'}
                
                # Check expiry
                if user['expires_at'] and datetime.now() > user['expires_at']:
                    return {'success': False, 'error': 'Account expired'}
                
                # Check device binding
                if user['device_fingerprint']:
                    if user['device_fingerprint'] != device_fingerprint:
                        return {'success': False, 'error': 'Account is bound to another device'}
                else:
                    # Bind device on first login
                    cursor.execute(
                        'UPDATE users SET device_fingerprint = %s WHERE id = %s',
                        (device_fingerprint, user['id'])
                    )
                    conn.commit()
                
                cursor.close()
                conn.close()
                
                return {
                    'success': True,
                    'user_id': user['id'],
                    'username': user['username'],
                    'account_type': user['account_type'],
                    'expires_at': user['expires_at'].isoformat() if user['expires_at'] else None
                }
                
            except psycopg2.Error as e:
                print(f"Authentication error: {e}")
                if conn:
                    conn.close()
                return {'success': False, 'error': 'Database error'}
    
    def create_session(self, user_id: int, device_fingerprint: str, duration_hours: int = 24) -> Optional[str]:
        """Tạo session mới"""
        with self.lock:
            conn = self.get_connection()
            if not conn:
                return None
                
            try:
                cursor = conn.cursor()
                
                # Generate session token
                session_token = secrets.token_urlsafe(32)
                expires_at = datetime.now() + timedelta(hours=duration_hours)
                
                # Insert session
                cursor.execute('''
                    INSERT INTO user_sessions (user_id, session_token, device_fingerprint, expires_at)
                    VALUES (%s, %s, %s, %s)
                    RETURNING session_token
                ''', (user_id, session_token, device_fingerprint, expires_at))
                
                token = cursor.fetchone()['session_token']
                conn.commit()
                cursor.close()
                conn.close()
                return token
                
            except psycopg2.Error as e:
                print(f"Create session error: {e}")
                if conn:
                    conn.rollback()
                    conn.close()
                return None
    
    def verify_session(self, session_token: str, device_fingerprint: str) -> Optional[Dict]:
        """Verify session và return user info"""
        with self.lock:
            conn = self.get_connection()
            if not conn:
                return None
                
            try:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT s.user_id, s.expires_at, s.is_active, u.username, u.is_active as user_active,
                           u.expires_at as user_expires, at.name as account_type
                    FROM user_sessions s
                    JOIN users u ON s.user_id = u.id
                    JOIN account_types at ON u.account_type_id = at.id
                    WHERE s.session_token = %s AND s.device_fingerprint = %s
                ''', (session_token, device_fingerprint))
                
                session = cursor.fetchone()
                if not session:
                    return {'valid': False, 'error': 'Invalid session'}
                
                if not session['is_active'] or not session['user_active']:
                    return {'valid': False, 'error': 'Session or user inactive'}
                
                if datetime.now() > session['expires_at']:
                    return {'valid': False, 'error': 'Session expired'}
                
                if session['user_expires'] and datetime.now() > session['user_expires']:
                    return {'valid': False, 'error': 'Account expired'}
                
                # Update last activity
                cursor.execute(
                    'UPDATE user_sessions SET last_activity = CURRENT_TIMESTAMP WHERE session_token = %s',
                    (session_token,)
                )
                conn.commit()
                
                cursor.close()
                conn.close()
                
                return {
                    'valid': True,
                    'user_id': session['user_id'],
                    'username': session['username'],
                    'account_type': session['account_type']
                }
                
            except psycopg2.Error as e:
                print(f"Verify session error: {e}")
                if conn:
                    conn.close()
                return {'valid': False, 'error': 'Database error'}
    
    def revoke_session(self, session_token: str) -> bool:
        """Revoke session"""
        with self.lock:
            conn = self.get_connection()
            if not conn:
                return False
                
            try:
                cursor = conn.cursor()
                cursor.execute(
                    'UPDATE user_sessions SET is_active = false WHERE session_token = %s',
                    (session_token,)
                )
                affected = cursor.rowcount
                conn.commit()
                cursor.close()
                conn.close()
                return affected > 0
                
            except psycopg2.Error as e:
                print(f"Revoke session error: {e}")
                if conn:
                    conn.rollback()
                    conn.close()
                return False
    
    def get_active_sessions(self) -> List[Dict]:
        """Lấy danh sách active sessions"""
        conn = self.get_connection()
        if not conn:
            return []
            
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT s.id, s.session_token, s.device_fingerprint, s.created_at, 
                       s.last_activity, s.expires_at, u.username, at.name as account_type
                FROM user_sessions s
                JOIN users u ON s.user_id = u.id
                JOIN account_types at ON u.account_type_id = at.id
                WHERE s.is_active = true AND s.expires_at > CURRENT_TIMESTAMP
                ORDER BY s.last_activity DESC
            ''')
            
            sessions = []
            for row in cursor.fetchall():
                sessions.append(dict(row))
            
            cursor.close()
            conn.close()
            return sessions
            
        except psycopg2.Error as e:
            print(f"Get sessions error: {e}")
            if conn:
                conn.close()
            return []
    
    def get_users(self, include_inactive: bool = False) -> List[Dict]:
        """Lấy danh sách users"""
        conn = self.get_connection()
        if not conn:
            return []
            
        try:
            cursor = conn.cursor()
            
            where_clause = "" if include_inactive else "WHERE u.is_active = true"
            
            cursor.execute(f'''
                SELECT u.id, u.username, u.device_fingerprint, u.expires_at, 
                       u.created_at, u.is_active, at.name as account_type
                FROM users u
                JOIN account_types at ON u.account_type_id = at.id
                {where_clause}
                ORDER BY u.created_at DESC
            ''')
            
            users = []
            for row in cursor.fetchall():
                users.append(dict(row))
            
            cursor.close()
            conn.close()
            return users
            
        except psycopg2.Error as e:
            print(f"Get users error: {e}")
            if conn:
                conn.close()
            return []
    
    def delete_user(self, user_id: int) -> bool:
        """Xóa user"""
        with self.lock:
            conn = self.get_connection()
            if not conn:
                return False
                
            try:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM users WHERE id = %s', (user_id,))
                conn.commit()
                cursor.close()
                conn.close()
                return True
                
            except psycopg2.Error as e:
                print(f"Delete user error: {e}")
                if conn:
                    conn.rollback()
                    conn.close()
                return False

    def log_auth_event(self, event_type: str, username: str = None, device_fingerprint: str = None, 
                      success: bool = False, details: str = None, ip_address: str = None) -> bool:
        """Log authentication event for analytics"""
        with self.lock:
            conn = self.get_connection()
            if not conn:
                return False
                
            try:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO auth_events (event_type, username, device_fingerprint, success, details, ip_address)
                    VALUES (%s, %s, %s, %s, %s, %s)
                ''', (event_type, username, device_fingerprint, success, details, ip_address))
                
                conn.commit()
                cursor.close()
                conn.close()
                return True
                
            except psycopg2.Error as e:
                print(f"Log auth event error: {e}")
                if conn:
                    conn.rollback()
                    conn.close()
                return False 