#!/usr/bin/env python3
"""
Admin Analytics cho ElevenLabs Authentication System
Analytics và reporting utilities cho admin dashboard
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import json
from collections import defaultdict

from ..database.manager import AuthDatabaseManager
from ..utils.logger import get_logger, LoggedOperation

class AdminAnalytics:
    """
    Analytics utilities cho admin dashboard
    """
    
    def __init__(self, db_manager: AuthDatabaseManager):
        self.db_manager = db_manager
        self.logger = get_logger("admin_analytics")
    
    def get_recent_logins(self, limit: int = 24) -> int:
        """Get count of recent successful logins"""
        try:
            with LoggedOperation(f"Get Recent Logins (last {limit}h)", self.logger):
                with self.db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    cutoff_time = datetime.now() - timedelta(hours=limit)
                    cursor.execute("""
                        SELECT COUNT(*) FROM auth_events 
                        WHERE event_type = 'LOGIN_SUCCESS' 
                        AND timestamp > %s
                    """, (cutoff_time,))
                    count = cursor.fetchone()[0]
                    return count
                    
        except Exception as e:
            self.logger.error(f"Failed to get recent logins: {e}")
            return 0
    
    def get_recent_activities(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent system activities"""
        try:
            with LoggedOperation(f"Get Recent Activities (limit={limit})", self.logger):
                with self.db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT 
                            ae.event_type, ae.username, ae.details, 
                            ae.timestamp, ae.success
                        FROM auth_events ae
                        ORDER BY ae.timestamp DESC
                        LIMIT %s
                    """, (limit,))
                    
                    activities = []
                    for row in cursor.fetchall():
                        activities.append({
                            'event_type': row[0],
                            'username': row[1] or 'System',
                            'details': row[2],
                            'timestamp': row[3],
                            'success': row[4]
                        })
                    
                    return activities
                    
        except Exception as e:
            self.logger.error(f"Failed to get recent activities: {e}")
            return []
    
    def get_login_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Get login statistics for the last N days"""
        try:
            with LoggedOperation(f"Get Login Statistics ({days} days)", self.logger):
                with self.db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    cutoff_date = datetime.now() - timedelta(days=days)
                    
                    # Daily login counts
                    cursor.execute("""
                        SELECT 
                            DATE(timestamp) as login_date,
                            COUNT(*) as login_count,
                            COUNT(CASE WHEN success = true THEN 1 END) as successful_logins,
                            COUNT(CASE WHEN success = false THEN 1 END) as failed_logins
                        FROM auth_events 
                        WHERE event_type IN ('LOGIN_SUCCESS', 'LOGIN_FAILED')
                        AND timestamp >= %s
                        GROUP BY DATE(timestamp)
                        ORDER BY login_date
                    """, (cutoff_date,))
                    
                    daily_stats = []
                    for row in cursor.fetchall():
                        daily_stats.append({
                            'date': row[0].strftime('%Y-%m-%d'),
                            'total_logins': row[1],
                            'successful_logins': row[2],
                            'failed_logins': row[3],
                            'success_rate': (row[2] / row[1] * 100) if row[1] > 0 else 0
                        })
                    
                    # Overall statistics
                    cursor.execute("""
                        SELECT 
                            COUNT(*) as total_attempts,
                            COUNT(CASE WHEN success = true THEN 1 END) as successful,
                            COUNT(CASE WHEN success = false THEN 1 END) as failed,
                            COUNT(DISTINCT username) as unique_users
                        FROM auth_events 
                        WHERE event_type IN ('LOGIN_SUCCESS', 'LOGIN_FAILED')
                        AND timestamp >= %s
                    """, (cutoff_date,))
                    
                    overall_row = cursor.fetchone()
                    overall_stats = {
                        'total_attempts': overall_row[0],
                        'successful_logins': overall_row[1],
                        'failed_logins': overall_row[2],
                        'unique_users': overall_row[3],
                        'success_rate': (overall_row[1] / overall_row[0] * 100) if overall_row[0] > 0 else 0
                    }
                    
                    return {
                        'daily_stats': daily_stats,
                        'overall_stats': overall_stats,
                        'period_days': days
                    }
                    
        except Exception as e:
            self.logger.error(f"Failed to get login statistics: {e}")
            return {'daily_stats': [], 'overall_stats': {}, 'period_days': days}
    
    def get_user_growth_stats(self, days: int = 90) -> Dict[str, Any]:
        """Get user growth statistics"""
        try:
            with LoggedOperation(f"Get User Growth Stats ({days} days)", self.logger):
                with self.db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    cutoff_date = datetime.now() - timedelta(days=days)
                    
                    # Daily user registrations
                    cursor.execute("""
                        SELECT 
                            DATE(u.created_at) as registration_date,
                            COUNT(*) as new_users,
                            at.name as account_type
                        FROM users u
                        JOIN account_types at ON u.account_type_id = at.id
                        WHERE u.created_at >= %s
                        GROUP BY DATE(u.created_at), at.name
                        ORDER BY registration_date, at.name
                    """, (cutoff_date,))
                    
                    # Process daily registrations
                    daily_registrations = defaultdict(lambda: defaultdict(int))
                    for row in cursor.fetchall():
                        date_str = row[0].strftime('%Y-%m-%d')
                        daily_registrations[date_str][row[2]] = row[1]
                    
                    # Convert to list format
                    growth_data = []
                    for date, account_types in daily_registrations.items():
                        total = sum(account_types.values())
                        growth_data.append({
                            'date': date,
                            'total_new_users': total,
                            'trial_users': account_types.get('trial', 0),
                            'paid_users': account_types.get('paid', 0)
                        })
                    
                    growth_data.sort(key=lambda x: x['date'])
                    
                    # Overall growth stats
                    cursor.execute("""
                        SELECT 
                            COUNT(*) as total_new_users,
                            COUNT(CASE WHEN at.name = 'trial' THEN 1 END) as trial_users,
                            COUNT(CASE WHEN at.name = 'paid' THEN 1 END) as paid_users
                        FROM users u
                        JOIN account_types at ON u.account_type_id = at.id
                        WHERE u.created_at >= %s
                    """, (cutoff_date,))
                    
                    overall_row = cursor.fetchone()
                    overall_growth = {
                        'total_new_users': overall_row[0],
                        'trial_users': overall_row[1],
                        'paid_users': overall_row[2],
                        'conversion_rate': (overall_row[2] / overall_row[0] * 100) if overall_row[0] > 0 else 0
                    }
                    
                    return {
                        'daily_growth': growth_data,
                        'overall_growth': overall_growth,
                        'period_days': days
                    }
                    
        except Exception as e:
            self.logger.error(f"Failed to get user growth stats: {e}")
            return {'daily_growth': [], 'overall_growth': {}, 'period_days': days}
    
    def get_device_analytics(self) -> Dict[str, Any]:
        """Get device and session analytics"""
        try:
            with LoggedOperation("Get Device Analytics", self.logger):
                with self.db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    # Active devices per user
                    cursor.execute("""
                        SELECT 
                            u.username,
                            COUNT(DISTINCT us.device_fingerprint) as device_count,
                            at.name as account_type,
                            at.max_devices
                        FROM users u
                        JOIN user_sessions us ON u.id = us.user_id
                        JOIN account_types at ON u.account_type_id = at.id
                        WHERE us.is_active = true
                        GROUP BY u.id, u.username, at.name, at.max_devices
                        ORDER BY device_count DESC
                        LIMIT 20
                    """)
                    
                    device_usage = []
                    for row in cursor.fetchall():
                        device_usage.append({
                            'username': row[0],
                            'device_count': row[1],
                            'account_type': row[2],
                            'max_devices': row[3],
                            'usage_percentage': (row[1] / row[3] * 100) if row[3] > 0 else 0
                        })
                    
                    # Session duration analytics
                    cursor.execute("""
                        SELECT 
                            AVG(EXTRACT(EPOCH FROM (last_activity - created_at))/3600) as avg_session_hours,
                            MAX(EXTRACT(EPOCH FROM (last_activity - created_at))/3600) as max_session_hours,
                            COUNT(*) as total_sessions
                        FROM user_sessions
                        WHERE last_activity > created_at
                    """)
                    
                    session_row = cursor.fetchone()
                    session_stats = {
                        'avg_session_hours': float(session_row[0]) if session_row[0] else 0.0,
                        'max_session_hours': float(session_row[1]) if session_row[1] else 0.0,
                        'total_sessions': session_row[2]
                    }
                    
                    # Most active devices
                    cursor.execute("""
                        SELECT 
                            LEFT(device_fingerprint, 8) as device_short,
                            COUNT(*) as session_count,
                            MAX(last_activity) as last_seen
                        FROM user_sessions
                        GROUP BY device_fingerprint
                        ORDER BY session_count DESC
                        LIMIT 10
                    """)
                    
                    active_devices = []
                    for row in cursor.fetchall():
                        active_devices.append({
                            'device_id': row[0] + '...',
                            'session_count': row[1],
                            'last_seen': row[2]
                        })
                    
                    return {
                        'device_usage': device_usage,
                        'session_stats': session_stats,
                        'active_devices': active_devices
                    }
                    
        except Exception as e:
            self.logger.error(f"Failed to get device analytics: {e}")
            return {'device_usage': [], 'session_stats': {}, 'active_devices': []}
    
    def get_security_analytics(self, days: int = 7) -> Dict[str, Any]:
        """Get security-related analytics"""
        try:
            with LoggedOperation(f"Get Security Analytics ({days} days)", self.logger):
                with self.db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    cutoff_date = datetime.now() - timedelta(days=days)
                    
                    # Failed login attempts
                    cursor.execute("""
                        SELECT 
                            username,
                            COUNT(*) as failed_attempts,
                            MAX(timestamp) as last_attempt
                        FROM audit_logs
                        WHERE event_type = 'LOGIN_FAILED'
                        AND timestamp >= %s
                        GROUP BY username
                        ORDER BY failed_attempts DESC
                        LIMIT 10
                    """, (cutoff_date,))
                    
                    failed_logins = []
                    for row in cursor.fetchall():
                        failed_logins.append({
                            'username': row[0],
                            'failed_attempts': row[1],
                            'last_attempt': row[2]
                        })
                    
                    # Security events
                    cursor.execute("""
                        SELECT 
                            event_type,
                            COUNT(*) as event_count
                        FROM audit_logs
                        WHERE event_type LIKE '%SECURITY%' OR event_type LIKE '%FAILED%'
                        AND timestamp >= %s
                        GROUP BY event_type
                        ORDER BY event_count DESC
                    """, (cutoff_date,))
                    
                    security_events = []
                    for row in cursor.fetchall():
                        security_events.append({
                            'event_type': row[0],
                            'count': row[1]
                        })
                    
                    # Account lockouts and suspensions
                    cursor.execute("""
                        SELECT COUNT(*) FROM users WHERE is_active = false
                    """)
                    inactive_accounts = cursor.fetchone()[0]
                    
                    return {
                        'failed_logins': failed_logins,
                        'security_events': security_events,
                        'inactive_accounts': inactive_accounts,
                        'period_days': days
                    }
                    
        except Exception as e:
            self.logger.error(f"Failed to get security analytics: {e}")
            return {'failed_logins': [], 'security_events': [], 'inactive_accounts': 0, 'period_days': days}
    
    def generate_analytics_report(self, report_type: str = "weekly") -> Dict[str, Any]:
        """Generate comprehensive analytics report"""
        try:
            with LoggedOperation(f"Generate Analytics Report: {report_type}", self.logger):
                
                # Determine time period
                days_map = {
                    'daily': 1,
                    'weekly': 7,
                    'monthly': 30,
                    'quarterly': 90
                }
                days = days_map.get(report_type, 7)
                
                # Collect all analytics
                report = {
                    'report_type': report_type,
                    'period_days': days,
                    'generated_at': datetime.now().isoformat(),
                    'login_stats': self.get_login_statistics(days),
                    'user_growth': self.get_user_growth_stats(days),
                    'device_analytics': self.get_device_analytics(),
                    'security_analytics': self.get_security_analytics(days)
                }
                
                # Calculate summary metrics
                login_stats = report['login_stats']['overall_stats']
                growth_stats = report['user_growth']['overall_growth']
                
                report['summary'] = {
                    'total_login_attempts': login_stats.get('total_attempts', 0),
                    'login_success_rate': login_stats.get('success_rate', 0),
                    'new_users': growth_stats.get('total_new_users', 0),
                    'conversion_rate': growth_stats.get('conversion_rate', 0),
                    'security_incidents': len(report['security_analytics']['security_events'])
                }
                
                self.logger.info(f"Analytics report generated: {report_type}")
                return report
                
        except Exception as e:
            self.logger.error(f"Failed to generate analytics report: {e}")
            return {
                'report_type': report_type,
                'generated_at': datetime.now().isoformat(),
                'error': str(e)
            }


# Test function
if __name__ == "__main__":
    from ..database.manager import AuthDatabaseManager
    
    print("📊 Testing AdminAnalytics...")
    
    # Initialize components
    db_manager = AuthDatabaseManager()
    analytics = AdminAnalytics(db_manager)
    
    # Test analytics functions
    print(f"Recent logins (24h): {analytics.get_recent_logins(24)}")
    
    recent_activities = analytics.get_recent_activities(5)
    print(f"Recent activities: {len(recent_activities)} events")
    
    login_stats = analytics.get_login_statistics(7)
    print(f"Login stats (7 days): {login_stats['overall_stats']}")
    
    # Generate report
    report = analytics.generate_analytics_report("weekly")
    print(f"Weekly report generated: {report['summary']}")
    
    print("✅ AdminAnalytics test completed!") 