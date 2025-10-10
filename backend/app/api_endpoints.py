"""
API endpoints for user management, analytics, and message history.
These endpoints demonstrate the new PostgreSQL capabilities.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from app.core.database import get_database_session
from app.services.whatsapp_service import WhatsAppService
from app.models.user import UserCreate, UserResponse
from app.repositories.user_repository import UserRepository

router = APIRouter(prefix="/api", tags=["WhatsApp Business API"])

@router.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_database_session)
):
    """Create a new user manually"""
    from app.models.user import UserProfile
    from datetime import datetime
    
    user_repo = UserRepository(db)
    
    # Check if user already exists
    existing_user = user_repo.get_by_phone_number(user_data.whatsapp_phone)
    if existing_user:
        raise HTTPException(
            status_code=400, 
            detail=f"User with phone number {user_data.whatsapp_phone} already exists"
        )
    
    # Create user profile
    user_profile = UserProfile(
        whatsapp_phone=user_data.whatsapp_phone,
        display_name=user_data.display_name,
        business_name=user_data.business_name,
        email=user_data.email,
        customer_tier=user_data.customer_tier,
        tags=user_data.tags,
        notes=user_data.notes,
        first_contact=datetime.utcnow(),
        last_interaction=datetime.utcnow(),
        total_messages=0
    )
    
    # Create user in database
    created_user = user_repo.create(user_profile)
    
    # Return user response
    return UserResponse(
        id=str(created_user.id),
        whatsapp_phone=created_user.whatsapp_phone,
        display_name=created_user.display_name,
        business_name=created_user.business_name,
        email=created_user.email,
        customer_tier=created_user.customer_tier,
        tags=created_user.tags or [],
        total_messages=created_user.total_messages,
        last_interaction=created_user.last_interaction,
        is_active=created_user.is_active,
        subscription=created_user.subscription,
        subscription_updated_at=created_user.subscription_updated_at,
        created_at=created_user.created_at
    )

@router.get("/users/{phone_number}")
async def get_user_profile(
    phone_number: str,
    db: Session = Depends(get_database_session)
):
    """Get user profile by phone number"""
    with WhatsAppService(db) as service:
        user = service.get_user_profile(phone_number)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

@router.get("/users/{phone_number}/conversation")
async def get_user_conversation(
    phone_number: str,
    limit: int = Query(50, description="Number of messages to retrieve"),
    db: Session = Depends(get_database_session)
):
    """Get conversation history for a user"""
    with WhatsAppService(db) as service:
        messages = service.get_user_conversation(phone_number, limit)
        return {
            "phone_number": phone_number,
            "message_count": len(messages),
            "messages": messages
        }

@router.get("/users/search")
async def search_users(
    q: str = Query(..., description="Search query for business name"),
    db: Session = Depends(get_database_session)
):
    """Search users by business name"""
    with WhatsAppService(db) as service:
        users = service.search_users(q)
        return {
            "query": q,
            "results_count": len(users),
            "users": users
        }

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

@router.put("/users/{phone_number}")
async def update_user_profile(
    phone_number: str,
    update_data: dict,
    db: Session = Depends(get_database_session)
):
    """Update user profile"""
    with WhatsAppService(db) as service:
        updated_user = service.update_user_profile(phone_number, update_data)
        if not updated_user:
            raise HTTPException(status_code=404, detail="User not found")
        return updated_user

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
