#!/usr/bin/env python3
"""
System Monitoring cho ElevenLabs Authentication System
System health monitoring và performance metrics cho admin dashboard
"""

import psutil
import socket
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import json
import threading
import time

from ..database.manager import AuthDatabaseManager
from ..utils.logger import get_logger, log_security_event, LoggedOperation

class SystemMonitor:
    """
    System monitoring utilities cho admin dashboard
    """
    
    def __init__(self, db_manager: AuthDatabaseManager):
        self.db_manager = db_manager
        self.logger = get_logger("system_monitor")
        self._monitoring_active = False
        self._monitor_thread = None
        
    def get_system_health(self) -> Dict[str, bool]:
        """Get overall system health status"""
        try:
            with LoggedOperation("Get System Health", self.logger):
                health = {
                    'database': self._check_database_health(),
                    'auth_api': self._check_auth_api_health(),
                    'logging': self._check_logging_health(),
                    'disk_space': self._check_disk_space(),
                    'memory': self._check_memory_usage()
                }
                
                overall_health = all(health.values())
                
                if not overall_health:
                    # Log health issues
                    failed_components = [k for k, v in health.items() if not v]
                    log_security_event(
                        "SYSTEM_HEALTH_DEGRADED", 
                        "MEDIUM", 
                        f"System components failing: {', '.join(failed_components)}"
                    )
                
                return health
                
        except Exception as e:
            self.logger.error(f"Failed to get system health: {e}")
            return {
                'database': False,
                'auth_api': False, 
                'logging': False,
                'disk_space': False,
                'memory': False
            }
    
    def _check_database_health(self) -> bool:
        """Check database connectivity and performance"""
        try:
            start_time = time.time()
            
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
            
            query_time = time.time() - start_time
            
            # Consider database healthy if query completes in under 1 second
            is_healthy = query_time < 1.0
            
            if not is_healthy:
                self.logger.warning(f"Database query slow: {query_time:.2f}s")
            
            return is_healthy
            
        except Exception as e:
            self.logger.error(f"Database health check failed: {e}")
            return False
    
    def _check_auth_api_health(self) -> bool:
        """Check authentication API health"""
        try:
            # Try to connect to auth API health endpoint
            response = requests.get(
                "https://backend-elevenlab.onrender.com/health", 
                timeout=5
            )
            
            is_healthy = response.status_code == 200
            
            if not is_healthy:
                self.logger.warning(f"Auth API health check failed: {response.status_code}")
            
            return is_healthy
            
        except Exception as e:
            self.logger.warning(f"Auth API health check failed: {e}")
            return False
    
    def _check_logging_health(self) -> bool:
        """Check logging system health"""
        try:
            # Simple logging test without filesystem checks
            test_logger = get_logger("health_check")
            test_logger.info("Health check test log")
            return True
                
        except Exception as e:
            self.logger.error(f"Logging health check failed: {e}")
            return False
    
    def _check_disk_space(self) -> bool:
        """Check available disk space"""
        try:
            # Check disk usage for current directory
            disk_usage = psutil.disk_usage('.')
            
            # Consider healthy if more than 10% disk space available
            free_percentage = (disk_usage.free / disk_usage.total) * 100
            is_healthy = free_percentage > 10.0
            
            if not is_healthy:
                self.logger.warning(f"Low disk space: {free_percentage:.1f}% free")
            
            return is_healthy
            
        except Exception as e:
            self.logger.error(f"Disk space check failed: {e}")
            return False
    
    def _check_memory_usage(self) -> bool:
        """Check system memory usage"""
        try:
            # Check system memory
            memory = psutil.virtual_memory()
            
            # Consider healthy if less than 90% memory used
            is_healthy = memory.percent < 90.0
            
            if not is_healthy:
                self.logger.warning(f"High memory usage: {memory.percent:.1f}%")
            
            return is_healthy
            
        except Exception as e:
            self.logger.error(f"Memory check failed: {e}")
            return False
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get detailed system performance metrics"""
        try:
            with LoggedOperation("Get System Metrics", self.logger):
                
                # CPU metrics
                cpu_percent = psutil.cpu_percent(interval=1)
                cpu_count = psutil.cpu_count()
                load_avg = psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0]
                
                # Memory metrics
                memory = psutil.virtual_memory()
                swap = psutil.swap_memory()
                
                # Disk metrics
                disk_usage = psutil.disk_usage('.')
                
                # Network metrics
                network_io = psutil.net_io_counters()
                
                # System uptime
                boot_time = psutil.boot_time()
                uptime_seconds = time.time() - boot_time
                
                return {
                    'cpu': {
                        'usage_percent': cpu_percent,
                        'core_count': cpu_count,
                        'load_average': list(load_avg)
                    },
                    'memory': {
                        'total_gb': round(memory.total / (1024**3), 2),
                        'used_gb': round(memory.used / (1024**3), 2),
                        'free_gb': round(memory.free / (1024**3), 2),
                        'usage_percent': memory.percent
                    },
                    'swap': {
                        'total_gb': round(swap.total / (1024**3), 2),
                        'used_gb': round(swap.used / (1024**3), 2),
                        'usage_percent': swap.percent
                    },
                    'disk': {
                        'total_gb': round(disk_usage.total / (1024**3), 2),
                        'used_gb': round(disk_usage.used / (1024**3), 2),
                        'free_gb': round(disk_usage.free / (1024**3), 2),
                        'usage_percent': round((disk_usage.used / disk_usage.total) * 100, 1)
                    },
                    'network': {
                        'bytes_sent': network_io.bytes_sent,
                        'bytes_received': network_io.bytes_recv,
                        'packets_sent': network_io.packets_sent,
                        'packets_received': network_io.packets_recv
                    },
                    'uptime': {
                        'seconds': uptime_seconds,
                        'hours': round(uptime_seconds / 3600, 1),
                        'days': round(uptime_seconds / 86400, 1)
                    },
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get system metrics: {e}")
            return {}
    
    def get_database_metrics(self) -> Dict[str, Any]:
        """Get database performance metrics"""
        try:
            with LoggedOperation("Get Database Metrics", self.logger):
                with self.db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    metrics = {}
                    
                    # Connection count
                    try:
                        cursor.execute("""
                            SELECT count(*) FROM pg_stat_activity 
                            WHERE state = 'active'
                        """)
                        metrics['active_connections'] = cursor.fetchone()[0]
                    except:
                        metrics['active_connections'] = 0
                    
                    # Database size
                    try:
                        cursor.execute("SELECT pg_database_size(current_database())")
                        db_size_bytes = cursor.fetchone()[0]
                        metrics['database_size_mb'] = round(db_size_bytes / (1024*1024), 2)
                    except:
                        metrics['database_size_mb'] = 0
                    
                    # Table sizes
                    try:
                        cursor.execute("""
                            SELECT 
                                schemaname,
                                tablename,
                                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
                            FROM pg_tables 
                            WHERE schemaname = 'public'
                            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                            LIMIT 10
                        """)
                        
                        table_sizes = []
                        for row in cursor.fetchall():
                            table_sizes.append({
                                'schema': row[0],
                                'table': row[1],
                                'size': row[2]
                            })
                        metrics['table_sizes'] = table_sizes
                    except:
                        metrics['table_sizes'] = []
                    
                    # Recent performance stats
                    try:
                        cursor.execute("""
                            SELECT 
                                avg(query_time) as avg_query_time,
                                max(query_time) as max_query_time,
                                count(*) as query_count
                            FROM (
                                SELECT extract(epoch from now() - query_start) as query_time
                                FROM pg_stat_activity 
                                WHERE state = 'active' AND query_start IS NOT NULL
                            ) subq
                        """)
                        
                        perf_row = cursor.fetchone()
                        if perf_row:
                            metrics['performance'] = {
                                'avg_query_time_seconds': float(perf_row[0]) if perf_row[0] else 0.0,
                                'max_query_time_seconds': float(perf_row[1]) if perf_row[1] else 0.0,
                                'active_query_count': perf_row[2]
                            }
                    except:
                        metrics['performance'] = {
                            'avg_query_time_seconds': 0.0,
                            'max_query_time_seconds': 0.0,
                            'active_query_count': 0
                        }
                    
                    return metrics
                    
        except Exception as e:
            self.logger.error(f"Failed to get database metrics: {e}")
            return {}
    
    def get_application_metrics(self) -> Dict[str, Any]:
        """Get application-specific metrics"""
        try:
            with LoggedOperation("Get Application Metrics", self.logger):
                with self.db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    metrics = {}
                    
                    # Active sessions in last hour
                    cursor.execute("""
                        SELECT COUNT(*) FROM user_sessions 
                        WHERE last_activity > NOW() - INTERVAL '1 hour'
                    """)
                    metrics['active_sessions_1h'] = cursor.fetchone()[0]
                    
                    # Logins in last hour
                    cursor.execute("""
                        SELECT COUNT(*) FROM audit_logs 
                        WHERE event_type = 'LOGIN_SUCCESS' 
                        AND timestamp > NOW() - INTERVAL '1 hour'
                    """)
                    metrics['logins_1h'] = cursor.fetchone()[0]
                    
                    # Failed logins in last hour
                    cursor.execute("""
                        SELECT COUNT(*) FROM audit_logs 
                        WHERE event_type = 'LOGIN_FAILED' 
                        AND timestamp > NOW() - INTERVAL '1 hour'
                    """)
                    metrics['failed_logins_1h'] = cursor.fetchone()[0]
                    
                    # Security events in last hour
                    cursor.execute("""
                        SELECT COUNT(*) FROM audit_logs 
                        WHERE (event_type LIKE '%SECURITY%' OR event_type LIKE '%FAILED%')
                        AND timestamp > NOW() - INTERVAL '1 hour'
                    """)
                    metrics['security_events_1h'] = cursor.fetchone()[0]
                    
                    # Calculate metrics
                    total_auth_attempts = metrics['logins_1h'] + metrics['failed_logins_1h']
                    metrics['login_success_rate_1h'] = (
                        (metrics['logins_1h'] / total_auth_attempts * 100) 
                        if total_auth_attempts > 0 else 100.0
                    )
                    
                    # Average session duration
                    cursor.execute("""
                        SELECT AVG(EXTRACT(EPOCH FROM (last_activity - created_at))/3600) 
                        FROM user_sessions 
                        WHERE last_activity > created_at 
                        AND created_at > NOW() - INTERVAL '24 hours'
                    """)
                    avg_session_hours = cursor.fetchone()[0]
                    metrics['avg_session_duration_hours'] = float(avg_session_hours) if avg_session_hours else 0.0
                    
                    return metrics
                    
        except Exception as e:
            self.logger.error(f"Failed to get application metrics: {e}")
            return {}
    
    def start_monitoring(self, interval_seconds: int = 60):
        """Start continuous system monitoring"""
        if self._monitoring_active:
            self.logger.warning("Monitoring already active")
            return
        
        self._monitoring_active = True
        self._monitor_thread = threading.Thread(target=self._monitoring_loop, args=(interval_seconds,))
        self._monitor_thread.daemon = True
        self._monitor_thread.start()
        
        self.logger.info(f"System monitoring started (interval: {interval_seconds}s)")
    
    def stop_monitoring(self):
        """Stop continuous monitoring"""
        self._monitoring_active = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        
        self.logger.info("System monitoring stopped")
    
    def _monitoring_loop(self, interval_seconds: int):
        """Continuous monitoring loop"""
        while self._monitoring_active:
            try:
                # Get current metrics
                health = self.get_system_health()
                system_metrics = self.get_system_metrics()
                app_metrics = self.get_application_metrics()
                
                # Check for critical issues
                self._check_critical_thresholds(system_metrics, app_metrics)
                
                # Log overall health status
                if not all(health.values()):
                    failed_components = [k for k, v in health.items() if not v]
                    self.logger.warning(f"System health check failed: {failed_components}")
                
                # Store metrics in database for historical analysis
                self._store_metrics_history(system_metrics, app_metrics)
                
            except Exception as e:
                self.logger.error(f"Monitoring loop error: {e}")
            
            # Wait for next interval
            time.sleep(interval_seconds)
    
    def _check_critical_thresholds(self, system_metrics: Dict, app_metrics: Dict):
        """Check for critical system thresholds"""
        try:
            # Check CPU usage
            cpu_usage = system_metrics.get('cpu', {}).get('usage_percent', 0)
            if cpu_usage > 90:
                log_security_event(
                    "SYSTEM_HIGH_CPU", 
                    "HIGH", 
                    f"CPU usage critical: {cpu_usage:.1f}%"
                )
            
            # Check memory usage
            memory_usage = system_metrics.get('memory', {}).get('usage_percent', 0)
            if memory_usage > 90:
                log_security_event(
                    "SYSTEM_HIGH_MEMORY", 
                    "HIGH", 
                    f"Memory usage critical: {memory_usage:.1f}%"
                )
            
            # Check disk usage
            disk_usage = system_metrics.get('disk', {}).get('usage_percent', 0)
            if disk_usage > 90:
                log_security_event(
                    "SYSTEM_HIGH_DISK", 
                    "HIGH", 
                    f"Disk usage critical: {disk_usage:.1f}%"
                )
            
            # Check failed login rate
            failed_logins = app_metrics.get('failed_logins_1h', 0)
            if failed_logins > 50:  # More than 50 failed logins per hour
                log_security_event(
                    "HIGH_FAILED_LOGIN_RATE", 
                    "HIGH", 
                    f"High failed login rate: {failed_logins} in last hour"
                )
            
        except Exception as e:
            self.logger.error(f"Critical threshold check failed: {e}")
    
    def _store_metrics_history(self, system_metrics: Dict, app_metrics: Dict):
        """Store metrics in database for historical analysis"""
        try:
            # Only store every 5 minutes to avoid too much data
            if hasattr(self, '_last_storage_time'):
                if time.time() - self._last_storage_time < 300:  # 5 minutes
                    return
            
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # Create metrics history table if not exists
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS system_metrics_history (
                        id SERIAL PRIMARY KEY,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        cpu_usage DECIMAL(5,2),
                        memory_usage DECIMAL(5,2),
                        disk_usage DECIMAL(5,2),
                        active_sessions INTEGER,
                        logins_1h INTEGER,
                        failed_logins_1h INTEGER,
                        metrics_data JSONB
                    )
                """)
                
                # Insert current metrics
                cursor.execute("""
                    INSERT INTO system_metrics_history 
                    (cpu_usage, memory_usage, disk_usage, active_sessions, logins_1h, failed_logins_1h, metrics_data)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    system_metrics.get('cpu', {}).get('usage_percent', 0),
                    system_metrics.get('memory', {}).get('usage_percent', 0),
                    system_metrics.get('disk', {}).get('usage_percent', 0),
                    app_metrics.get('active_sessions_1h', 0),
                    app_metrics.get('logins_1h', 0),
                    app_metrics.get('failed_logins_1h', 0),
                    json.dumps({'system': system_metrics, 'application': app_metrics})
                ))
                
                conn.commit()
                self._last_storage_time = time.time()
                
        except Exception as e:
            self.logger.error(f"Failed to store metrics history: {e}")


# Test function
if __name__ == "__main__":
    from ..database.manager import AuthDatabaseManager
    
    print("📡 Testing SystemMonitor...")
    
    # Initialize components
    db_manager = AuthDatabaseManager()
    monitor = SystemMonitor(db_manager)
    
    # Test health checks
    health = monitor.get_system_health()
    print(f"System health: {health}")
    
    # Test system metrics
    metrics = monitor.get_system_metrics()
    print(f"CPU usage: {metrics.get('cpu', {}).get('usage_percent', 0):.1f}%")
    print(f"Memory usage: {metrics.get('memory', {}).get('usage_percent', 0):.1f}%")
    
    # Test database metrics
    db_metrics = monitor.get_database_metrics()
    print(f"Database size: {db_metrics.get('database_size_mb', 0)}MB")
    
    # Test application metrics
    app_metrics = monitor.get_application_metrics()
    print(f"Active sessions (1h): {app_metrics.get('active_sessions_1h', 0)}")
    
    print("✅ SystemMonitor test completed!") 