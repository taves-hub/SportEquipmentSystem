#!/usr/bin/env python3
"""
Database Backup and Restore Utility
Backs up the PostgreSQL database and allows restoration
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime
from config import Config

# Database configuration from config.py
DB_URI = Config.SQLALCHEMY_DATABASE_URI
# Parse PostgreSQL URI: postgresql://postgres:Taves254@localhost/sports_equipment_db
parts = DB_URI.replace('postgresql://', '').split('@')
credentials = parts[0].split(':')
db_user = credentials[0]
db_password = credentials[1]
host_db = parts[1].split('/')
db_host = host_db[0]
db_name = host_db[1]

BACKUP_DIR = Path('database_backups')
BACKUP_DIR.mkdir(exist_ok=True)

# Path to PostgreSQL tools
# Check common installation paths
POSTGRES_BIN_PATHS = [
    Path('C:\\Program Files\\PostgreSQL\\18\\bin'),
    Path('C:\\Program Files\\PostgreSQL\\17\\bin'),
    Path('C:\\Program Files\\PostgreSQL\\16\\bin'),
    Path('C:\\Program Files\\PostgreSQL\\15\\bin'),
    Path('C:\\PostgreSQL\\bin'),
    Path('C:\\Program Files (x86)\\PostgreSQL\\bin'),
]

POSTGRES_BIN = None
for path in POSTGRES_BIN_PATHS:
    if path.exists():
        POSTGRES_BIN = path
        break

if not POSTGRES_BIN:
    print("WARNING: PostgreSQL bin directory not found!")
    print("Please ensure PostgreSQL is installed and paths are correct.")


def backup_database():
    """Create a backup of the PostgreSQL database"""
    if not POSTGRES_BIN:
        print("✗ Error: PostgreSQL bin directory not found!")
        print("  Please ensure PostgreSQL is installed.")
        return False
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = BACKUP_DIR / f'{db_name}_backup_{timestamp}.sql'
    
    try:
        print(f"Creating database backup...")
        print(f"  Database: {db_name}")
        print(f"  Host: {db_host}")
        print(f"  User: {db_user}")
        
        # Use pg_dump to create backup (full path)
        pg_dump_exe = POSTGRES_BIN / 'pg_dump.exe'
        cmd = [
            str(pg_dump_exe),
            '-h', db_host,
            '-U', db_user,
            '-d', db_name,
            '-f', str(backup_file),
            '--verbose'
        ]
        
        # Set password via environment variable
        import os
        env = os.environ.copy()
        env['PGPASSWORD'] = db_password
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            file_size = backup_file.stat().st_size / (1024 * 1024)  # Size in MB
            print(f"\n✓ Database backup successful!")
            print(f"  File: {backup_file}")
            print(f"  Size: {file_size:.2f} MB")
            print(f"  Location: {backup_file.absolute()}")
            return True
        else:
            print(f"✗ Backup failed!")
            print(f"  Error: {result.stderr}")
            return False
            
    except FileNotFoundError as e:
        print(f"✗ Error: {e}")
        print("  Make sure PostgreSQL tools are properly installed")
        return False
    except Exception as e:
        print(f"✗ Backup error: {e}")
        return False


def restore_database(backup_file_path):
    """Restore the database from a backup file"""
    if not POSTGRES_BIN:
        print("✗ Error: PostgreSQL bin directory not found!")
        print("  Please ensure PostgreSQL is installed.")
        return False
    
    backup_file = Path(backup_file_path)
    
    if not backup_file.exists():
        print(f"✗ Backup file not found: {backup_file}")
        return False
    
    try:
        print(f"Restoring database from backup...")
        print(f"  Database: {db_name}")
        print(f"  Backup: {backup_file}")
        print(f"  Size: {backup_file.stat().st_size / (1024 * 1024):.2f} MB")
        
        # Confirm before restoring
        confirm = input("\n⚠️  WARNING: This will overwrite the existing database. Continue? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Restore cancelled.")
            return False
        
        # Use psql to restore (full path)
        psql_exe = POSTGRES_BIN / 'psql.exe'
        cmd = [
            str(psql_exe),
            '-h', db_host,
            '-U', db_user,
            '-d', db_name,
            '-f', str(backup_file)
        ]
        
        # Set password via environment variable
        import os
        env = os.environ.copy()
        env['PGPASSWORD'] = db_password
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"\n✓ Database restore successful!")
            print(f"  Database: {db_name}")
            return True
        else:
            print(f"✗ Restore failed!")
            print(f"  Error: {result.stderr}")
            return False
            
    except FileNotFoundError as e:
        print(f"✗ Error: {e}")
        print("  Make sure PostgreSQL tools are properly installed")
        return False
    except Exception as e:
        print(f"✗ Restore error: {e}")
        return False


def list_backups():
    """List all available backups"""
    backups = list(BACKUP_DIR.glob(f'{db_name}_backup_*.sql'))
    
    if not backups:
        print(f"No backups found in {BACKUP_DIR}")
        return
    
    print(f"\nAvailable Backups ({len(backups)} total):")
    print("-" * 80)
    
    for i, backup in enumerate(sorted(backups, reverse=True), 1):
        size = backup.stat().st_size / (1024 * 1024)
        mod_time = datetime.fromtimestamp(backup.stat().st_mtime)
        print(f"{i:2d}. {backup.name:<50} {size:>8.2f} MB  {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")


def get_database_stats():
    """Get statistics about the database"""
    try:
        print(f"Database Statistics:")
        print(f"  Name: {db_name}")
        print(f"  Host: {db_host}")
        print(f"  User: {db_user}")
        print(f"  Port: 5432 (default)")
        
        # Try to connect and get table count
        import psycopg2
        try:
            conn = psycopg2.connect(
                host=db_host,
                user=db_user,
                password=db_password,
                database=db_name
            )
            cursor = conn.cursor()
            
            # Get table count
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            table_count = cursor.fetchone()[0]
            
            print(f"  Tables: {table_count}")
            
            # Get database size
            cursor.execute(f"SELECT pg_database_size('{db_name}')")
            db_size = cursor.fetchone()[0] / (1024 * 1024)  # Convert to MB
            print(f"  Size: {db_size:.2f} MB")
            
            cursor.close()
            conn.close()
            
        except ImportError:
            print("  Note: psycopg2 not installed. Cannot retrieve detailed stats.")
            print("         Run: pip install psycopg2-binary")
            
    except Exception as e:
        print(f"Could not retrieve database stats: {e}")


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Sports Equipment Management System - Database Utility")
        print("\nUsage:")
        print("  python database_utility.py backup          - Create a database backup")
        print("  python database_utility.py restore <file>  - Restore from backup file")
        print("  python database_utility.py list            - List all backups")
        print("  python database_utility.py stats           - Show database statistics")
        print("\nExample:")
        print("  python database_utility.py backup")
        print("  python database_utility.py restore database_backups/sports_equipment_db_backup_20260213_120000.sql")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == 'backup':
        success = backup_database()
        sys.exit(0 if success else 1)
    
    elif command == 'restore':
        if len(sys.argv) < 3:
            print("Error: Backup file path required")
            print("Usage: python database_utility.py restore <file>")
            sys.exit(1)
        success = restore_database(sys.argv[2])
        sys.exit(0 if success else 1)
    
    elif command == 'list':
        list_backups()
    
    elif command == 'stats':
        get_database_stats()
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == '__main__':
    main()
