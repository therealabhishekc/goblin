from fastapi import FastAPI
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import asyncio
import time

from app.config import get_settings
from app.core.database import init_database
from app.core.logging import logger

# API routers
from app.api import health, webhook, messaging, monitoring
try:
    from app.api import archive
except ImportError:
    archive = None
try:
    from app.api import admin
except ImportError:
    admin = None
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
    
    # 🔒 Start RACE-SAFE SQS message processor if available
    processor_task = None
    if SQS_ENABLED and message_processor:
        try:
            # Start race-safe message processor in background
            processor_task = asyncio.create_task(message_processor.start_processing())
            logger.info("✅ 🔒 Race-safe SQS message processor started")
        except Exception as e:
            logger.error(f"❌ Failed to start message processor: {e}")
    else:
        logger.info("ℹ️  Running without SQS message processing")
    
    yield
    
    # 🔒 RACE-SAFE Shutdown
    logger.info("🛑 Application shutdown initiated")
    
    # Stop message processor gracefully
    if processor_task and message_processor:
        logger.info("🛑 Stopping race-safe message processor...")
        message_processor.stop_processing()
        
        # Give processor time to finish current messages
        try:
            await asyncio.wait_for(processor_task, timeout=30.0)
            logger.info("✅ Message processor stopped gracefully")
        except asyncio.TimeoutError:
            logger.warning("⚠️ Message processor stop timeout, cancelling...")
            processor_task.cancel()
            try:
                await processor_task
            except asyncio.CancelledError:
                logger.info("✅ Message processor cancelled")
    
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

# Include admin router if available  
if admin:
    try:
        app.include_router(admin.router)
        logger.info("✅ Admin API endpoints loaded")
    except Exception as e:
        logger.warning(f"⚠️  Admin API endpoints failed to load: {e}")

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
    """🔒 Race-Safe Root endpoint with enhanced status information"""
    return {
        "message": f"Welcome to {settings.app_name} 🔒 Race-Safe Edition",
        "version": settings.app_version,
        "status": "running",
        "features": {
            "race_condition_prevention": True,
            "atomic_deduplication": True,
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
        },
        "processor_stats": message_processor.get_stats() if message_processor else None
    }

@app.get("/health/detailed")
async def detailed_health_check():
    """🔒 Enhanced health check with race-safe components"""
    from app.services.sqs_service import sqs_service
    from app.dynamodb_client import table
    
    health_status = {
        "status": "healthy",
        "timestamp": int(time.time()),
        "components": {
            "dynamodb": {
                "status": "healthy" if table else "unavailable",
                "table_configured": bool(table)
            },
            "sqs": "checking...",
            "message_processor": {
                "status": "running" if (message_processor and message_processor.running) else "stopped",
                "stats": message_processor.get_stats() if message_processor else None
            }
        }
    }
    
    # Check SQS health
    try:
        sqs_health = await sqs_service.health_check()
        health_status["components"]["sqs"] = sqs_health
    except Exception as e:
        health_status["components"]["sqs"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    return health_status
