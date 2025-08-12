#!/usr/bin/env python3
"""
Session Manager cho ElevenLabs Tool
Handle local session caching với encryption và offline support
"""

import os
import json
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import requests
from pathlib import Path

from ..utils.fingerprint import get_device_fingerprint

class SessionManager:
    """
    Local session management với encryption và caching
    """
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url.rstrip('/')
        self.session_file = self._get_session_file_path()
        self.device_fingerprint = get_device_fingerprint()
        self._encryption_key = None
        
    def _get_session_file_path(self) -> str:
        """Lấy đường dẫn file session"""
        # Lưu session file trong user data directory
        if os.name == 'nt':  # Windows
            app_data = os.environ.get('APPDATA', os.path.expanduser('~'))
            session_dir = os.path.join(app_data, 'ElevenLabsTool')
        else:  # Linux/macOS
            home_dir = os.path.expanduser('~')
            session_dir = os.path.join(home_dir, '.elevenlabs_tool')
        
        # Tạo directory nếu chưa có
        os.makedirs(session_dir, exist_ok=True)
        
        return os.path.join(session_dir, '.session_cache')
    
    def _get_encryption_key(self) -> bytes:
        """Tạo encryption key từ device fingerprint"""
        if self._encryption_key:
            return self._encryption_key
            
        # Sử dụng device fingerprint + salt để tạo key
        password = f"{self.device_fingerprint}_elevenlabs_session".encode()
        salt = b'elevenlabs_salt_2024'  # Fixed salt for consistency
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        self._encryption_key = key
        return key
    
    def _encrypt_data(self, data: str) -> str:
        """Encrypt session data"""
        try:
            key = self._get_encryption_key()
            fernet = Fernet(key)
            encrypted = fernet.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            print(f"Encryption error: {e}")
            return ""
    
    def _decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt session data"""
        try:
            key = self._get_encryption_key()
            fernet = Fernet(key)
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = fernet.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            print(f"Decryption error: {e}")
            return ""
    
    def _create_session_signature(self, session_data: Dict) -> str:
        """Tạo signature để verify tính toàn vẹn của session"""
        # Tạo string từ session data
        data_string = f"{session_data.get('session_token', '')}" \
                     f"{session_data.get('user_id', '')}" \
                     f"{session_data.get('expires_at', '')}" \
                     f"{self.device_fingerprint}"
        
        # Hash với secret
        secret = f"elevenlabs_session_secret_{self.device_fingerprint}"
        signature = hashlib.sha256(f"{data_string}{secret}".encode()).hexdigest()
        return signature
    
    def _verify_session_signature(self, session_data: Dict, stored_signature: str) -> bool:
        """Verify session signature"""
        calculated_signature = self._create_session_signature(session_data)
        return calculated_signature == stored_signature
    
    def save_session(self, session_token: str, user_info: Dict, expires_at: str) -> bool:
        """
        Lưu session vào local cache với encryption
        
        Args:
            session_token: Session token từ server
            user_info: Thông tin user
            expires_at: Thời điểm hết hạn (ISO format)
        """
        try:
            session_data = {
                'session_token': session_token,
                'user_info': user_info,
                'expires_at': expires_at,
                'device_fingerprint': self.device_fingerprint,
                'created_at': datetime.now().isoformat(),
                'api_base_url': self.api_base_url
            }
            
            # Tạo signature
            signature = self._create_session_signature(session_data)
            
            # Tạo final data structure
            final_data = {
                'session_data': session_data,
                'signature': signature,
                'version': '1.0'
            }
            
            # Encrypt và save
            json_data = json.dumps(final_data)
            encrypted_data = self._encrypt_data(json_data)
            
            if not encrypted_data:
                return False
            
            with open(self.session_file, 'w') as f:
                f.write(encrypted_data)
            
            # Set file permissions (Unix/Linux)
            if os.name != 'nt':
                os.chmod(self.session_file, 0o600)  # Read/write for owner only
            
            return True
            
        except Exception as e:
            print(f"Save session error: {e}")
            return False
    
    def load_session(self) -> Optional[Dict]:
        """
        Load session từ local cache
        
        Returns:
            Session data nếu valid, None nếu invalid/expired
        """
        try:
            if not os.path.exists(self.session_file):
                return None
            
            # Read và decrypt
            with open(self.session_file, 'r') as f:
                encrypted_data = f.read().strip()
            
            if not encrypted_data:
                return None
            
            decrypted_data = self._decrypt_data(encrypted_data)
            if not decrypted_data:
                return None
            
            final_data = json.loads(decrypted_data)
            session_data = final_data.get('session_data', {})
            stored_signature = final_data.get('signature', '')
            
            # Verify signature
            if not self._verify_session_signature(session_data, stored_signature):
                print("Session signature verification failed")
                self.clear_session()
                return None
            
            # Verify device fingerprint
            if session_data.get('device_fingerprint') != self.device_fingerprint:
                print("Device fingerprint mismatch")
                self.clear_session()
                return None
            
            # Check expiry
            expires_at_str = session_data.get('expires_at')
            if expires_at_str:
                expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
                if datetime.now() > expires_at:
                    print("Session expired")
                    self.clear_session()
                    return None
            
            return session_data
            
        except Exception as e:
            print(f"Load session error: {e}")
            self.clear_session()
            return None
    
    def clear_session(self) -> bool:
        """Xóa session cache"""
        try:
            if os.path.exists(self.session_file):
                os.remove(self.session_file)
            return True
        except Exception as e:
            print(f"Clear session error: {e}")
            return False
    
    def login(self, username: str, password: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Login user và cache session
        
        Returns:
            (success, user_info, error_message)
        """
        try:
            # Call login API
            response = requests.post(
                f"{self.api_base_url}/auth/login",
                json={
                    'username': username,
                    'password': password
                },
                timeout=10
            )
            
            if response.status_code != 200:
                return False, None, f"Server error: {response.status_code}"
            
            data = response.json()
            
            if not data.get('success'):
                return False, None, data.get('error', 'Login failed')
            
            # Save session cache
            session_token = data.get('session_token')
            user_info = data.get('user_info')
            expires_at = data.get('expires_at')
            
            if session_token and user_info and expires_at:
                self.save_session(session_token, user_info, expires_at)
            
            return True, user_info, None
            
        except requests.RequestException as e:
            return False, None, f"Connection error: {str(e)}"
        except Exception as e:
            return False, None, f"Login error: {str(e)}"
    
    def verify_session_online(self, session_token: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Verify session với server (online)
        
        Returns:
            (valid, user_info, error_message)
        """
        try:
            response = requests.post(
                f"{self.api_base_url}/auth/verify",
                json={'session_token': session_token},
                timeout=10
            )
            
            if response.status_code != 200:
                return False, None, f"Server error: {response.status_code}"
            
            data = response.json()
            
            if data.get('valid'):
                return True, data.get('user_info'), None
            else:
                return False, None, data.get('error', 'Session invalid')
                
        except requests.RequestException as e:
            return False, None, f"Connection error: {str(e)}"
        except Exception as e:
            return False, None, f"Verification error: {str(e)}"
    
    def logout(self, session_token: str = None) -> bool:
        """
        Logout user (revoke session và clear cache)
        """
        try:
            # Log bắt đầu logout
            if hasattr(self, 'logger'):
                self.logger.info("[Logout] Bắt đầu logout user...")
            else:
                print("[Logout] Bắt đầu logout user...")

            # Get session token from cache if not provided
            if not session_token:
                session_data = self.load_session()
                if session_data:
                    session_token = session_data.get('session_token')
                    if hasattr(self, 'logger'):
                        self.logger.info(f"[Logout] Lấy session_token từ cache: {session_token}")
                    else:
                        print(f"[Logout] Lấy session_token từ cache: {session_token}")
                else:
                    if hasattr(self, 'logger'):
                        self.logger.warning("[Logout] Không tìm thấy session_data trong cache!")
                    else:
                        print("[Logout] Không tìm thấy session_data trong cache!")

            # Clear local cache first
            self.clear_session()
            if hasattr(self, 'logger'):
                self.logger.info("[Logout] Đã clear local session cache.")
            else:
                print("[Logout] Đã clear local session cache.")

            # Revoke session on server
            if session_token:
                try:
                    response = requests.post(
                        f"{self.api_base_url}/auth/logout",
                        json={'session_token': session_token},
                        timeout=5
                    )
                    if response.status_code == 200:
                        if hasattr(self, 'logger'):
                            self.logger.info(f"[Logout] Đã gửi request logout lên server, status: {response.status_code}, resp: {response.text}")
                        else:
                            print(f"[Logout] Đã gửi request logout lên server, status: {response.status_code}, resp: {response.text}")
                    else:
                        if hasattr(self, 'logger'):
                            self.logger.warning(f"[Logout] Server trả về lỗi khi logout, status: {response.status_code}, resp: {response.text}")
                        else:
                            print(f"[Logout] Server trả về lỗi khi logout, status: {response.status_code}, resp: {response.text}")
                except Exception as e:
                    if hasattr(self, 'logger'):
                        self.logger.error(f"[Logout] Lỗi khi gửi request logout lên server: {e}")
                    else:
                        print(f"[Logout] Lỗi khi gửi request logout lên server: {e}")
            else:
                if hasattr(self, 'logger'):
                    self.logger.warning("[Logout] Không có session_token để gửi lên server!")
                else:
                    print("[Logout] Không có session_token để gửi lên server!")

            if hasattr(self, 'logger'):
                self.logger.info("[Logout] Logout hoàn tất.")
            else:
                print("[Logout] Logout hoàn tất.")
            return True
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"[Logout] Logout error: {e}")
            else:
                print(f"[Logout] Logout error: {e}")
            return False
    
    def get_current_session(self) -> Optional[Dict]:
        """
        Lấy session hiện tại - REQUIRES ONLINE SERVER VERIFICATION
        
        Returns:
            Session data nếu valid trên server, None nếu không thể verify online
        """
        # Load từ cache
        session_data = self.load_session()
        if not session_data:
            return None
        
        session_token = session_data.get('session_token')
        if not session_token:
            return None
        
        # FORCE ONLINE VERIFICATION - NO OFFLINE FALLBACK
        try:
            valid, user_info, error = self.verify_session_online(session_token)
            if valid and user_info:
                # Update user info từ server
                session_data['user_info'] = user_info
                return session_data
            else:
                # Online verification failed - clear cache và reject
                print(f"Server rejected session: {error}")
                self.clear_session()
                return None
                
        except requests.RequestException as e:
            # Server không khả dụng - REJECT access
            print(f"Server unavailable - authentication failed: {e}")
            print("Application requires active server connection")
            self.clear_session()  # Clear cache để force fresh login khi server up
            return None
        except Exception as e:
            # Lỗi khác - REJECT access  
            print(f"Authentication verification failed: {e}")
            self.clear_session()
            return None
    
    def is_authenticated(self) -> bool:
        """Check xem user có authenticated không"""
        return self.get_current_session() is not None
    
    def has_valid_session(self) -> bool:
        """Check xem có session hợp lệ không (alias for is_authenticated)"""
        return self.is_authenticated()
    
    def is_session_valid(self) -> bool:
        """Check xem session hiện tại có valid không (another alias)"""
        return self.is_authenticated()
    
    def get_user_info(self) -> Optional[Dict]:
        """Lấy thông tin user hiện tại"""
        session_data = self.get_current_session()
        if session_data:
            return session_data.get('user_info')
        return None
    
    def get_session_info(self) -> Dict:
        """Lấy thông tin về session hiện tại (for debugging)"""
        session_data = self.load_session()
        
        if not session_data:
            return {
                'authenticated': False,
                'session_file_exists': os.path.exists(self.session_file)
            }
        
        user_info = session_data.get('user_info', {})
        expires_at_str = session_data.get('expires_at')
        
        time_left = None
        if expires_at_str:
            expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
            time_left = expires_at - datetime.now()
        
        return {
            'authenticated': True,
            'username': user_info.get('username'),
            'account_type': user_info.get('account_type'),
            'expires_at': expires_at_str,
            'time_left_hours': time_left.total_seconds() / 3600 if time_left else None,
            'device_fingerprint': session_data.get('device_fingerprint'),
            'api_base_url': session_data.get('api_base_url')
        }


# Convenience functions
def create_session_manager(api_url: str = "http://localhost:8000") -> SessionManager:
    """Tạo SessionManager instance"""
    return SessionManager(api_url)

def quick_login(username: str, password: str, api_url: str = "http://localhost:8000") -> Tuple[bool, Optional[str]]:
    """Quick login function"""
    session_manager = SessionManager(api_url)
    success, user_info, error = session_manager.login(username, password)
    return success, error

def is_user_authenticated(api_url: str = "http://localhost:8000") -> bool:
    """Check xem user có authenticated không"""
    session_manager = SessionManager(api_url)
    return session_manager.is_authenticated()

def get_current_user(api_url: str = "http://localhost:8000") -> Optional[Dict]:
    """Lấy thông tin user hiện tại"""
    session_manager = SessionManager(api_url)
    return session_manager.get_user_info()

def logout_user(api_url: str = "http://localhost:8000") -> bool:
    """Logout user"""
    session_manager = SessionManager(api_url)
    return session_manager.logout()


# Test function
if __name__ == "__main__":
    session_manager = SessionManager()
    
    print("=== Session Manager Test ===")
    print(f"Session file: {session_manager.session_file}")
    print(f"Device fingerprint: {session_manager.device_fingerprint}")
    
    # Test session info
    session_info = session_manager.get_session_info()
    print(f"Session info: {session_info}")
    
    # Test authentication status
    print(f"Is authenticated: {session_manager.is_authenticated()}")
    
    user_info = session_manager.get_user_info()
    if user_info:
        print(f"User: {user_info.get('username')} ({user_info.get('account_type')})")
    else:
        print("No user logged in") 