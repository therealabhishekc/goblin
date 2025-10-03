#!/usr/bin/env python3
"""
Prepopulate to_phone column with "business" for all existing messages
This represents messages sent TO the business (incoming direction)
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

def analyze_current_state(conn):
    """Analyze current state of to_phone column"""
    cursor = conn.cursor()
    
    print("🔍 Analyzing current to_phone column state...")
    
    # Check total messages and to_phone values
    cursor.execute("""
        SELECT 
            COUNT(*) as total_messages,
            COUNT(to_phone) as messages_with_to_phone,
            COUNT(CASE WHEN to_phone IS NULL THEN 1 END) as null_to_phone,
            COUNT(CASE WHEN to_phone = 'business' THEN 1 END) as business_to_phone,
            COUNT(DISTINCT to_phone) as unique_to_phone_values
        FROM whatsapp_messages
    """)
    
    stats = cursor.fetchone()
    total, with_to_phone, null_to_phone, business_count, unique_values = stats
    
    print(f"📊 Current Statistics:")
    print(f"  - Total messages: {total}")
    print(f"  - Messages with to_phone: {with_to_phone}")
    print(f"  - Messages with NULL to_phone: {null_to_phone}")
    print(f"  - Messages with 'business' to_phone: {business_count}")
    print(f"  - Unique to_phone values: {unique_values}")
    
    # Show current unique values
    cursor.execute("""
        SELECT to_phone, COUNT(*) as count
        FROM whatsapp_messages 
        GROUP BY to_phone
        ORDER BY count DESC
    """)
    
    unique_values = cursor.fetchall()
    print(f"\n📋 Current to_phone values:")
    for value, count in unique_values:
        display_value = f"'{value}'" if value is not None else "NULL"
        print(f"  - {display_value}: {count} messages")
    
    return null_to_phone, business_count

def preview_changes(conn):
    """Preview what changes will be made"""
    cursor = conn.cursor()
    
    print("\n🔍 Preview of changes to be made:")
    
    # Show messages that will be affected
    cursor.execute("""
        SELECT message_id, from_phone, content, to_phone, direction, timestamp
        FROM whatsapp_messages 
        WHERE to_phone IS NULL OR to_phone != 'business'
        ORDER BY timestamp
        LIMIT 10
    """)
    
    messages_to_update = cursor.fetchall()
    
    if messages_to_update:
        print(f"📝 Messages that will be updated (showing up to 10):")
        for msg_id, from_phone, content, to_phone, direction, timestamp in messages_to_update:
            content_preview = (content[:30] + "...") if content and len(content) > 30 else (content or "")
            current_to = f"'{to_phone}'" if to_phone else "NULL"
            print(f"  - {msg_id[:20]}... | from: {from_phone} | to: {current_to} -> 'business' | '{content_preview}' | {direction}")
        
        # Count total messages to be updated
        cursor.execute("""
            SELECT COUNT(*) FROM whatsapp_messages 
            WHERE to_phone IS NULL OR to_phone != 'business'
        """)
        total_to_update = cursor.fetchone()[0]
        
        if len(messages_to_update) < total_to_update:
            print(f"  ... and {total_to_update - len(messages_to_update)} more messages")
        
        return total_to_update
    else:
        print("✅ No messages need to be updated - all already have to_phone = 'business'")
        return 0

def update_to_phone_values(conn):
    """Update all to_phone values to 'business'"""
    try:
        cursor = conn.cursor()
        
        print("\n📝 Updating to_phone values to 'business'...")
        
        # Update all NULL or non-'business' values to 'business'
        cursor.execute("""
            UPDATE whatsapp_messages 
            SET to_phone = 'business'
            WHERE to_phone IS NULL OR to_phone != 'business'
        """)
        
        rows_updated = cursor.rowcount
        print(f"✅ Updated {rows_updated} message(s)")
        
        # Commit the changes
        conn.commit()
        print("✅ Changes committed successfully!")
        
        return True, rows_updated
        
    except Exception as e:
        print(f"❌ Update failed: {e}")
        conn.rollback()
        return False, 0

def verify_updates(conn, expected_updates):
    """Verify the updates were applied correctly"""
    cursor = conn.cursor()
    
    print("\n🔍 Verifying updates...")
    
    # Check final state
    cursor.execute("""
        SELECT 
            COUNT(*) as total_messages,
            COUNT(CASE WHEN to_phone = 'business' THEN 1 END) as business_messages,
            COUNT(CASE WHEN to_phone IS NULL THEN 1 END) as null_messages,
            COUNT(DISTINCT to_phone) as unique_values
        FROM whatsapp_messages
    """)
    
    total, business_count, null_count, unique_count = cursor.fetchone()
    
    print(f"📊 Final Statistics:")
    print(f"  - Total messages: {total}")
    print(f"  - Messages with to_phone = 'business': {business_count}")
    print(f"  - Messages with NULL to_phone: {null_count}")
    print(f"  - Unique to_phone values: {unique_count}")
    
    # Verify all messages now have 'business'
    if business_count == total and null_count == 0:
        print("✅ SUCCESS: All messages now have to_phone = 'business'")
        return True
    else:
        print("❌ ERROR: Some messages still don't have to_phone = 'business'")
        
        # Show remaining non-business values
        cursor.execute("""
            SELECT to_phone, COUNT(*) 
            FROM whatsapp_messages 
            WHERE to_phone != 'business' OR to_phone IS NULL
            GROUP BY to_phone
        """)
        
        remaining = cursor.fetchall()
        if remaining:
            print("Remaining non-'business' values:")
            for value, count in remaining:
                display_value = f"'{value}'" if value is not None else "NULL"
                print(f"  - {display_value}: {count} messages")
        
        return False

def show_sample_data(conn):
    """Show sample of updated data"""
    cursor = conn.cursor()
    
    print("\n📄 Sample of updated messages:")
    cursor.execute("""
        SELECT message_id, from_phone, to_phone, content, direction, timestamp
        FROM whatsapp_messages 
        ORDER BY timestamp DESC
        LIMIT 5
    """)
    
    messages = cursor.fetchall()
    
    for msg_id, from_phone, to_phone, content, direction, timestamp in messages:
        content_preview = (content[:40] + "...") if content and len(content) > 40 else (content or "")
        print(f"  - {direction}: {from_phone} → {to_phone} | '{content_preview}' | {timestamp}")

def main():
    print("📞 Prepopulating to_phone column with 'business'")
    print("=" * 60)
    
    conn = connect_to_db()
    if not conn:
        sys.exit(1)
    
    try:
        # Step 1: Analyze current state
        null_count, business_count = analyze_current_state(conn)
        
        # Step 2: Preview changes
        updates_needed = preview_changes(conn)
        
        if updates_needed == 0:
            print("\n✅ No updates needed - all messages already have to_phone = 'business'")
            return
        
        # Step 3: Ask for confirmation
        print(f"\n⚠️  This will update {updates_needed} message(s) to have to_phone = 'business'")
        print("This represents that all incoming messages are directed TO the business.")
        response = input("Continue with the update? (y/N): ")
        
        if response.lower() != 'y':
            print("❌ Operation cancelled by user")
            return
        
        # Step 4: Perform update
        success, updated_count = update_to_phone_values(conn)
        
        if not success:
            print("❌ Update operation failed!")
            sys.exit(1)
        
        # Step 5: Verify updates
        if verify_updates(conn, updated_count):
            print(f"\n🎉 Successfully updated {updated_count} message(s)!")
            
            # Step 6: Show sample data
            show_sample_data(conn)
            
            print(f"\n✅ All messages now have to_phone = 'business'")
            print("This indicates all messages are directed TO the business (incoming)")
        else:
            print("\n❌ Verification failed!")
            sys.exit(1)
        
    finally:
        conn.close()

if __name__ == "__main__":
    main()