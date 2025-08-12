#!/usr/bin/env python3
"""
Admin Web Interface cho ElevenLabs Authentication System
FastAPI-based admin dashboard với user management, analytics, và monitoring
"""

from fastapi import FastAPI, Depends, HTTPException, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
import json
import os

# Import authentication components
from ..database.manager import AuthDatabaseManager
from ..utils.logger import get_logger, log_auth_event, log_security_event, LoggedOperation
from ..utils.fingerprint import get_device_fingerprint
from .user_manager import AdminUserManager
from .analytics import AdminAnalytics
from .monitoring import SystemMonitor

class AdminWebInterface:
    """
    Web-based admin interface cho authentication system management
    """
    
    def __init__(self, database_url: str = "postgresql://elevenlabs_auth_db_user:Dta5busSXW4WPPaasBVvjtyTXT2fXU9t@dpg-d21hsaidbo4c73e6ghe0-a/elevenlabs_auth_db_l1le", admin_username: str = "admin", admin_password: str = "admin123"):
        self.database_url = database_url
        self.admin_username = admin_username
        self.admin_password_hash = hashlib.sha256(admin_password.encode()).hexdigest()
        self.logger = get_logger("admin_web")
        
        # Parse database URL or use default parameters
        if database_url and database_url.startswith('postgresql://'):
            # Parse postgresql://username:password@host:port/database
            import urllib.parse
            parsed = urllib.parse.urlparse(database_url)
            db_host = parsed.hostname or 'localhost'
            db_port = parsed.port or 5432
            db_name = parsed.path.lstrip('/') or 'elevenlabs_auth'
            db_user = parsed.username or 'postgres'
            db_pass = parsed.password or 'postgres'
        else:
            # Use default parameters
            db_host = 'localhost'
            db_port = 5432
            db_name = 'elevenlabs_auth'
            db_user = 'postgres'
            db_pass = '123456'
        
        # Initialize components with correct parameters
        self.db_manager = AuthDatabaseManager(
            host=db_host,
            port=db_port,
            database=db_name,
            username=db_user,
            password=db_pass
        )
        self.user_manager = AdminUserManager(self.db_manager)
        self.analytics = AdminAnalytics(self.db_manager)
        self.monitor = SystemMonitor(self.db_manager)
        
        # Setup templates directory
        self.templates_dir = os.path.join(os.path.dirname(__file__), "templates")
        
        try:
            os.makedirs(self.templates_dir, exist_ok=True)
            with LoggedOperation("Initialize Admin Web Interface", self.logger):
                self._create_templates()
        except Exception as e:
            self.logger.warning(f"Template creation failed: {e}")
            # Continue without templates - will use basic responses
    
    def _create_templates(self):
        """Create HTML templates for admin interface"""
        # Create base template
        base_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ElevenLabs Admin Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        body { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        .glass { background: rgba(255, 255, 255, 0.1); backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.2); }
    </style>
</head>
<body class="min-h-screen">
    <nav class="glass border-b border-white/20 p-4">
        <div class="container mx-auto flex justify-between items-center">
            <div class="flex items-center space-x-4">
                <i class="fas fa-shield-alt text-white text-2xl"></i>
                <h1 class="text-white text-xl font-bold">ElevenLabs Admin</h1>
            </div>
            <div class="flex space-x-4">
                <a href="/admin/dashboard" class="text-white hover:text-blue-200 transition-colors">
                    <i class="fas fa-tachometer-alt mr-2"></i>Dashboard
                </a>
                <a href="/admin/users" class="text-white hover:text-blue-200 transition-colors">
                    <i class="fas fa-users mr-2"></i>Users
                </a>
                <a href="/admin/analytics" class="text-white hover:text-blue-200 transition-colors">
                    <i class="fas fa-chart-bar mr-2"></i>Analytics
                </a>
                <a href="/admin/logs" class="text-white hover:text-blue-200 transition-colors">
                    <i class="fas fa-file-alt mr-2"></i>Logs
                </a>
                <a href="/admin/logout" class="text-red-200 hover:text-red-100 transition-colors">
                    <i class="fas fa-sign-out-alt mr-2"></i>Logout
                </a>
            </div>
        </div>
    </nav>
    
    <main class="container mx-auto p-6">
        {% block content %}{% endblock %}
    </main>
    
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
        // Auto-refresh data every 30 seconds
        setInterval(() => {
            if (typeof refreshData === 'function') {
                refreshData();
            }
        }, 30000);
    </script>
</body>
</html>
        """
        
        # Create dashboard template
        dashboard_template = """
{% extends "base.html" %}
{% block content %}
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
    <!-- Stats Cards -->
    <div class="glass rounded-lg p-6 text-white">
        <div class="flex items-center justify-between">
            <div>
                <p class="text-blue-200 text-sm">Total Users</p>
                <p class="text-3xl font-bold">{{ stats.total_users }}</p>
            </div>
            <i class="fas fa-users text-4xl text-blue-300"></i>
        </div>
    </div>
    
    <div class="glass rounded-lg p-6 text-white">
        <div class="flex items-center justify-between">
            <div>
                <p class="text-green-200 text-sm">Active Sessions</p>
                <p class="text-3xl font-bold">{{ stats.active_sessions }}</p>
            </div>
            <i class="fas fa-circle text-4xl text-green-300"></i>
        </div>
    </div>
    
    <div class="glass rounded-lg p-6 text-white">
        <div class="flex items-center justify-between">
            <div>
                <p class="text-yellow-200 text-sm">Trial Accounts</p>
                <p class="text-3xl font-bold">{{ stats.trial_users }}</p>
            </div>
            <i class="fas fa-clock text-4xl text-yellow-300"></i>
        </div>
    </div>
    
    <div class="glass rounded-lg p-6 text-white">
        <div class="flex items-center justify-between">
            <div>
                <p class="text-purple-200 text-sm">Paid Accounts</p>
                <p class="text-3xl font-bold">{{ stats.paid_users }}</p>
            </div>
            <i class="fas fa-crown text-4xl text-purple-300"></i>
        </div>
    </div>
</div>

<div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
    <!-- Recent Activity -->
    <div class="glass rounded-lg p-6">
        <h3 class="text-white text-xl font-bold mb-4">
            <i class="fas fa-clock mr-2"></i>Recent Activity
        </h3>
        <div class="space-y-3 max-h-96 overflow-y-auto">
            {% for activity in recent_activities %}
            <div class="flex items-center space-x-3 p-3 bg-white/10 rounded-lg">
                <div class="w-2 h-2 bg-{{ activity.color }}-400 rounded-full"></div>
                <div class="flex-1">
                    <p class="text-white text-sm">{{ activity.message }}</p>
                    <p class="text-gray-300 text-xs">{{ activity.timestamp }}</p>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>
    
    <!-- System Health -->
    <div class="glass rounded-lg p-6">
        <h3 class="text-white text-xl font-bold mb-4">
            <i class="fas fa-heartbeat mr-2"></i>System Health
        </h3>
        <div class="space-y-4">
            <div class="flex justify-between items-center">
                <span class="text-gray-300">Database</span>
                <span class="px-3 py-1 rounded-full text-xs {{ 'bg-green-500 text-white' if health.database else 'bg-red-500 text-white' }}">
                    {{ 'Online' if health.database else 'Offline' }}
                </span>
            </div>
            <div class="flex justify-between items-center">
                <span class="text-gray-300">Authentication API</span>
                <span class="px-3 py-1 rounded-full text-xs {{ 'bg-green-500 text-white' if health.auth_api else 'bg-red-500 text-white' }}">
                    {{ 'Online' if health.auth_api else 'Offline' }}
                </span>
            </div>
            <div class="flex justify-between items-center">
                <span class="text-gray-300">Logging System</span>
                <span class="px-3 py-1 rounded-full text-xs {{ 'bg-green-500 text-white' if health.logging else 'bg-red-500 text-white' }}">
                    {{ 'Online' if health.logging else 'Offline' }}
                </span>
            </div>
        </div>
    </div>
</div>

<script>
function refreshData() {
    fetch('/admin/api/dashboard-data')
        .then(response => response.json())
        .then(data => {
            // Update stats
            document.querySelector('[data-stat="total_users"]').textContent = data.stats.total_users;
            document.querySelector('[data-stat="active_sessions"]').textContent = data.stats.active_sessions;
            // ... update other elements
        })
        .catch(error => console.error('Error refreshing data:', error));
}
</script>
{% endblock %}
        """
        
        # Create users template
        users_template = """
{% extends "base.html" %}
{% block content %}
<div class="flex justify-between items-center mb-6">
    <h2 class="text-2xl font-bold text-white">User Management</h2>
    <button onclick="openCreateUserModal()" class="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-lg">
        <i class="fas fa-plus mr-2"></i>Add New User
    </button>
</div>

<!-- Users Table -->
<div class="glass rounded-lg overflow-hidden">
    <div class="overflow-x-auto">
        <table class="w-full text-white">
            <thead class="bg-white/20">
                <tr>
                    <th class="p-4 text-left">ID</th>
                    <th class="p-4 text-left">Username</th>
                    <th class="p-4 text-left">Account Type</th>
                    <th class="p-4 text-left">Created</th>
                    <th class="p-4 text-left">Status</th>
                    <th class="p-4 text-left">Actions</th>
                </tr>
            </thead>
            <tbody>
                {% for user in users %}
                <tr class="border-b border-white/10 hover:bg-white/5">
                    <td class="p-4">{{ user.id }}</td>
                                         <td class="p-4">
                         <div class="font-semibold">{{ user.username }}</div>
                         <div class="text-sm text-gray-300">{{ user.device_fingerprint[:8] if user.device_fingerprint else 'No Device' }}...</div>
                     </td>
                    <td class="p-4">
                        <span class="px-3 py-1 rounded-full text-xs {{ 'bg-yellow-500' if user.account_type == 'trial' else 'bg-purple-500' }}">
                            {{ user.account_type.title() }}
                        </span>
                    </td>
                    <td class="p-4 text-sm">{{ user.created_at.strftime('%Y-%m-%d') if user.created_at else 'N/A' }}</td>
                    <td class="p-4">
                        <span class="px-3 py-1 rounded-full text-xs {{ 'bg-green-500' if user.is_active else 'bg-red-500' }}">
                            {{ 'Active' if user.is_active else 'Inactive' }}
                        </span>
                    </td>
                    <td class="p-4">
                        <div class="flex space-x-2">
                            <button onclick="editUser({{ user.id }}, '{{ user.account_type }}')" 
                                    class="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded text-sm">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button onclick="toggleUserStatus({{ user.id }})" 
                                    class="bg-orange-500 hover:bg-orange-600 text-white px-3 py-1 rounded text-sm">
                                <i class="fas fa-toggle-{{ 'off' if user.is_active else 'on' }}"></i>
                            </button>
                            <button onclick="deleteUser({{ user.id }}, '{{ user.username }}')" 
                                    class="bg-red-500 hover:bg-red-600 text-white px-3 py-1 rounded text-sm">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>

<!-- Create User Modal -->
<div id="createUserModal" class="fixed inset-0 bg-black bg-opacity-50 hidden z-50">
    <div class="flex items-center justify-center min-h-screen">
        <div class="glass rounded-lg p-6 w-96">
            <h3 class="text-xl font-bold text-white mb-4">Create New User</h3>
            <form id="createUserForm">
                <div class="mb-4">
                    <label class="block text-white text-sm font-bold mb-2">Username</label>
                    <input type="text" name="username" required 
                           class="w-full px-3 py-2 bg-white/20 text-white rounded border border-white/30 focus:border-white/50">
                </div>
                <div class="mb-4">
                    <label class="block text-white text-sm font-bold mb-2">Password</label>
                    <input type="password" name="password" required 
                           class="w-full px-3 py-2 bg-white/20 text-white rounded border border-white/30 focus:border-white/50">
                </div>
                <div class="mb-6">
                    <label class="block text-white text-sm font-bold mb-2">Account Type</label>
                    <select name="account_type" 
                            class="w-full px-3 py-2 bg-white/20 text-white rounded border border-white/30 focus:border-white/50">
                        {% for account_type in account_types %}
                        <option value="{{ account_type.name }}">{{ account_type.name.title() }}</option>
                        {% endfor %}
                    </select>
                </div>
                <div class="flex justify-end space-x-3">
                    <button type="button" onclick="closeCreateUserModal()" 
                            class="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded">
                        Cancel
                    </button>
                    <button type="submit" 
                            class="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded">
                        Create User
                    </button>
                </div>
            </form>
        </div>
    </div>
</div>

<!-- Edit User Modal -->
<div id="editUserModal" class="fixed inset-0 bg-black bg-opacity-50 hidden z-50">
    <div class="flex items-center justify-center min-h-screen">
        <div class="glass rounded-lg p-6 w-96">
            <h3 class="text-xl font-bold text-white mb-4">Edit User</h3>
            <form id="editUserForm">
                <input type="hidden" name="user_id" id="editUserId">
                <div class="mb-6">
                    <label class="block text-white text-sm font-bold mb-2">Account Type</label>
                    <select name="account_type" id="editAccountType"
                            class="w-full px-3 py-2 bg-white/20 text-white rounded border border-white/30 focus:border-white/50">
                        {% for account_type in account_types %}
                        <option value="{{ account_type.name }}">{{ account_type.name.title() }}</option>
                        {% endfor %}
                    </select>
                </div>
                <div class="flex justify-end space-x-3">
                    <button type="button" onclick="closeEditUserModal()" 
                            class="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded">
                        Cancel
                    </button>
                    <button type="submit" 
                            class="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded">
                        Update User
                    </button>
                </div>
            </form>
        </div>
    </div>
</div>

<script>
// User Management JavaScript
function openCreateUserModal() {
    document.getElementById('createUserModal').classList.remove('hidden');
}

function closeCreateUserModal() {
    document.getElementById('createUserModal').classList.add('hidden');
    document.getElementById('createUserForm').reset();
}

function editUser(userId, accountType) {
    document.getElementById('editUserId').value = userId;
    document.getElementById('editAccountType').value = accountType;
    document.getElementById('editUserModal').classList.remove('hidden');
}

function closeEditUserModal() {
    document.getElementById('editUserModal').classList.add('hidden');
}

function toggleUserStatus(userId) {
    if (confirm('Are you sure you want to toggle this user status?')) {
        fetch(`/admin/api/users/${userId}/toggle-status`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                alert('Error: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error toggling user status');
        });
    }
}

function deleteUser(userId, username) {
    if (confirm(`Are you sure you want to delete user "${username}"?`)) {
        fetch(`/admin/api/users/${userId}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                alert('Error: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error deleting user');
        });
    }
}

// Create user form handler
document.getElementById('createUserForm').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const formData = new FormData(this);
    
    fetch('/admin/api/users', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload();
        } else {
            alert('Error: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error creating user');
    });
});

// Edit user form handler
document.getElementById('editUserForm').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const formData = new FormData(this);
    const userId = formData.get('user_id');
    
    fetch(`/admin/api/users/${userId}`, {
        method: 'PUT',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload();
        } else {
            alert('Error: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error updating user');
    });
});
</script>
{% endblock %}
        """

        # Write templates to files - Skip if already exists to preserve user changes
        base_path = os.path.join(self.templates_dir, "base.html")
        if not os.path.exists(base_path):
            with open(base_path, "w", encoding="utf-8") as f:
                f.write(base_template)
        
        dashboard_path = os.path.join(self.templates_dir, "dashboard.html")
        if not os.path.exists(dashboard_path):
            with open(dashboard_path, "w", encoding="utf-8") as f:
                f.write(dashboard_template)
        
        # NEVER overwrite users.html - preserve user changes
        users_path = os.path.join(self.templates_dir, "users.html")
        if not os.path.exists(users_path):
            with open(users_path, "w", encoding="utf-8") as f:
                f.write(users_template)
        
        self.logger.info("Admin templates created successfully")
    
    def verify_admin_credentials(self, credentials: HTTPBasicCredentials) -> bool:
        """Verify admin login credentials"""
        try:
            username_correct = secrets.compare_digest(credentials.username, self.admin_username)
            password_hash = hashlib.sha256(credentials.password.encode()).hexdigest()
            password_correct = secrets.compare_digest(password_hash, self.admin_password_hash)
            
            if username_correct and password_correct:
                log_auth_event(
                    "ADMIN_LOGIN_SUCCESS", 
                    credentials.username, 
                    get_device_fingerprint(), 
                    True, 
                    "Admin logged into web interface"
                )
                return True
            else:
                log_security_event(
                    "ADMIN_LOGIN_FAILED", 
                    "HIGH", 
                    f"Failed admin login attempt: {credentials.username}"
                )
                return False
                
        except Exception as e:
            self.logger.error(f"Admin credential verification error: {e}")
            return False
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get dashboard statistics"""
        try:
            with LoggedOperation("Get Dashboard Stats", self.logger):
                return {
                    'total_users': self.user_manager.get_total_users(),
                    'active_sessions': self.user_manager.get_active_sessions_count(),
                    'trial_users': self.user_manager.get_users_by_account_type('trial'),
                    'paid_users': self.user_manager.get_users_by_account_type('paid'),
                    'recent_logins': self.analytics.get_recent_logins(limit=24),
                    'system_health': self.monitor.get_system_health()
                }
        except Exception as e:
            self.logger.error(f"Failed to get dashboard stats: {e}")
            return {
                'total_users': 0,
                'active_sessions': 0, 
                'trial_users': 0,
                'paid_users': 0,
                'recent_logins': 0,
                'system_health': {'database': False, 'auth_api': False, 'logging': False}
            }
    
    def get_recent_activities(self, limit: int = 20) -> List[Dict]:
        """Get recent system activities"""
        try:
            activities = self.analytics.get_recent_activities(limit)
            formatted_activities = []
            
            for activity in activities:
                color = self._get_activity_color(activity['event_type'])
                formatted_activities.append({
                    'message': self._format_activity_message(activity),
                    'timestamp': activity['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                    'color': color
                })
            
            return formatted_activities
            
        except Exception as e:
            self.logger.error(f"Failed to get recent activities: {e}")
            return []
    
    def _get_activity_color(self, event_type: str) -> str:
        """Get color for activity type"""
        color_map = {
            'LOGIN_SUCCESS': 'green',
            'LOGIN_FAILED': 'red', 
            'USER_CREATED': 'blue',
            'SESSION_EXPIRED': 'yellow',
            'ADMIN_ACTION': 'purple',
            'SECURITY_EVENT': 'red'
        }
        return color_map.get(event_type, 'gray')
    
    def _format_activity_message(self, activity: Dict) -> str:
        """Format activity message for display"""
        event_type = activity['event_type']
        username = activity.get('username', 'Unknown')
        details = activity.get('details', '')
        
        message_templates = {
            'LOGIN_SUCCESS': f"User {username} logged in successfully",
            'LOGIN_FAILED': f"Failed login attempt for {username}",
            'USER_CREATED': f"New user {username} created",
            'SESSION_EXPIRED': f"Session expired for {username}",
            'ADMIN_ACTION': f"Admin action: {details}",
            'SECURITY_EVENT': f"Security event: {details}"
        }
        
        return message_templates.get(event_type, f"{event_type}: {details}")


def create_admin_app(database_url: str = None, admin_username: str = "admin", admin_password: str = "admin123") -> FastAPI:
    """
    Create FastAPI admin application
    
    Args:
        database_url: Database connection URL
        admin_username: Admin login username
        admin_password: Admin login password
        
    Returns:
        FastAPI application instance
    """
    
    # Initialize admin interface
    admin_interface = AdminWebInterface(database_url, admin_username, admin_password)
    logger = get_logger("admin_app")
    
    # Create FastAPI app
    app = FastAPI(
        title="ElevenLabs Admin Interface",
        description="Admin dashboard cho ElevenLabs Authentication System",
        version="1.0.0"
    )
    
    # Setup templates
    templates = Jinja2Templates(directory=admin_interface.templates_dir)
    
    # Setup static files
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    os.makedirs(static_dir, exist_ok=True)
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    
    # Security
    security = HTTPBasic()
    
    def get_current_admin(credentials: HTTPBasicCredentials = Depends(security)):
        if not admin_interface.verify_admin_credentials(credentials):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid admin credentials",
                headers={"WWW-Authenticate": "Basic"},
            )
        return credentials.username
    
    # Routes
    @app.get("/", response_class=RedirectResponse)
    async def root():
        return RedirectResponse(url="/admin/dashboard")
    
    @app.get("/admin/dashboard", response_class=HTMLResponse)
    async def admin_dashboard(request: Request, admin_user: str = Depends(get_current_admin)):
        """Admin dashboard page"""
        try:
            with LoggedOperation(f"Admin Dashboard Access: {admin_user}", logger):
                
                # Get dashboard data
                stats = admin_interface.get_dashboard_stats()
                recent_activities = admin_interface.get_recent_activities()
                health = admin_interface.monitor.get_system_health()
                
                # Log admin access
                log_auth_event(
                    "ADMIN_DASHBOARD_ACCESS", 
                    admin_user, 
                    get_device_fingerprint(), 
                    True, 
                    "Admin accessed dashboard"
                )
                
                return templates.TemplateResponse("dashboard.html", {
                    "request": request,
                    "stats": stats,
                    "recent_activities": recent_activities,
                    "health": health,
                    "admin_user": admin_user
                })
                
        except Exception as e:
            logger.error(f"Dashboard error for admin {admin_user}: {e}")
            raise HTTPException(status_code=500, detail="Dashboard error")
    
    @app.get("/admin/api/dashboard-data")
    async def get_dashboard_data(admin_user: str = Depends(get_current_admin)):
        """API endpoint for dashboard data refresh"""
        try:
            stats = admin_interface.get_dashboard_stats()
            recent_activities = admin_interface.get_recent_activities()
            health = admin_interface.monitor.get_system_health()
            
            return {
                "stats": stats,
                "recent_activities": recent_activities,
                "health": health,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Dashboard data API error: {e}")
            raise HTTPException(status_code=500, detail="Failed to get dashboard data")
    
    @app.get("/admin/users", response_class=HTMLResponse)
    async def admin_users(request: Request, admin_user: str = Depends(get_current_admin)):
        """User management page"""
        try:
            with LoggedOperation(f"Admin Users Access: {admin_user}", logger):
                
                # Get all users
                users = admin_interface.user_manager.get_all_users()
                account_types = admin_interface.user_manager.get_account_types()
                
                # Log admin access
                log_auth_event(
                    "ADMIN_USERS_ACCESS", 
                    admin_user, 
                    get_device_fingerprint(), 
                    True, 
                    "Admin accessed user management"
                )
                
                return templates.TemplateResponse("users.html", {
                    "request": request,
                    "users": users,
                    "account_types": account_types,
                    "admin_user": admin_user
                })
                
        except Exception as e:
            logger.error(f"Users page error for admin {admin_user}: {e}")
            raise HTTPException(status_code=500, detail="Users page error")
    
    @app.get("/admin/analytics", response_class=HTMLResponse)
    async def admin_analytics(request: Request, admin_user: str = Depends(get_current_admin)):
        """Analytics page"""
        # Implementation for analytics
        return HTMLResponse("<h1>Analytics - Coming Soon</h1>")
    
    @app.get("/admin/logs", response_class=HTMLResponse)
    async def admin_logs(request: Request, admin_user: str = Depends(get_current_admin)):
        """Logs viewer page"""
        # Implementation for logs viewer
        return HTMLResponse("<h1>System Logs - Coming Soon</h1>")
    
    # User Management API Endpoints
    @app.post("/admin/api/users")
    async def create_user_api(
        username: str = Form(...),
        password: str = Form(...),
        account_type: str = Form(...),
        admin_user: str = Depends(get_current_admin)
    ):
        """Create new user"""
        try:
            # Check if user already exists first
            if admin_interface.user_manager.db_manager.user_exists(username):
                return {"success": False, "message": f"Username '{username}' already exists"}
            
            user_id = admin_interface.user_manager.create_user(username, password, account_type)
            if user_id:
                log_auth_event(
                    "USER_CREATED", 
                    admin_user, 
                    get_device_fingerprint(), 
                    True, 
                    f"Admin created user: {username}"
                )
                return {"success": True, "message": f"User {username} created successfully", "user_id": user_id}
            else:
                return {"success": False, "message": f"Failed to create user {username}"}
        except Exception as e:
            logger.error(f"Create user API error: {e}")
            return {"success": False, "message": str(e)}
    
    @app.put("/admin/api/users/{user_id}")
    async def update_user_api(
        user_id: int,
        username: str = Form(...),
        password: str = Form(None),
        account_type: str = Form(...),
        admin_user: str = Depends(get_current_admin)
    ):
        """Update user information"""
        try:
            success = admin_interface.user_manager.update_user_full(user_id, username, password, account_type)
            if success:
                log_auth_event(
                    "USER_UPDATED", 
                    admin_user, 
                    get_device_fingerprint(), 
                    True, 
                    f"Admin updated user {user_id}: {username}"
                )
                return {"success": True, "message": "User updated successfully"}
            else:
                return {"success": False, "message": "Failed to update user"}
        except Exception as e:
            logger.error(f"Update user API error: {e}")
            return {"success": False, "message": str(e)}
    
    @app.delete("/admin/api/users/{user_id}")
    async def delete_user_api(
        user_id: int,
        admin_user: str = Depends(get_current_admin)
    ):
        """Delete user"""
        try:
            success = admin_interface.user_manager.delete_user(user_id)
            if success:
                log_auth_event(
                    "USER_DELETED", 
                    admin_user, 
                    get_device_fingerprint(), 
                    True, 
                    f"Admin deleted user {user_id}"
                )
                return {"success": True, "message": "User deleted successfully"}
            else:
                return {"success": False, "message": "Failed to delete user"}
        except Exception as e:
            logger.error(f"Delete user API error: {e}")
            return {"success": False, "message": str(e)}
    
    @app.get("/admin/api/users/{user_id}/devices")
    async def get_user_devices_api(
        user_id: int,
        admin_user: str = Depends(get_current_admin)
    ):
        """Get user device information and sessions"""
        try:
            # First check if user exists
            conn = admin_interface.user_manager.db_manager.get_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute("SELECT username FROM users WHERE id = %s", (user_id,))
                user_row = cursor.fetchone()
                cursor.close()
                conn.close()
                
                if not user_row:
                    return {"success": False, "message": f"User {user_id} not found"}
            
            device_data = admin_interface.user_manager.get_user_device_details(user_id)
            
            # Always return success, even if no device data (new users won't have sessions yet)
            if device_data:
                log_auth_event(
                    "USER_DEVICE_VIEWED", 
                    admin_user, 
                    get_device_fingerprint(), 
                    True, 
                    f"Admin viewed devices for user {user_id}"
                )
                return {"success": True, **device_data}
            else:
                # Return success with empty device data for new users
                return {
                    "success": True, 
                    "devices": [],
                    "active_sessions": [],
                    "login_history": [],
                    "message": f"No device history yet for user {user_id} (may be a new user)"
                }
        except Exception as e:
            logger.error(f"Get user devices API error: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {"success": False, "message": f"API Error: {str(e)}"}
    
    @app.post("/admin/api/sessions/{session_token}/revoke")
    async def revoke_session_api(
        session_token: str,
        admin_user: str = Depends(get_current_admin)
    ):
        """Revoke a specific session"""
        try:
            success = admin_interface.user_manager.revoke_user_session(session_token)
            if success:
                log_auth_event(
                    "SESSION_REVOKED_BY_ADMIN", 
                    admin_user, 
                    get_device_fingerprint(), 
                    True, 
                    f"Admin revoked session {session_token[:12]}..."
                )
                return {"success": True, "message": "Session revoked successfully"}
            else:
                return {"success": False, "message": "Failed to revoke session"}
        except Exception as e:
            logger.error(f"Revoke session API error: {e}")
            return {"success": False, "message": str(e)}
    
    @app.post("/admin/api/users/{user_id}/toggle-status")
    async def toggle_user_status_api(
        user_id: int,
        admin_user: str = Depends(get_current_admin)
    ):
        """Toggle user active status"""
        try:
            success = admin_interface.user_manager.toggle_user_status(user_id)
            if success:
                log_auth_event(
                    "USER_STATUS_CHANGED", 
                    admin_user, 
                    get_device_fingerprint(), 
                    True, 
                    f"Admin toggled status for user {user_id}"
                )
                return {"success": True, "message": "User status updated successfully"}
            else:
                return {"success": False, "message": "Failed to update user status"}
        except Exception as e:
            logger.error(f"Toggle user status API error: {e}")
            return {"success": False, "message": str(e)}

    @app.get("/admin/logout")
    async def admin_logout(admin_user: str = Depends(get_current_admin)):
        """Admin logout"""
        log_auth_event(
            "ADMIN_LOGOUT", 
            admin_user, 
            get_device_fingerprint(), 
            True, 
            "Admin logged out from web interface"
        )
        return {"message": "Logged out successfully"}
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """System health check"""
        health = admin_interface.monitor.get_system_health()
        return {"status": "healthy" if all(health.values()) else "degraded", "health": health}
    
    logger.info("Admin web application created successfully")
    return app


# Test function
if __name__ == "__main__":
    import uvicorn
    
    print("🌐 Starting ElevenLabs Admin Interface...")
    print("📊 Dashboard: http://localhost:8001/admin/dashboard")
    print("🔐 Default login: admin / admin123")
    
    app = create_admin_app()
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info") 