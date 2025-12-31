"""
Marketing Campaign API Endpoints
Manage marketing campaigns with rate limiting and duplicate prevention
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Optional, List
from datetime import date

from app.models.marketing import CampaignCreate, CampaignResponse, RecipientCreate, CampaignStats
from app.services.marketing_service import MarketingCampaignService
from app.core.logging import logger

router = APIRouter(prefix="/marketing", tags=["Marketing Campaigns"])


@router.post("/campaigns", response_model=dict)
async def create_campaign(request: CampaignCreate):
    """
    Create a new marketing campaign
    
    ## Example Request:
    ```json
    {
        "name": "Summer Sale 2025",
        "description": "Promotional campaign for summer sale",
        "template_name": "summer_sale_promo",
        "language_code": "en_US",
        "daily_send_limit": 250,
        "priority": 5,
        "target_audience": {
            "customer_tier": "premium",
            "tags": ["fashion", "accessories"]
        },
        "template_components": [
            {
                "type": "header",
                "parameters": [{
                    "type": "image",
                    "image": {"link": "https://example.com/sale-banner.jpg"}
                }]
            },
            {
                "type": "body",
                "parameters": [
                    {"type": "text", "text": "30%"}
                ]
            }
        ]
    }
    ```
    """
    try:
        result = MarketingCampaignService.create_campaign(
            name=request.name,
            template_name=request.template_name,
            description=request.description,
            language_code=request.language_code,
            target_audience=request.target_audience,
            daily_send_limit=request.daily_send_limit,
            priority=request.priority,
            scheduled_start_date=request.scheduled_start_date,
            scheduled_end_date=request.scheduled_end_date,
            template_components=request.template_components
        )
        
        return result
    except Exception as e:
        logger.error(f"❌ Error creating campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/campaigns/{campaign_id}/recipients", response_model=dict)
async def add_campaign_recipients(
    campaign_id: str,
    phone_numbers: Optional[List[str]] = None,
    use_target_audience: bool = Query(
        False,
        description="Auto-select recipients based on campaign's target audience"
    )
):
    """
    Add recipients to a campaign
    
    ## Option 1: Explicit phone numbers
    ```json
    {
        "phone_numbers": ["14694652751", "19453083188", ...]
    }
    ```
    
    ## Option 2: Use target audience
    Set `use_target_audience=true` in query params to automatically select
    all subscribed customers matching the campaign's target audience.
    
    **Note**: Only SUBSCRIBED users will be added. Unsubscribed users are automatically filtered out.
    """
    try:
        result = MarketingCampaignService.add_recipients_to_campaign(
            campaign_id=campaign_id,
            phone_numbers=phone_numbers,
            use_target_audience=use_target_audience
        )
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Error adding recipients: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/campaigns/{campaign_id}/activate", response_model=dict)
async def activate_campaign(
    campaign_id: str,
    start_date: Optional[date] = Query(
        None,
        description="Start date for sending (defaults to tomorrow)"
    )
):
    """
    Activate a campaign and create send schedule
    
    This will:
    1. Create a daily send schedule based on recipients and daily_send_limit
    2. Distribute recipients across days (max 250/day)
    3. Activate the campaign to start sending
    
    ## Example:
    - Campaign has 10,000 recipients
    - Daily limit is 250
    - Will create 40-day schedule starting from start_date
    """
    try:
        result = MarketingCampaignService.activate_campaign(
            campaign_id=campaign_id,
            start_date=start_date
        )
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Error activating campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/campaigns/{campaign_id}/pause", response_model=dict)
async def pause_campaign(campaign_id: str):
    """
    Pause an active campaign
    Paused campaigns will not send messages until resumed
    """
    try:
        result = MarketingCampaignService.pause_campaign(campaign_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Error pausing campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/campaigns/{campaign_id}/resume", response_model=dict)
async def resume_campaign(campaign_id: str):
    """
    Resume a paused campaign
    """
    try:
        result = MarketingCampaignService.resume_campaign(campaign_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Error resuming campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/campaigns/{campaign_id}/cancel", response_model=dict)
async def cancel_campaign(campaign_id: str):
    """
    Cancel a campaign
    Cancelled campaigns cannot be reactivated
    """
    try:
        result = MarketingCampaignService.cancel_campaign(campaign_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Error cancelling campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/campaigns/{campaign_id}/stats", response_model=dict)
async def get_campaign_stats(campaign_id: str):
    """
    Get campaign statistics and progress
    
    Returns:
    - Total targets
    - Messages sent/delivered/read/failed/pending
    - Progress percentage
    - Delivery and read rates
    - Estimated completion date
    """
    try:
        stats = MarketingCampaignService.get_campaign_stats(campaign_id)
        
        if not stats:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        return stats
    except Exception as e:
        logger.error(f"❌ Error getting campaign stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/campaigns", response_model=List[dict])
async def list_campaigns(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100, description="Max campaigns to return")
):
    """
    List all campaigns
    
    ## Filter by status:
    - draft
    - active
    - paused
    - completed
    - cancelled
    """
    try:
        campaigns = MarketingCampaignService.list_campaigns(
            status=status,
            limit=limit
        )
        
        return campaigns
    except Exception as e:
        logger.error(f"❌ Error listing campaigns: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process-daily", response_model=dict)
async def process_daily_campaigns():
    """
    Process today's campaigns and send scheduled messages
    
    **⚠️ This endpoint should be called by a scheduled job (cron/scheduler)**
    
    It will:
    1. Get today's send schedule
    2. Send messages to pending recipients (up to daily limit)
    3. Update recipient status
    4. Record analytics
    
    **Automated replies are NOT affected** - they continue working as normal.
    This only sends TEMPLATE MESSAGES for active marketing campaigns.
    """
    try:
        result = await MarketingCampaignService.process_daily_campaigns()
        return result
    except Exception as e:
        logger.error(f"❌ Error processing daily campaigns: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def marketing_health():
    """
    Health check for marketing service
    """
    try:
        from app.core.database import get_db_session
        from app.repositories.marketing_repository import MarketingCampaignRepository
        
        with get_db_session() as db:
            repo = MarketingCampaignRepository(db)
            active_campaigns = repo.get_active_campaigns()
        
        return {
            "service": "marketing",
            "status": "healthy",
            "active_campaigns": len(active_campaigns),
            "message": "Marketing service is operational"
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "service": "marketing",
                "status": "unhealthy",
                "error": str(e)
            }
        )


@router.post("/campaigns/{campaign_id}/reschedule-today")
async def reschedule_campaign_to_today(campaign_id: str):
    """
    Reschedule all pending recipients of a campaign to TODAY
    Useful for testing or urgent campaign launches
    """
    try:
        from app.core.database import get_db_session
        from app.repositories.marketing_repository import MarketingCampaignRepository
        from app.models.marketing import RecipientStatus
        import uuid
        from datetime import date
        
        with get_db_session() as db:
            repo = MarketingCampaignRepository(db)
            campaign_uuid = uuid.UUID(campaign_id)
            
            # Get all pending recipients
            from sqlalchemy import and_
            from app.models.marketing import CampaignRecipientDB, CampaignSendScheduleDB
            
            recipients = db.query(CampaignRecipientDB).filter(
                and_(
                    CampaignRecipientDB.campaign_id == campaign_uuid,
                    CampaignRecipientDB.status == RecipientStatus.PENDING.value
                )
            ).all()
            
            # Update their scheduled_send_date to today
            count = 0
            for recipient in recipients:
                recipient.scheduled_send_date = date.today()
                count += 1
            
            # Update schedule entries to today
            schedules = db.query(CampaignSendScheduleDB).filter(
                CampaignSendScheduleDB.campaign_id == campaign_uuid
            ).all()
            
            for schedule in schedules:
                schedule.send_date = date.today()
            
            db.commit()
            
            logger.info(f"✅ Rescheduled {count} recipients to today for campaign {campaign_id}")
            
            return JSONResponse({
                "message": f"Rescheduled {count} recipients to today",
                "campaign_id": campaign_id,
                "new_date": date.today().isoformat(),
                "recipients_updated": count
            })
            
    except Exception as e:
        logger.error(f"❌ Error rescheduling campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))
