"""
Database connection management.
Handles PostgreSQL and DynamoDB c    
     #    
    # Use traditional password authentication
    db_password = os.getenv("DB_PASSWORD", "password")
    url = f"postgresql://{DB_USER}:{db_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    logger.info("🔑 Using password authentication")
    return url

# Create engine with dynamic URLtional password authentication
    db_password = os.getenv("DB_PASSWORD", "password")
    url = f"postgresql://{DB_USER}:{db_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    logger.info("🔑 Using password authentication")
    return url

# Create engine with dynamic URLaditional password authentication
    db_password = os.getenv("DB_PASSWORD", "password")
    url = f"postgresql://{DB_USER}:{db_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    logger.info("🔑 Using password authentication")
    return url with IAM authentication.
"""
import os
import boto3
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from contextlib import contextmanager
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)

# Database Configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "whatsapp_business")
DB_USER = os.getenv("DB_USER", "app_user")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
USE_IAM_AUTH = os.getenv("USE_IAM_AUTH", "false").lower() == "true"

# Fallback to traditional auth for local development
DATABASE_URL = os.getenv("DATABASE_URL")

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
    
    if USE_IAM_AUTH:
        # Always use IAM authentication when enabled, ignore DATABASE_URL
        logger.info("🔐 Using IAM database authentication")
        token = get_iam_db_token()
        url = f"postgresql://{DB_USER}:{token}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require"
        return url
    
    # For non-IAM auth, try DATABASE_URL first
    try:
        from ..config import get_settings
        settings = get_settings()
        database_url = settings.database_url
        if database_url and ':' in database_url.split('@')[0]:  # Check if password is included
            logger.info("🔧 Using DATABASE_URL from configuration")
            return database_url
    except Exception as e:
        logger.warning(f"Could not load settings: {e}")
    
    # Fallback to environment variable
    DATABASE_URL = os.getenv("DATABASE_URL")
    if DATABASE_URL and ':' in DATABASE_URL.split('@')[0]:  # Check if password is included
        logger.info("🔧 Using DATABASE_URL from environment")
        return DATABASE_URL
    
    # Use traditional password authentication
    db_password = os.getenv("DB_PASSWORD", "password")
    url = f"postgresql://{DB_USER}:{db_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    logger.info("� Using password authentication")
    return url

# Create engine with dynamic URL
def create_db_engine():
    """Create SQLAlchemy engine with token refresh capability"""
    
    def get_connection():
        """Get database connection with fresh IAM token if needed"""
        url = create_database_url()
        return create_engine(
            url,
            pool_pre_ping=True,
            pool_recycle=300,  # Refresh connections every 5 minutes
            echo=os.getenv("DEBUG", "false").lower() == "true"
        )
    
    return get_connection()

# Initialize engine
engine = create_db_engine()

# Add event listener to refresh IAM tokens
@event.listens_for(engine, "do_connect")
def refresh_iam_token(dialect, conn_rec, cargs, cparams):
    """Refresh IAM token on new connections"""
    if USE_IAM_AUTH and not DATABASE_URL:
        try:
            token = get_iam_db_token()
            # Update the password in connection params
            cparams['password'] = token
            logger.debug("🔄 IAM token refreshed for new connection")
        except Exception as e:
            logger.error(f"❌ Failed to refresh IAM token: {e}")
            raise

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# DynamoDB setup
dynamodb = boto3.resource('dynamodb', region_name=os.getenv('AWS_REGION', 'us-east-1'))

def get_database_session() -> Generator[Session, None, None]:
    """
    Dependency function to get database session.
    Use this in FastAPI dependency injection.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_db_session():
    """
    Context manager for database sessions.
    Use in services and repositories.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_database():
    """
    Initialize database by creating all tables.
    Run this on application startup.
    """
    # Import all SQLAlchemy models to ensure they're registered
    from ..models.whatsapp import WhatsAppMessageDB
    from ..models.user import UserProfileDB  
    from ..models.business import BusinessMetricsDB, MessageTemplateDB
    
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")

def get_dynamodb_table(table_name: str):
    """Get DynamoDB table reference"""
    return dynamodb.Table(table_name)
