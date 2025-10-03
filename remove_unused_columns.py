#!/usr/bin/env python3
"""
Remove context_message_id and webhook_raw_data columns from whatsapp_messages table
These columns are not being used and can be safely removed to simplify the schema
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

def check_columns_exist(conn):
    """Check if the columns exist before attempting to remove them"""
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'whatsapp_messages' 
        AND column_name IN ('context_message_id', 'webhook_raw_data')
    """)
    
    existing_columns = [row[0] for row in cursor.fetchall()]
    return existing_columns

def check_column_usage(conn, column_name):
    """Check if column has any non-null values"""
    cursor = conn.cursor()
    
    cursor.execute(f"""
        SELECT COUNT(*) as total_rows,
               COUNT({column_name}) as non_null_rows
        FROM whatsapp_messages
    """)
    
    total_rows, non_null_rows = cursor.fetchone()
    return total_rows, non_null_rows

def remove_columns_step_by_step(conn, columns_to_remove):
    """Remove columns one by one with safety checks"""
    try:
        cursor = conn.cursor()
        
        for column in columns_to_remove:
            print(f"\n📝 Processing column: {column}")
            
            # Check usage before removal
            total_rows, non_null_rows = check_column_usage(conn, column)
            print(f"  - Total rows: {total_rows}")
            print(f"  - Rows with {column}: {non_null_rows}")
            
            if non_null_rows > 0:
                print(f"  ⚠️  WARNING: {non_null_rows} rows have data in {column}")
                response = input(f"  Continue removing {column}? (y/N): ")
                if response.lower() != 'y':
                    print(f"  ⏭️  Skipping {column}")
                    continue
            
            # Remove the column
            print(f"  🗑️  Removing column {column}...")
            cursor.execute(f"""
                ALTER TABLE whatsapp_messages 
                DROP COLUMN IF EXISTS {column}
            """)
            print(f"  ✅ Column {column} removed successfully")
        
        # Commit all changes
        conn.commit()
        print("\n🎉 All column removals completed successfully!")
        
        return True
        
    except Exception as e:
        print(f"❌ Column removal failed: {e}")
        conn.rollback()
        return False

def verify_removal(conn, original_columns):
    """Verify the columns were successfully removed"""
    cursor = conn.cursor()
    
    print("\n🔍 Verifying column removal...")
    
    # Check remaining columns
    cursor.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns 
        WHERE table_name = 'whatsapp_messages'
        ORDER BY ordinal_position
    """)
    remaining_columns = cursor.fetchall()
    
    print("✅ Remaining columns in whatsapp_messages:")
    for col_name, col_type in remaining_columns:
        print(f"  - {col_name}: {col_type}")
    
    # Verify targeted columns are gone
    removed_columns = []
    for column in original_columns:
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'whatsapp_messages' 
            AND column_name = %s
        """, (column,))
        
        if not cursor.fetchone():
            removed_columns.append(column)
            print(f"✅ Confirmed: {column} successfully removed")
        else:
            print(f"❌ ERROR: {column} still exists!")
    
    return len(removed_columns) == len(original_columns)

def show_table_info(conn):
    """Display current table structure and sample data"""
    cursor = conn.cursor()
    
    print("\n📊 Current table structure:")
    cursor.execute("""
        SELECT 
            column_name, 
            data_type, 
            is_nullable, 
            column_default
        FROM information_schema.columns 
        WHERE table_name = 'whatsapp_messages'
        ORDER BY ordinal_position
    """)
    
    columns = cursor.fetchall()
    print("   Column Name          | Data Type            | Nullable | Default")
    print("   --------------------|----------------------|----------|--------")
    for col_name, data_type, nullable, default in columns:
        default_str = str(default)[:20] if default else "None"
        print(f"   {col_name:<20} | {data_type:<20} | {nullable:<8} | {default_str}")
    
    # Show row count
    cursor.execute("SELECT COUNT(*) FROM whatsapp_messages")
    row_count = cursor.fetchone()[0]
    print(f"\n📈 Total messages in table: {row_count}")

def main():
    print("🗑️  Removing unused columns from whatsapp_messages table...")
    print("Columns to remove: context_message_id, webhook_raw_data")
    print("=" * 60)
    
    conn = connect_to_db()
    if not conn:
        sys.exit(1)
    
    try:
        # Show current table info
        show_table_info(conn)
        
        # Check which columns exist
        existing_columns = check_columns_exist(conn)
        
        if not existing_columns:
            print("\n✅ Target columns don't exist. Nothing to remove!")
            return
        
        print(f"\n📋 Found columns to remove: {existing_columns}")
        
        # Ask for confirmation
        print(f"\n⚠️  This will permanently remove {len(existing_columns)} columns from the database.")
        response = input("Continue? (y/N): ")
        
        if response.lower() != 'y':
            print("❌ Operation cancelled by user")
            return
        
        # Remove columns
        if remove_columns_step_by_step(conn, existing_columns):
            # Verify removal
            if verify_removal(conn, existing_columns):
                print("\n🎉 Column removal completed successfully!")
                
                # Show updated table structure
                print("\n" + "="*60)
                show_table_info(conn)
            else:
                print("\n❌ Column removal verification failed!")
                sys.exit(1)
        else:
            print("\n❌ Column removal failed!")
            sys.exit(1)
        
    finally:
        conn.close()

if __name__ == "__main__":
    main()