"""
Analytics and reporting API endpoints.
Provides message analytics, metrics, and recent message history.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.core.database import get_database_session
from app.services.whatsapp_service import WhatsAppService

router = APIRouter(prefix="/analytics", tags=["Analytics & Reporting"])


@router.get("/daily")
async def get_daily_analytics(
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format"),
    db: Session = Depends(get_database_session)
):
    """
    Get analytics for a specific day
    
    Args:
        date: Date in YYYY-MM-DD format (defaults to today)
        
    Returns:
        Analytics data including message counts, users, etc.
    """
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


@router.get("/summary")
async def get_analytics_summary(db: Session = Depends(get_database_session)):
    """
    Get overall analytics summary
    
    Returns:
        Summary of all-time metrics including total messages, users, etc.
    """
    with WhatsAppService(db) as service:
        summary = service.get_analytics_summary()
        return summary


@router.get("/messages/recent")
async def get_recent_messages(
    hours: int = Query(24, description="Number of hours to look back", ge=1, le=720),
    db: Session = Depends(get_database_session)
):
    """
    Get recent messages
    
    Args:
        hours: Number of hours to look back (1-720, default: 24)
        
    Returns:
        List of recent messages with metadata
    """
    with WhatsAppService(db) as service:
        messages = service.get_recent_messages(hours)
        return {
            "hours": hours,
            "message_count": len(messages),
            "messages": messages
        }
