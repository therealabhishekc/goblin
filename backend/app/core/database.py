"""
Database connection management.
Handles PostgreSQL connections with IAM authentication.
"""
import os
import time
import urllib.request
from pathlib import Path
import boto3
from sqlalchemy import create_engine, text, event
from sqlalchemy.engine import URL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator, Optional
from contextlib import contextmanager
from botocore.exceptions import ClientError
from app.core.logging import logger

# Database Configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "whatsapp_business")
DB_USER = os.getenv("DB_USER", "app_user")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
USE_IAM_AUTH = os.getenv("USE_IAM_AUTH", "false").lower() == "true"
DB_SSL_MODE = (os.getenv("DB_SSL_MODE", "verify-full") or "verify-full").strip().lower()
CERTS_DIR = Path(__file__).resolve().parent / "certs"
DEFAULT_CERT_FILENAME = f"{AWS_REGION}-bundle.pem"
DEFAULT_CERT_PATH = os.getenv("DB_SSL_ROOT_CERT") or str(CERTS_DIR / DEFAULT_CERT_FILENAME)
AWS_RDS_CERT_BUNDLE_URL = os.getenv(
    "AWS_RDS_CERT_BUNDLE_URL",
    f"https://truststore.pki.rds.amazonaws.com/{AWS_REGION}/{AWS_REGION}-bundle.pem",
)


def _ensure_ssl_root_cert(cert_path: Optional[str]) -> Optional[str]:
    """Ensure the SSL root certificate exists locally, downloading it if necessary.

    Using ``Optional`` keeps compatibility with Python runtimes that do not support
    the PEP 604 ``|`` union syntax (e.g. AWS App Runner's Python 3.9 image).
    """
    if not cert_path:
        logger.warning(
            "⚠️ DB_SSL_ROOT_CERT not provided; relying on system trust store for database SSL verification."
        )
        return None

    path = Path(cert_path).expanduser()

    if path.name.lower() == "system":
        logger.info("ℹ️ Using system trust store for database SSL verification.")
        return None

    if path.exists():
        return str(path)

    bundle_url = AWS_RDS_CERT_BUNDLE_URL
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(
            f"📥 Downloading AWS RDS CA bundle from {bundle_url} to {path} for database SSL verification..."
        )
        with urllib.request.urlopen(bundle_url, timeout=10) as response:
            path.write_bytes(response.read())
        logger.info("✅ AWS RDS CA bundle downloaded successfully.")
        return str(path)
    except Exception as exc:  # pragma: no cover - network failures surfaced via logs
        logger.error(f"❌ Failed to retrieve AWS RDS CA bundle: {exc}")
        return None


DB_SSL_ROOT_CERT = _ensure_ssl_root_cert(DEFAULT_CERT_PATH)
if DB_SSL_ROOT_CERT:
    logger.info(
        f"🔐 Database SSL configured with mode='{DB_SSL_MODE}' and root certificate='{DB_SSL_ROOT_CERT}'."
    )
else:
    logger.warning(
        f"⚠️ Database SSL operating with mode='{DB_SSL_MODE}' using system trust store (no explicit root certificate)."
    )

class IAMTokenRefresher:
    """
    Automatically refresh IAM tokens before they expire.
    Tokens expire after 15 minutes, so we refresh at 14 minutes.
    """
    
    def __init__(self):
        self.token = None
        self.token_generated_at = None
        self.token_ttl = 840  # 14 minutes (safe margin before 15min expiry)
    
    def get_fresh_token(self):
        """Get a fresh token, refreshing if needed"""
        now = time.time()
        
        # Check if token needs refresh
        if (self.token is None or 
            self.token_generated_at is None or 
            (now - self.token_generated_at) > self.token_ttl):
            
            logger.info("🔄 Refreshing IAM database token...")
            self.token = self._generate_token()
            self.token_generated_at = now
            logger.info("✅ IAM token refreshed successfully")
        
        return self.token
    
    def _generate_token(self):
        """Generate a new IAM database authentication token"""
        try:
            rds_client = boto3.client('rds', region_name=AWS_REGION)
            token = rds_client.generate_db_auth_token(
                DBHostname=DB_HOST,
                Port=DB_PORT,
                DBUsername=DB_USER,
                Region=AWS_REGION
            )
            return token
        except ClientError as e:
            logger.error(f"❌ Failed to generate IAM token: {e}")
            raise

# Global token refresher instance
token_refresher = IAMTokenRefresher()

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
    connection_query = {"sslmode": DB_SSL_MODE}
    if DB_SSL_ROOT_CERT:
        connection_query["sslrootcert"] = DB_SSL_ROOT_CERT
    
    if USE_IAM_AUTH:
        logger.info("🔐 Using IAM database authentication")
        try:
            token = token_refresher.get_fresh_token()
            url = URL.create(
                drivername="postgresql",
                username=DB_USER,
                password=token,
                host=DB_HOST,
                port=DB_PORT,
                database=DB_NAME,
                query=connection_query,
            )
            cert_info = connection_query.get("sslrootcert", "system trust store")
            logger.info(
                f"✅ IAM database URL created for {DB_HOST} (sslmode={DB_SSL_MODE}, sslrootcert={cert_info})"
            )
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
    url = URL.create(
        drivername="postgresql",
        username=DB_USER,
        password=db_password,
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        query=connection_query,
    )
    cert_info = connection_query.get("sslrootcert", "system trust store")
    logger.info(
        f"🔑 Using password authentication (sslmode={DB_SSL_MODE}, sslrootcert={cert_info})"
    )
    return url

# Database setup
engine = None
SessionLocal = None
Base = declarative_base()

def init_database():
    """Initialize database connection with IAM token refresh support"""
    global engine, SessionLocal
    
    try:
        logger.info("🔧 Initializing database connection...")
        url = create_database_url()
        
        # Create engine with pool_pre_ping and pool_recycle
        # pool_recycle=600 ensures connections are recycled every 10 minutes (before token expires)
        connect_args = {
            "connect_timeout": 30,
            "sslmode": DB_SSL_MODE,
        }
        if DB_SSL_ROOT_CERT:
            connect_args["sslrootcert"] = DB_SSL_ROOT_CERT
        engine = create_engine(
            url, 
            echo=False, 
            pool_pre_ping=True,
            pool_recycle=600,  # Recycle connections every 10 minutes
            pool_size=10,
            max_overflow=20,
            connect_args=connect_args,
        )
        
        # Add event listener to refresh token on new connections (for IAM auth)
        if USE_IAM_AUTH:
            @event.listens_for(engine, "do_connect")
            def receive_do_connect(dialect, conn_rec, cargs, cparams):
                """Refresh IAM token before each new connection"""
                logger.debug("🔄 Creating new database connection with fresh IAM token...")
                token = token_refresher.get_fresh_token()
                cparams['password'] = token
        
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
