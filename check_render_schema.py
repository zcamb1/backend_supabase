#!/usr/bin/env python3
"""
Kiểm tra schema Render hiện tại để so sánh với Supabase
"""
import psycopg2
import psycopg2.extras

def check_render_schema():
    """Kiểm tra schema Render"""
    print("🔍 Checking Render Database Schema...")
    print("=" * 50)
    
    # Render connection details
    render_config = {
        'host': 'dpg-d21hsaidbo4c73e6ghe0-a.singapore-postgres.render.com',
        'port': 5432,
        'database': 'elevenlabs_auth_db_l1le',
        'user': 'elevenlabs_auth_db_user',
        'password': 'Dta5busSXW4WPPaasBVvjtyTXT2fXU9t'
    }
    
    try:
        # Connect to Render
        conn = psycopg2.connect(**render_config)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Check users table schema
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            AND table_schema = 'public'
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        print("📋 Render users table schema:")
        for col in columns:
            nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
            default = f"DEFAULT {col['column_default']}" if col['column_default'] else ""
            print(f"   - {col['column_name']}: {col['data_type']} {nullable} {default}")
        
        # Check data counts
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        print(f"\n📊 Render data counts:")
        print(f"   - Users: {user_count}")
        
        cursor.execute("SELECT COUNT(*) FROM user_sessions")
        session_count = cursor.fetchone()[0]
        print(f"   - User Sessions: {session_count}")
        
        cursor.execute("SELECT COUNT(*) FROM auth_events")
        event_count = cursor.fetchone()[0]
        print(f"   - Auth Events: {event_count}")
        
        cursor.close()
        conn.close()
        
        print("\n✅ Render schema check completed")
        return True
        
    except Exception as e:
        print(f"❌ Error checking Render schema: {e}")
        return False

def main():
    """Main function"""
    print("🔍 Render vs Supabase Schema Comparison")
    print("=" * 60)
    
    if check_render_schema():
        print("\n📋 NEXT STEPS:")
        print("1. So sánh schema Render với Supabase")
        print("2. Nếu khác nhau → Cần fix Supabase để giống Render")
        print("3. Nếu giống nhau → Có thể deploy an toàn")
    else:
        print("\n❌ Không thể kết nối Render để kiểm tra")

if __name__ == "__main__":
    main()
