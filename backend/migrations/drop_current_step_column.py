"""
Migration: Drop current_step column from conversation_state table
Date: 2024
Description: Remove current_step column as step tracking is now handled in context JSON field
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_database_url():
    """Get database URL from environment variables"""
    # Try DATABASE_URL first (standard format)
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url
    
    # Fall back to individual variables
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    
    if not all([db_host, db_name, db_user]):
        raise ValueError("Missing required database environment variables (DATABASE_URL or DB_HOST/DB_NAME/DB_USER)")
    
    if db_password:
        return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    else:
        return f"postgresql://{db_user}@{db_host}:{db_port}/{db_name}"

def run_migration():
    """Execute the migration"""
    print("🚀 Starting migration: Drop current_step column")
    
    # Create database connection
    database_url = get_database_url()
    engine = create_engine(database_url)
    
    with engine.begin() as connection:
        # Check if column exists
        check_sql = """
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'conversation_state' 
        AND column_name = 'current_step'
        """
        
        result = connection.execute(text(check_sql))
        column_exists = result.fetchone() is not None
        
        if not column_exists:
            print("✅ Column 'current_step' does not exist - migration already applied or not needed")
            return
        
        print("📋 Column 'current_step' exists - proceeding with drop")
        
        # Drop the column
        drop_sql = """
        ALTER TABLE conversation_state 
        DROP COLUMN IF EXISTS current_step;
        """
        
        connection.execute(text(drop_sql))
        print("✅ Successfully dropped column 'current_step' from conversation_state table")
        
        # Verify column is gone
        result = connection.execute(text(check_sql))
        if result.fetchone() is None:
            print("✅ Verified: Column no longer exists")
        else:
            print("⚠️ Warning: Column still exists after drop attempt")

def rollback_migration():
    """Rollback migration - add column back"""
    print("⏪ Rolling back migration: Add current_step column")
    
    # Create database connection
    database_url = get_database_url()
    engine = create_engine(database_url)
    
    with engine.begin() as connection:
        # Add column back with default value
        add_sql = """
        ALTER TABLE conversation_state 
        ADD COLUMN IF NOT EXISTS current_step VARCHAR(50) DEFAULT 'initial' NOT NULL;
        """
        
        connection.execute(text(add_sql))
        print("✅ Successfully added back column 'current_step'")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Drop current_step column migration")
    parser.add_argument(
        "--rollback",
        action="store_true",
        help="Rollback migration (add column back)"
    )
    
    args = parser.parse_args()
    
    try:
        if args.rollback:
            rollback_migration()
        else:
            run_migration()
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)
