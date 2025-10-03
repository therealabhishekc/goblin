#!/usr/bin/env python3
"""
Update status values migration script
Updates the status column to support new values and adds proper constraints
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

def analyze_current_status_values(conn):
    """Analyze current status values in the database"""
    cursor = conn.cursor()
    
    print("🔍 Analyzing current status values...")
    
    # Get current status distribution
    cursor.execute("""
        SELECT 
            status,
            COUNT(*) as count,
            direction
        FROM whatsapp_messages
        GROUP BY status, direction
        ORDER BY status, direction
    """)
    
    status_counts = cursor.fetchall()
    
    print("📊 Current status distribution:")
    if status_counts:
        for status, count, direction in status_counts:
            print(f"  - {status} ({direction}): {count} messages")
    else:
        print("  - No messages found")
    
    # Check current constraints
    cursor.execute("""
        SELECT 
            conname as constraint_name,
            pg_get_constraintdef(oid) as definition
        FROM pg_constraint 
        WHERE conrelid = 'whatsapp_messages'::regclass 
        AND conname LIKE '%status%'
    """)
    
    constraints = cursor.fetchall()
    
    print("\n📋 Current status constraints:")
    if constraints:
        for name, definition in constraints:
            print(f"  - {name}: {definition}")
    else:
        print("  - No status constraints found")
    
    # Check default value
    cursor.execute("""
        SELECT column_default
        FROM information_schema.columns 
        WHERE table_name = 'whatsapp_messages' 
        AND column_name = 'status'
    """)
    
    default = cursor.fetchone()
    default_value = default[0] if default else "None"
    print(f"\n🔧 Current default value: {default_value}")
    
    return status_counts

def update_existing_status_values(conn):
    """Update existing status values"""
    try:
        cursor = conn.cursor()
        
        print("\n📝 Step 1: Updating existing status values...")
        
        # Convert 'received' and NULL to 'processing'
        cursor.execute("""
            UPDATE whatsapp_messages 
            SET status = 'processing' 
            WHERE status = 'received' OR status IS NULL
        """)
        
        updated_rows = cursor.rowcount
        print(f"✅ Updated {updated_rows} messages from 'received'/NULL to 'processing'")
        
        return True, updated_rows
        
    except Exception as e:
        print(f"❌ Failed to update status values: {e}")
        return False, 0

def drop_existing_constraints(conn):
    """Drop existing status constraints"""
    try:
        cursor = conn.cursor()
        
        print("\n📝 Step 2: Dropping existing status constraints...")
        
        # Drop existing check constraint if it exists
        cursor.execute("""
            ALTER TABLE whatsapp_messages 
            DROP CONSTRAINT IF EXISTS whatsapp_messages_status_check
        """)
        
        print("✅ Dropped existing status check constraint (if any)")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to drop constraints: {e}")
        return False

def add_new_status_constraint(conn):
    """Add new status constraint with updated values"""
    try:
        cursor = conn.cursor()
        
        print("\n📝 Step 3: Adding new status constraint...")
        
        # Add new check constraint with updated values
        cursor.execute("""
            ALTER TABLE whatsapp_messages 
            ADD CONSTRAINT whatsapp_messages_status_check 
            CHECK (status IN ('processing', 'processed', 'failed', 'sent', 'delivered', 'read'))
        """)
        
        print("✅ Added new status constraint with values: processing, processed, failed, sent, delivered, read")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to add new constraint: {e}")
        return False

def update_default_status(conn):
    """Update default status value"""
    try:
        cursor = conn.cursor()
        
        print("\n📝 Step 4: Updating default status value...")
        
        # Update default value for status column
        cursor.execute("""
            ALTER TABLE whatsapp_messages 
            ALTER COLUMN status SET DEFAULT 'processing'
        """)
        
        print("✅ Updated default status to 'processing'")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to update default status: {e}")
        return False

def add_column_comment(conn):
    """Add explanatory comment to status column"""
    try:
        cursor = conn.cursor()
        
        print("\n📝 Step 5: Adding column comment...")
        
        # Add comment explaining the status values
        cursor.execute("""
            COMMENT ON COLUMN whatsapp_messages.status IS 
            'Message status: processing (being processed), processed (completed successfully), failed (processing failed), sent (outgoing message sent), delivered (message delivered to customer), read (message read by recipient)'
        """)
        
        print("✅ Added explanatory comment to status column")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to add column comment: {e}")
        return False

def verify_migration(conn):
    """Verify the migration was successful"""
    cursor = conn.cursor()
    
    print("\n🔍 Verifying migration...")
    
    # Check updated status distribution
    cursor.execute("""
        SELECT 
            status,
            COUNT(*) as count,
            direction
        FROM whatsapp_messages
        GROUP BY status, direction
        ORDER BY status, direction
    """)
    
    status_counts = cursor.fetchall()
    
    print("📊 Updated status distribution:")
    for status, count, direction in status_counts:
        print(f"  - {status} ({direction}): {count} messages")
    
    # Verify constraint
    cursor.execute("""
        SELECT 
            conname as constraint_name,
            pg_get_constraintdef(oid) as definition
        FROM pg_constraint 
        WHERE conrelid = 'whatsapp_messages'::regclass 
        AND conname = 'whatsapp_messages_status_check'
    """)
    
    constraint = cursor.fetchone()
    
    if constraint:
        print(f"\n✅ Status constraint verified: {constraint[0]}")
        print(f"   Definition: {constraint[1]}")
    else:
        print("\n❌ Status constraint not found!")
        return False
    
    # Check default value
    cursor.execute("""
        SELECT column_default
        FROM information_schema.columns 
        WHERE table_name = 'whatsapp_messages' 
        AND column_name = 'status'
    """)
    
    default = cursor.fetchone()
    default_value = default[0] if default else "None"
    print(f"\n✅ Default status value: {default_value}")
    
    return True

def run_migration_steps(conn):
    """Run all migration steps in sequence"""
    try:
        # Step 1: Update existing status values
        success, updated_count = update_existing_status_values(conn)
        if not success:
            return False
        
        # Step 2: Drop existing constraints
        if not drop_existing_constraints(conn):
            return False
        
        # Step 3: Add new constraint
        if not add_new_status_constraint(conn):
            return False
        
        # Step 4: Update default value
        if not update_default_status(conn):
            return False
        
        # Step 5: Add column comment
        if not add_column_comment(conn):
            return False
        
        # Commit all changes
        conn.commit()
        print("\n🎉 All migration steps completed successfully!")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
        return False

def main():
    print("🔧 Running Status Values Migration")
    print("=" * 50)
    print("Purpose: Update status column to support new values")
    print("New values: processing, processed, failed, sent, delivered, read")
    print("=" * 50)
    
    conn = connect_to_db()
    if not conn:
        sys.exit(1)
    
    try:
        # Analyze current state
        current_status = analyze_current_status_values(conn)
        
        # Ask for confirmation
        print(f"\n⚠️  This migration will:")
        print("  1. Update 'received'/NULL status values to 'processing'")
        print("  2. Drop existing status constraints")
        print("  3. Add new constraint with updated status values")
        print("  4. Set default status to 'processing'")
        print("  5. Add explanatory comment to status column")
        
        response = input("\nContinue with migration? (y/N): ")
        
        if response.lower() != 'y':
            print("❌ Migration cancelled by user")
            return
        
        # Run migration
        if run_migration_steps(conn):
            # Verify results
            if verify_migration(conn):
                print(f"\n✅ Status values migration completed successfully!")
                print("All messages now use the updated status values.")
            else:
                print(f"\n❌ Migration verification failed!")
                sys.exit(1)
        else:
            print(f"\n❌ Migration failed!")
            sys.exit(1)
        
    finally:
        conn.close()

if __name__ == "__main__":
    main()