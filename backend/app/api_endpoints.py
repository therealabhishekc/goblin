"""
Analytics API endpoints.
Legacy endpoints for analytics and message history - kept for backward compatibility.

Note: User management endpoints have been moved to /app/api/users.py
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.core.database import get_database_session
from app.services.whatsapp_service import WhatsAppService

router = APIRouter(prefix="/api", tags=["Analytics & Messages"])


# ============================================================================
# ANALYTICS ENDPOINTS
# ============================================================================

@router.get("/analytics/daily")
async def get_daily_analytics(
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format"),
    db: Session = Depends(get_database_session)
):
    """Get analytics for a specific day"""
    target_date = datetime.utcnow()
    if date:
        try:
            target_date = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    with WhatsAppService(db) as service:
        analytics = service.get_daily_analytics(target_date)
        if not analytics:
            return {
                "date": target_date.strftime("%Y-%m-%d"),
                "message": "No data available for this date"
            }
        return analytics


@router.get("/analytics/summary")
async def get_analytics_summary(db: Session = Depends(get_database_session)):
    """Get overall analytics summary"""
    with WhatsAppService(db) as service:
        summary = service.get_analytics_summary()
        return summary


@router.get("/messages/recent")
async def get_recent_messages(
    hours: int = Query(24, description="Number of hours to look back"),
    db: Session = Depends(get_database_session)
):
    """Get recent messages"""
    with WhatsAppService(db) as service:
        messages = service.get_recent_messages(hours)
        return {
            "hours": hours,
            "message_count": len(messages),
            "messages": messages
        }


# ============================================================================
# HEALTH CHECK
# ============================================================================

@router.get("/health/database")
async def database_health_check(db: Session = Depends(get_database_session)):
    """Check database connectivity and show table info"""
    try:
        with WhatsAppService(db) as service:
            # Try to get analytics summary to test DB connection
            summary = service.get_analytics_summary()
            
            return {
                "status": "healthy",
                "database": "postgresql",
                "tables": [
                    "user_profiles",
                    "whatsapp_messages", 
                    "business_metrics",
                    "message_templates"
                ],
                "metrics_summary": summary
            }
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Database health check failed: {str(e)}"
        )
