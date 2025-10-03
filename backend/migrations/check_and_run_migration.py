#!/usr/bin/env python3
"""
Script to check if migration is needed and run it
"""

import psycopg2
import boto3
import sys

# Database connection parameters
DB_HOST = "whatsapp-postgres-development.cyd40iccy9uu.us-east-1.rds.amazonaws.com"
DB_PORT = 5432
DB_NAME = "whatsapp_business_development"
DB_USER = "app_user"

def connect_to_db():
    """Connect to the database using IAM authentication"""
    try:
        # Generate IAM auth token
        rds_client = boto3.client('rds', region_name='us-east-1')
        token = rds_client.generate_db_auth_token(
            DBHostname=DB_HOST,
            Port=DB_PORT,
            DBUsername=DB_USER,
            Region='us-east-1'
        )
        
        # Connect with the token
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=token,
            sslmode='require'
        )
        return conn
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return None

def check_direction_column(conn):
    """Check if direction column exists"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'whatsapp_messages' 
        AND column_name = 'direction'
    """)
    result = cursor.fetchone()
    return result is not None

def run_migration(conn):
    """Run the migration SQL"""
    try:
        cursor = conn.cursor()
        
        # Read the migration file
        with open('/Users/abskchsk/Documents/govindjis/wa-app/backend/migrations/add_direction_column.sql', 'r') as f:
            migration_sql = f.read()
        
        # Split into individual statements and execute
        statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip() and not stmt.strip().startswith('--')]
        
        for stmt in statements:
            if stmt and not stmt.startswith('SELECT') and not stmt.startswith('COMMENT'):
                print(f"📝 Executing: {stmt[:50]}...")
                cursor.execute(stmt)
        
        conn.commit()
        print("✅ Migration executed successfully!")
        
        # Verify the column was added
        cursor.execute("""
            SELECT column_name, data_type, column_default, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'whatsapp_messages' 
            AND column_name = 'direction'
        """)
        result = cursor.fetchone()
        
        if result:
            print(f"✅ Direction column created: {result}")
        
        # Check if index was created
        cursor.execute("""
            SELECT indexname, indexdef 
            FROM pg_indexes 
            WHERE tablename = 'whatsapp_messages' 
            AND indexname = 'idx_messages_direction'
        """)
        index_result = cursor.fetchone()
        
        if index_result:
            print(f"✅ Index created: {index_result[0]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
        return False

def main():
    print("🔍 Checking direction column migration...")
    
    conn = connect_to_db()
    if not conn:
        sys.exit(1)
    
    try:
        # Check if migration is needed
        if check_direction_column(conn):
            print("✅ Direction column already exists!")
        else:
            print("❌ Direction column missing. Running migration...")
            if run_migration(conn):
                print("🎉 Migration completed successfully!")
            else:
                print("❌ Migration failed!")
                sys.exit(1)
        
        # Show current table structure
        cursor = conn.cursor()
        cursor.execute("""
            SELECT column_name, data_type, column_default
            FROM information_schema.columns 
            WHERE table_name = 'whatsapp_messages'
            ORDER BY ordinal_position
        """)
        columns = cursor.fetchall()
        
        print("\n📋 Current whatsapp_messages table structure:")
        for col_name, col_type, col_default in columns:
            print(f"  - {col_name}: {col_type} (default: {col_default})")
        
    finally:
        conn.close()

if __name__ == "__main__":
    main()