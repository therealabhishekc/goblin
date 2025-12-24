"""
Health check endpoints.
System status, database connectivity, SQS integration, and service health monitoring.
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import get_database_session
from app.core.config import get_settings
import time

# SQS integration
try:
    from app.services.sqs_service import sqs_service
    from app.workers.message_processor import message_processor
    SQS_AVAILABLE = True
except ImportError:
    sqs_service = None
    message_processor = None
    SQS_AVAILABLE = False

# Startup validation
try:
    from app.services.startup_validator import startup_validator, validate_startup, is_application_ready
    STARTUP_VALIDATION_AVAILABLE = True
except ImportError:
    startup_validator = None
    validate_startup = None
    is_application_ready = None
    STARTUP_VALIDATION_AVAILABLE = False

router = APIRouter(prefix="/health", tags=["Health Checks"])

@router.get("/startup")
async def startup_validation():
    """Run or get startup validation results"""
    if not STARTUP_VALIDATION_AVAILABLE:
        return JSONResponse(
            content={
                "status": "not_available",
                "message": "Startup validation not configured",
                "timestamp": time.time()
            },
            status_code=503
        )
    
    try:
        # Run validation if not already done or force re-run
        is_ready = await validate_startup()
        validation_summary = startup_validator.get_validation_summary()
        
        status_code = 200 if is_ready else 503
        
        return JSONResponse(
            content={
                "startup_validation": validation_summary,
                "ready_for_traffic": is_ready,
                "timestamp": time.time()
            },
            status_code=status_code
        )
        
    except Exception as e:
        return JSONResponse(
            content={
                "status": "error",
                "error": str(e),
                "timestamp": time.time()
            },
            status_code=503
        )

@router.get("/")
@router.get("")
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
        db.execute(text("SELECT 1"))
        
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
    """Comprehensive health check with SQS queue validation"""
    try:
        settings = get_settings()
        
        # Test database
        db.execute(text("SELECT 1"))
        db_status = "healthy"
        
        # Check configuration
        config_issues = []
        if not settings.whatsapp_token:
            config_issues.append("WhatsApp token not configured")
        if not settings.verify_token:
            config_issues.append("Verify token not configured")
        
        # Enhanced SQS queue validation
        sqs_status = "not_available"
        sqs_queues = {}
        queue_issues = []
        
        if SQS_AVAILABLE and sqs_service:
            try:
                sqs_health = await sqs_service.health_check()
                sqs_status = sqs_health["status"]
                sqs_queues = sqs_health["queues"]
                
                # Check critical queues are configured
                required_queues = ["incoming", "outgoing", "analytics"]
                missing_queues = []
                unhealthy_queues = []
                
                for queue_name in required_queues:
                    if queue_name not in sqs_queues:
                        missing_queues.append(queue_name)
                    elif sqs_queues[queue_name]["status"] != "healthy":
                        unhealthy_queues.append(queue_name)
                
                if missing_queues:
                    queue_issues.extend([f"{q} queue not configured" for q in missing_queues])
                if unhealthy_queues:
                    queue_issues.extend([f"{q} queue unhealthy" for q in unhealthy_queues])
                    
            except Exception as e:
                sqs_status = "error"
                queue_issues.append(f"SQS health check failed: {str(e)}")
        else:
            queue_issues.append("SQS service not available")
        
        # Determine overall status
        all_issues = config_issues + queue_issues
        overall_status = "healthy" if not all_issues else "degraded"
        
        return {
            "status": overall_status,
            "timestamp": time.time(),
            "services": {
                "database": {
                    "status": db_status,
                    "type": "postgresql"
                },
                "whatsapp_api": {
                    "status": "configured" if settings.whatsapp_token else "not_configured"
                },
                "sqs": {
                    "status": sqs_status,
                    "enabled": SQS_AVAILABLE,
                    "queues": sqs_queues,
                    "issues": queue_issues
                }
            },
            "configuration": {
                "status": "complete" if not all_issues else "incomplete",
                "issues": all_issues
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

@router.get("/sqs")
async def sqs_health():
    """SQS service health check"""
    if not SQS_AVAILABLE:
        return JSONResponse(
            content={
                "status": "not_available",
                "message": "SQS service not configured",
                "timestamp": time.time()
            },
            status_code=503
        )
    
    try:
        sqs_health_data = await sqs_service.health_check()
        status_code = 200 if sqs_health_data["sqs_service"] == "healthy" else 503
        
        return JSONResponse(
            content=sqs_health_data,
            status_code=status_code
        )
    except Exception as e:
        return JSONResponse(
            content={
                "status": "error",
                "error": str(e),
                "timestamp": time.time()
            },
            status_code=503
        )

@router.get("/readiness")
async def readiness_check(db: Session = Depends(get_database_session)):
    """Readiness check - determines if app can accept webhook traffic"""
    readiness_status = {
        "ready": True,
        "timestamp": time.time(),
        "checks": {},
        "blocking_issues": []
    }
    
    try:
        # Database connectivity (critical)
        try:
            db.execute(text("SELECT 1"))
            readiness_status["checks"]["database"] = {
                "status": "healthy",
                "critical": True
            }
        except Exception as e:
            readiness_status["checks"]["database"] = {
                "status": "unhealthy",
                "critical": True,
                "error": str(e)
            }
            readiness_status["ready"] = False
            readiness_status["blocking_issues"].append("Database connectivity failed")
        
        # SQS queue validation (critical for webhook processing)
        if SQS_AVAILABLE and sqs_service:
            try:
                sqs_health = await sqs_service.health_check()
                
                # Check that critical queues are available and healthy
                critical_queues = ["incoming"]
                sqs_ready = True
                sqs_issues = []
                
                for queue_name in critical_queues:
                    if queue_name not in sqs_health["queues"]:
                        sqs_ready = False
                        sqs_issues.append(f"{queue_name} queue not configured")
                    elif sqs_health["queues"][queue_name]["status"] != "healthy":
                        sqs_ready = False
                        sqs_issues.append(f"{queue_name} queue unhealthy: {sqs_health['queues'][queue_name].get('error', 'unknown')}")
                
                readiness_status["checks"]["sqs_queues"] = {
                    "status": "healthy" if sqs_ready else "unhealthy",
                    "critical": True,
                    "details": sqs_health["queues"],
                    "issues": sqs_issues
                }
                
                if not sqs_ready:
                    readiness_status["ready"] = False
                    readiness_status["blocking_issues"].extend(sqs_issues)
                    
            except Exception as e:
                readiness_status["checks"]["sqs_queues"] = {
                    "status": "error",
                    "critical": True,
                    "error": str(e)
                }
                readiness_status["ready"] = False
                readiness_status["blocking_issues"].append(f"SQS health check failed: {str(e)}")
        else:
            readiness_status["checks"]["sqs_queues"] = {
                "status": "not_available",
                "critical": True,
                "error": "SQS service not configured"
            }
            readiness_status["ready"] = False
            readiness_status["blocking_issues"].append("SQS service not available")
        
        # WhatsApp API configuration (critical)
        settings = get_settings()
        whatsapp_ready = bool(settings.whatsapp_token and settings.verify_token)
        
        readiness_status["checks"]["whatsapp_config"] = {
            "status": "healthy" if whatsapp_ready else "not_configured",
            "critical": True,
            "has_token": bool(settings.whatsapp_token),
            "has_verify_token": bool(settings.verify_token)
        }
        
        if not whatsapp_ready:
            readiness_status["ready"] = False
            readiness_status["blocking_issues"].append("WhatsApp API credentials not configured")
        
    except Exception as e:
        readiness_status = {
            "ready": False,
            "timestamp": time.time(),
            "error": str(e),
            "blocking_issues": [f"Readiness check failed: {str(e)}"]
        }
    
    status_code = 200 if readiness_status["ready"] else 503
    return JSONResponse(content=readiness_status, status_code=status_code)

@router.get("/workers")
async def workers_health():
    """Message processor workers health check"""
    if not SQS_AVAILABLE or not message_processor:
        return JSONResponse(
            content={
                "status": "not_available",
                "message": "Message processor not configured",
                "timestamp": time.time()
            },
            status_code=503
        )
    
    try:
        worker_stats = message_processor.get_stats()
        status_code = 200 if worker_stats["running"] else 503
        
        return JSONResponse(
            content={
                "status": "healthy" if worker_stats["running"] else "stopped",
                "workers": worker_stats,
                "timestamp": time.time()
            },
            status_code=status_code
        )
    except Exception as e:
        return JSONResponse(
            content={
                "status": "error",
                "error": str(e),
                "timestamp": time.time()
            },
            status_code=503
        )
