#!/usr/bin/env python3
"""
Manually run the direction column migration
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

def run_migration_step_by_step(conn):
    """Run migration commands one by one"""
    try:
        cursor = conn.cursor()
        
        # Step 1: Add the direction column
        print("📝 Step 1: Adding direction column...")
        cursor.execute("""
            ALTER TABLE whatsapp_messages 
            ADD COLUMN direction VARCHAR(20) DEFAULT 'incoming'
        """)
        print("✅ Direction column added")
        
        # Step 2: Add check constraint
        print("📝 Step 2: Adding check constraint...")
        cursor.execute("""
            ALTER TABLE whatsapp_messages 
            ADD CONSTRAINT check_direction CHECK (direction IN ('incoming', 'outgoing'))
        """)
        print("✅ Check constraint added")
        
        # Step 3: Create index
        print("📝 Step 3: Creating index...")
        cursor.execute("""
            CREATE INDEX idx_messages_direction ON whatsapp_messages(direction)
        """)
        print("✅ Index created")
        
        # Step 4: Update existing records
        print("📝 Step 4: Updating existing records...")
        cursor.execute("""
            UPDATE whatsapp_messages 
            SET direction = 'incoming' 
            WHERE direction IS NULL
        """)
        rows_updated = cursor.rowcount
        print(f"✅ Updated {rows_updated} existing records")
        
        # Commit all changes
        conn.commit()
        print("🎉 All migration steps completed successfully!")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration step failed: {e}")
        conn.rollback()
        return False

def verify_migration(conn):
    """Verify the migration was successful"""
    cursor = conn.cursor()
    
    # Check column exists
    cursor.execute("""
        SELECT column_name, data_type, column_default, is_nullable
        FROM information_schema.columns 
        WHERE table_name = 'whatsapp_messages' 
        AND column_name = 'direction'
    """)
    column_info = cursor.fetchone()
    
    if column_info:
        print(f"✅ Direction column verified: {column_info}")
    else:
        print("❌ Direction column not found!")
        return False
    
    # Check constraint exists
    cursor.execute("""
        SELECT constraint_name, check_clause 
        FROM information_schema.check_constraints 
        WHERE constraint_name = 'check_direction'
    """)
    constraint_info = cursor.fetchone()
    
    if constraint_info:
        print(f"✅ Check constraint verified: {constraint_info}")
    else:
        print("❌ Check constraint not found!")
    
    # Check index exists
    cursor.execute("""
        SELECT indexname, indexdef 
        FROM pg_indexes 
        WHERE tablename = 'whatsapp_messages' 
        AND indexname = 'idx_messages_direction'
    """)
    index_info = cursor.fetchone()
    
    if index_info:
        print(f"✅ Index verified: {index_info[0]}")
    else:
        print("❌ Index not found!")
    
    # Check data
    cursor.execute("""
        SELECT direction, COUNT(*) 
        FROM whatsapp_messages 
        GROUP BY direction
    """)
    direction_counts = cursor.fetchall()
    
    if direction_counts:
        print("✅ Direction data:")
        for direction, count in direction_counts:
            print(f"  - {direction}: {count} messages")
    
    return True

def main():
    print("🔧 Running manual migration for direction column...")
    
    conn = connect_to_db()
    if not conn:
        sys.exit(1)
    
    try:
        # Check if column already exists
        cursor = conn.cursor()
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'whatsapp_messages' 
            AND column_name = 'direction'
        """)
        
        if cursor.fetchone():
            print("✅ Direction column already exists!")
        else:
            print("❌ Direction column missing. Running migration...")
            if not run_migration_step_by_step(conn):
                sys.exit(1)
        
        # Verify everything worked
        print("\n🔍 Verifying migration...")
        verify_migration(conn)
        
    finally:
        conn.close()

if __name__ == "__main__":
    main()