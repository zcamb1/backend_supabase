#!/usr/bin/env python3
"""
Database Factory Pattern
Cho phép chuyển đổi dễ dàng giữa Render PostgreSQL và Supabase
"""
import os
from typing import Optional, Union
from .manager import AuthDatabaseManager
from .supabase_manager import SupabaseDatabaseManager

class DatabaseFactory:
    """Factory để tạo database manager dựa trên configuration"""
    
    @staticmethod
    def create_database_manager(
        database_type: str = None,
        **kwargs
    ) -> Union[AuthDatabaseManager, SupabaseDatabaseManager]:
        """
        Tạo database manager dựa trên type
        
        Args:
            database_type: 'render' | 'supabase' | None (auto-detect)
            **kwargs: Additional parameters for specific database type
        """
        
        # Auto-detect database type từ environment
        if not database_type:
            database_type = os.environ.get('DATABASE_TYPE', 'render')
        
        database_type = database_type.lower()
        
        if database_type == 'supabase':
            return DatabaseFactory._create_supabase_manager(**kwargs)
        elif database_type == 'render':
            return DatabaseFactory._create_render_manager(**kwargs)
        else:
            raise ValueError(f"Unsupported database type: {database_type}")
    
    @staticmethod
    def _create_supabase_manager(**kwargs) -> SupabaseDatabaseManager:
        """Tạo Supabase database manager"""
        supabase_url = kwargs.get('supabase_url') or os.environ.get('SUPABASE_URL')
        supabase_key = kwargs.get('supabase_key') or os.environ.get('SUPABASE_ANON_KEY')
        
        if not supabase_url or not supabase_key:
            raise ValueError("Supabase URL và Key phải được cung cấp")
        
        return SupabaseDatabaseManager(
            supabase_url=supabase_url,
            supabase_key=supabase_key
        )
    
    @staticmethod
    def _create_render_manager(**kwargs) -> AuthDatabaseManager:
        """Tạo Render PostgreSQL database manager"""
        
        # Lấy credentials từ kwargs hoặc environment hoặc defaults
        host = kwargs.get('host') or os.environ.get('DB_HOST', 'dpg-d21hsaidbo4c73e6ghe0-a')
        port = kwargs.get('port') or int(os.environ.get('DB_PORT', '5432'))
        database = kwargs.get('database') or os.environ.get('DB_NAME', 'elevenlabs_auth_db_l1le')
        username = kwargs.get('username') or os.environ.get('DB_USER', 'elevenlabs_auth_db_user')
        password = kwargs.get('password') or os.environ.get('DB_PASSWORD', 'Dta5busSXW4WPPaasBVvjtyTXT2fXU9t')
        
        return AuthDatabaseManager(
            host=host,
            port=port,
            database=database,
            username=username,
            password=password
        )
    
    @staticmethod
    def create_from_database_url(database_url: str):
        """Tạo database manager từ database URL"""
        if database_url.startswith('postgresql://'):
            # Parse PostgreSQL URL
            import urllib.parse
            parsed = urllib.parse.urlparse(database_url)
            
            return AuthDatabaseManager(
                host=parsed.hostname,
                port=parsed.port or 5432,
                database=parsed.path.lstrip('/'),
                username=parsed.username,
                password=parsed.password
            )
        else:
            raise ValueError(f"Unsupported database URL format: {database_url}")

# Convenience functions
def get_database_manager(
    database_type: str = None,
    **kwargs
) -> Union[AuthDatabaseManager, SupabaseDatabaseManager]:
    """Convenience function để lấy database manager"""
    return DatabaseFactory.create_database_manager(database_type, **kwargs)

def get_supabase_manager(**kwargs) -> SupabaseDatabaseManager:
    """Convenience function để lấy Supabase manager"""
    return DatabaseFactory.create_database_manager('supabase', **kwargs)

def get_render_manager(**kwargs) -> AuthDatabaseManager:
    """Convenience function để lấy Render manager"""
    return DatabaseFactory.create_database_manager('render', **kwargs)
