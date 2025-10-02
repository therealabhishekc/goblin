# This file has been deprecated and consolidated into core/database.py
# All database connections now use the newer implementation with IAM auth support
# This file is kept temporarily for reference - will be removed in next cleanup

# MIGRATION NOTICE:
# - Use: from app.core.database import get_database_session, init_database, Base
# - Instead of: from app.database.connection import ...
# - New implementation supports AWS IAM authentication and improved security

from app.core.database import (
    get_database_session,
    get_db_session, 
    init_database,
    Base,
    SessionLocal,
    engine
)

# Re-export for backward compatibility (temporary)
__all__ = [
    'get_database_session',
    'get_db_session',
    'init_database', 
    'Base',
    'SessionLocal',
    'engine'
]
