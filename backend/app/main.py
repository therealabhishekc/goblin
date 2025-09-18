from fastapi import FastAPI
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.config import get_settings
from app.core.database import init_database
from app.core.logging import logger

# API routers
from app.api import health, webhook
try:
    from app.api import archive
except ImportError:
    archive = None
from app.api_endpoints import router as legacy_api_router

# Database initialization
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize application on startup"""
    settings = get_settings()
    logger.info(f"🚀 Starting {settings.app_name} v{settings.app_version}")
    
    try:
        # Initialize database
        init_database()
        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
    
    yield
    
    logger.info("🛑 Application shutdown")

# Create FastAPI application
settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    description="Enterprise WhatsApp Business API with PostgreSQL integration",
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan
)

# Include API routers
app.include_router(health.router)
app.include_router(webhook.router)

# Include archive router if available
if archive:
    try:
        app.include_router(archive.router)
        logger.info("✅ Archive API endpoints loaded")
    except Exception as e:
        logger.warning(f"⚠️  Archive API endpoints failed to load: {e}")

# Legacy endpoints (for backward compatibility)
try:
    app.include_router(legacy_api_router)
    logger.info("✅ Legacy API endpoints loaded")
except Exception as e:
    logger.warning(f"⚠️  Legacy API endpoints failed to load: {e}")

# Include other routers if available
try:
    from app.websocket import router as websocket_router
    app.include_router(websocket_router)
    logger.info("✅ WebSocket router loaded")
except Exception as e:
    logger.warning(f"⚠️  WebSocket router failed to load: {e}")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }
