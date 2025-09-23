from fastapi import FastAPI
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import asyncio

from app.config import get_settings
from app.core.database import init_database
from app.core.logging import logger

# API routers
from app.api import health, webhook, messaging, monitoring
try:
    from app.api import archive
except ImportError:
    archive = None
from app.api_endpoints import router as legacy_api_router

# SQS Workers
try:
    from app.workers.message_processor import message_processor
    SQS_ENABLED = True
except ImportError:
    message_processor = None
    SQS_ENABLED = False
    logger.warning("⚠️  SQS workers not available - running without message processing")

# Database and workers initialization
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
    
    # Start SQS message processor if available
    processor_task = None
    if SQS_ENABLED and message_processor:
        try:
            # Start message processor workers in background (don't await)
            processor_task = asyncio.create_task(message_processor._start_workers())
            logger.info("✅ SQS message processor started")
        except Exception as e:
            logger.error(f"❌ Failed to start message processor: {e}")
    else:
        logger.info("ℹ️  Running without SQS message processing")
    
    yield
    
    # Shutdown
    logger.info("🛑 Application shutdown initiated")
    
    # Stop message processor
    if processor_task and not processor_task.done():
        logger.info("🛑 Stopping message processor...")
        await message_processor.stop()
        processor_task.cancel()
        try:
            await processor_task
        except asyncio.CancelledError:
            logger.info("✅ Message processor stopped")
    
    logger.info("🛑 Application shutdown complete")

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
app.include_router(messaging.router)
app.include_router(monitoring.router)

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
        "features": {
            "sqs_queuing": SQS_ENABLED,
            "message_processing": bool(message_processor),
            "monitoring": True,
            "async_messaging": True
        },
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "messaging": "/messaging",
            "monitoring_dashboard": "/monitoring/dashboard",
            "webhook": "/webhook"
        }
    }
