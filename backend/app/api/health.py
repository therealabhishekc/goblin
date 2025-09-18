"""
Health check endpoints.
System status, database connectivity, and service health monitoring.
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.core.database import get_database_session
from app.config import get_settings
import time

router = APIRouter(prefix="/health", tags=["Health Checks"])

@router.get("/")
async def health_check():
    """Basic health check"""
    return JSONResponse(
        content={
            "status": "healthy",
            "timestamp": time.time(),
            "service": "WhatsApp Business API"
        },
        status_code=200
    )

@router.get("/database")
async def database_health(db: Session = Depends(get_database_session)):
    """Database connectivity check"""
    try:
        # Simple query to test database connection
        db.execute("SELECT 1")
        
        return {
            "status": "healthy",
            "database": "postgresql",
            "connection": "active",
            "timestamp": time.time()
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "database": "postgresql",
                "error": str(e),
                "timestamp": time.time()
            }
        )

@router.get("/config")
async def config_check():
    """Configuration status check"""
    settings = get_settings()
    
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "app_version": settings.app_version,
        "environment": "production" if not settings.debug else "development",
        "whatsapp_configured": bool(settings.whatsapp_token),
        "timestamp": time.time()
    }

@router.get("/detailed")
async def detailed_health(db: Session = Depends(get_database_session)):
    """Comprehensive health check"""
    try:
        settings = get_settings()
        
        # Test database
        db.execute("SELECT 1")
        db_status = "healthy"
        
        # Check configuration
        config_issues = []
        if not settings.whatsapp_token:
            config_issues.append("WhatsApp token not configured")
        if not settings.verify_token:
            config_issues.append("Verify token not configured")
        
        return {
            "status": "healthy" if not config_issues else "degraded",
            "timestamp": time.time(),
            "services": {
                "database": {
                    "status": db_status,
                    "type": "postgresql"
                },
                "whatsapp_api": {
                    "status": "configured" if settings.whatsapp_token else "not_configured"
                }
            },
            "configuration": {
                "status": "complete" if not config_issues else "incomplete",
                "issues": config_issues
            },
            "application": {
                "name": settings.app_name,
                "version": settings.app_version,
                "debug": settings.debug
            }
        }
        
    except Exception as e:
        return JSONResponse(
            content={
                "status": "unhealthy",
                "timestamp": time.time(),
                "error": str(e)
            },
            status_code=503
        )
