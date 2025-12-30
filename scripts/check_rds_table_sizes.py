#!/usr/bin/env python3
"""
Check RDS table sizes and disk usage

Usage:
    python check_rds_table_sizes.py

    Or with custom connection (bypassing default config):
    export DB_HOST=whatsapp-postgres-development.cibi66cyqd2r.us-east-1.rds.amazonaws.com
    export DB_NAME=whatsapp-postgres-development
    export DB_USER=postgres
    export DB_PASSWORD=0?yZZ*n~tj?FX]j2xXg602Z.$|DK
    export DB_SSL_MODE=require  # or disable for local testing
    python check_rds_table_sizes.py
"""
import sys
import os
from pathlib import Path

# Add the backend directory to the path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.core.database import get_db_session, init_database
from sqlalchemy import text


def format_bytes(bytes_size):
    """Format bytes to human-readable format"""
    if bytes_size is None:
        return "0 B"
    
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} PB"


def get_table_sizes():
    """Query PostgreSQL for table sizes"""
    query = text("""
        SELECT 
            schemaname as schema,
            tablename as table_name,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
            pg_total_relation_size(schemaname||'.'||tablename) as total_bytes,
            pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as table_size,
            pg_relation_size(schemaname||'.'||tablename) as table_bytes,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) as indexes_size
        FROM pg_tables
        WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
        ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
    """)
    
    with get_db_session() as db:
        result = db.execute(query)
        rows = result.fetchall()
        
        print("\n" + "="*100)
        print("DATABASE TABLE SIZES")
        print("="*100)
        print(f"{'Schema':<15} {'Table Name':<40} {'Total Size':<15} {'Table':<15} {'Indexes':<15}")
        print("-"*100)
        
        total_bytes = 0
        for row in rows:
            schema, table_name, total_size, total_bytes_val, table_size, table_bytes_val, indexes_size = row
            total_bytes += total_bytes_val
            print(f"{schema:<15} {table_name:<40} {total_size:<15} {table_size:<15} {indexes_size:<15}")
        
        print("-"*100)
        print(f"{'TOTAL DATABASE SIZE:':<56} {format_bytes(total_bytes)}")
        print("="*100)
        
        # Get database size
        db_size_query = text("""
            SELECT 
                pg_database.datname as database_name,
                pg_size_pretty(pg_database_size(pg_database.datname)) as size,
                pg_database_size(pg_database.datname) as size_bytes
            FROM pg_database
            WHERE pg_database.datname = current_database();
        """)
        
        db_result = db.execute(db_size_query)
        db_row = db_result.fetchone()
        
        print(f"\nTotal database size (including system tables): {db_row[1]}")
        
        # Get top 10 largest tables with row counts
        print("\n" + "="*100)
        print("TOP 10 LARGEST TABLES WITH ROW COUNTS")
        print("="*100)
        
        top_tables_query = text("""
            SELECT 
                schemaname as schema,
                tablename as table_name,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
                (SELECT count(*) FROM (SELECT 1 FROM "{schema}"."{table}" LIMIT 1000000) t) as estimated_rows
            FROM pg_tables
            WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
            LIMIT 10;
        """)
        
        # For row counts, we need to query each table individually
        for row in rows[:10]:
            schema, table_name = row[0], row[1]
            try:
                count_query = text(f'SELECT COUNT(*) FROM "{schema}"."{table_name}"')
                count_result = db.execute(count_query)
                row_count = count_result.scalar()
                print(f"{schema}.{table_name:<40} - Size: {row[2]:<15} Rows: {row_count:,}")
            except Exception as e:
                print(f"{schema}.{table_name:<40} - Size: {row[2]:<15} Rows: Error - {str(e)[:30]}")


if __name__ == "__main__":
    try:
        # Initialize database connection
        init_database()
        get_table_sizes()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
