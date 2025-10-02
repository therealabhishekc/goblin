"""
DEPRECATED: Database configuration has been consolidated to app.core.database

This package contains legacy database code that has been consolidated into:
- app.core.database - Main database connection management (USE THIS)

Legacy files (will be removed in future cleanup):
- connection.py - Old connection implementation (now redirects to core)
- models.py - Old model definitions (replaced by individual files in app/models/)

For new development, use:
    from app.core.database import get_database_session, Base, init_database
"""

# Re-export core database functions for compatibility
from app.core.database import (
    get_database_session,
    get_db_session,
    init_database,
    Base,
    SessionLocal,
    engine
)
