"""
API endpoints for archived data retrieval
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from datetime import datetime, timedelta
from app.services.s3_service import get_s3_service
from app.core.logging import logger

router = APIRouter(prefix="/api/v1/archive", tags=["archive"])

@router.get("/messages")
async def get_archived_messages(
    phone_number: Optional[str] = Query(None, description="Filter by phone number"),
    days_back: int = Query(30, description="Number of days to look back"),
    limit: int = Query(100, description="Maximum number of messages to return")
):
    """Retrieve archived messages from S3"""
    try:
        s3_service = get_s3_service()
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        messages = await s3_service.retrieve_archived_messages(
            phone_number=phone_number,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        
        return {
            "success": True,
            "data": messages,
            "count": len(messages),
            "filters": {
                "phone_number": phone_number,
                "days_back": days_back,
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to retrieve archived messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversations/{phone_number}")
async def get_archived_conversation(
    phone_number: str,
    days_back: int = Query(30, description="Number of days to look back")
):
    """Get archived conversation history for a specific phone number"""
    try:
        s3_service = get_s3_service()
        
        messages = await s3_service.search_archived_conversations(
            phone_number=phone_number,
            days_back=days_back
        )
        
        return {
            "success": True,
            "phone_number": phone_number,
            "messages": messages,
            "count": len(messages),
            "days_back": days_back
        }
        
    except Exception as e:
        logger.error(f"Failed to retrieve conversation for {phone_number}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/media/{message_id}")
async def get_archived_media(message_id: str):
    """Retrieve archived media file by message ID"""
    try:
        s3_service = get_s3_service()
        
        media_data = await s3_service.retrieve_archived_media(message_id)
        
        if not media_data:
            raise HTTPException(status_code=404, detail="Media not found")
        
        # Return media data (you might want to stream this for large files)
        return {
            "success": True,
            "message_id": message_id,
            "media_size_bytes": len(media_data),
            "note": "Use streaming endpoint for large files"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve media for message {message_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_storage_stats():
    """Get statistics about archived data storage"""
    try:
        s3_service = get_s3_service()
        stats = await s3_service.get_storage_statistics()
        
        return {
            "success": True,
            "storage_statistics": stats
        }
        
    except Exception as e:
        logger.error(f"Failed to get storage statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test-connection")
async def test_s3_connection():
    """Test S3 connection and permissions"""
    try:
        s3_service = get_s3_service()
        result = s3_service.validate_connection()
        
        if result['connected'] and result['bucket_exists'] and result['permissions_valid']:
            return {
                "success": True,
                "message": "S3 connection is working properly",
                "details": result
            }
        else:
            return {
                "success": False,
                "message": "S3 connection has issues",
                "details": result
            }
            
    except Exception as e:
        logger.error(f"S3 connection test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
