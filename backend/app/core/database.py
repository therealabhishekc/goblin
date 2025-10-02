"""
Database connection management.
Handles PostgreSQL connections with IAM authentication.
"""
import os
import boto3
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from contextlib import contextmanager
from botocore.exceptions import ClientError
from urllib.parse import quote_plus
from app.core.logging import logger

# Database Configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "whatsapp_business")
DB_USER = os.getenv("DB_USER", "app_user")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
USE_IAM_AUTH = os.getenv("USE_IAM_AUTH", "false").lower() == "true"

def get_iam_db_token():
    """Generate IAM database authentication token"""
    try:
        rds_client = boto3.client('rds', region_name=AWS_REGION)
        token = rds_client.generate_db_auth_token(
            DBHostname=DB_HOST,
            Port=DB_PORT,
            DBUsername=DB_USER,
            Region=AWS_REGION
        )
        logger.info("✅ IAM database token generated successfully")
        return token
    except ClientError as e:
        logger.error(f"❌ Failed to generate IAM token: {e}")
        raise

def create_database_url():
    """Create database URL with appropriate authentication"""
    
    logger.info(f"🔧 Database config - USE_IAM_AUTH: {USE_IAM_AUTH}, DB_HOST: {DB_HOST}")
    
    if USE_IAM_AUTH:
        logger.info("🔐 Using IAM database authentication")
        try:
            token = get_iam_db_token()
            encoded_token = quote_plus(token)
            url = f"postgresql://{DB_USER}:{encoded_token}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require"
            logger.info(f"✅ IAM database URL created for {DB_HOST}")
            return url
        except Exception as e:
            logger.error(f"❌ Failed to create IAM database URL: {e}")
            raise
    
    # Fallback to environment DATABASE_URL
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        logger.info("🔧 Using DATABASE_URL from environment")
        return database_url
    
    # Last resort: password auth
    db_password = os.getenv("DB_PASSWORD", "password")
    url = f"postgresql://{DB_USER}:{db_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require"
    logger.info("🔑 Using password authentication")
    return url

# Database setup
engine = None
SessionLocal = None
Base = declarative_base()

def init_database():
    """Initialize database connection"""
    global engine, SessionLocal
    
    try:
        logger.info("🔧 Initializing database connection...")
        url = create_database_url()
        engine = create_engine(url, echo=False, pool_pre_ping=True)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
            
        logger.info("✅ Database connection initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")
        raise

def get_database_session():
    """Get database session dependency for FastAPI"""
    if SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Context manager for database sessions"""
    if SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def test_database_connection() -> bool:
    """Test database connectivity"""
    try:
        if engine is None:
            init_database()
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        
        return True
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False
