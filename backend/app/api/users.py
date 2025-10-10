"""
User Management API Endpoints
Provides CRUD operations, search, bulk import, and analytics for WhatsApp users
"""
from fastapi import APIRouter, Depends, HTTPException, Query, File, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import csv
import io

from app.core.database import get_database_session
from app.services.whatsapp_service import WhatsAppService
from app.models.user import UserCreate, UserResponse, UserProfile
from app.repositories.user_repository import UserRepository
from app.core.logging import logger

router = APIRouter(prefix="/api/users", tags=["User Management"])


# ============================================================================
# USER CRUD OPERATIONS
# ============================================================================

@router.post("", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_database_session)
):
    """
    Create a new user manually
    
    Used by: AddUserForm.js
    
    Example:
    ```json
    {
        "whatsapp_phone": "+1234567890",
        "display_name": "John Doe",
        "business_name": "Doe's Store",
        "email": "john@example.com",
        "customer_tier": "premium",
        "tags": ["vip", "regular"],
        "notes": "Great customer"
    }
    ```
    """
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
    
    try:
        # Create user in database
        created_user = user_repo.create(user_profile)
        
        logger.info(f"✅ Created user: {created_user.whatsapp_phone}")
        
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
    except Exception as e:
        logger.error(f"❌ Failed to create user: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")


@router.get("/{phone_number}")
async def get_user_profile(
    phone_number: str,
    db: Session = Depends(get_database_session)
):
    """
    Get user profile by phone number
    
    Used by: UpdateUserForm.js (search functionality)
    
    Example:
    ```
    GET /api/users/+1234567890
    ```
    """
    try:
        with WhatsAppService(db) as service:
            user = service.get_user_profile(phone_number)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            logger.info(f"📋 Retrieved user profile: {phone_number}")
            return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get user profile: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get user: {str(e)}")


@router.put("/{phone_number}")
async def update_user_profile(
    phone_number: str,
    update_data: dict,
    db: Session = Depends(get_database_session)
):
    """
    Update user profile
    
    Used by: UpdateUserForm.js (update functionality)
    
    Example:
    ```json
    {
        "display_name": "John Smith",
        "customer_tier": "vip",
        "tags": ["vip", "loyal"],
        "notes": "Upgraded to VIP"
    }
    ```
    """
    try:
        with WhatsAppService(db) as service:
            updated_user = service.update_user_profile(phone_number, update_data)
            if not updated_user:
                raise HTTPException(status_code=404, detail="User not found")
            
            logger.info(f"✏️ Updated user profile: {phone_number}")
            return updated_user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to update user: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update user: {str(e)}")


@router.delete("/{phone_number}")
async def delete_user(
    phone_number: str,
    db: Session = Depends(get_database_session)
):
    """
    Delete user by phone number
    
    Note: This is a soft delete - sets is_active to False
    """
    try:
        user_repo = UserRepository(db)
        user = user_repo.get_by_phone_number(phone_number)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Soft delete - set is_active to False
        user_repo.update(user.id, {"is_active": False})
        
        logger.info(f"🗑️ Deleted user: {phone_number}")
        
        return {
            "success": True,
            "message": f"User {phone_number} deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to delete user: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete user: {str(e)}")


# ============================================================================
# USER SEARCH & LISTING
# ============================================================================

@router.get("")
async def list_users(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    customer_tier: Optional[str] = Query(None, description="Filter by customer tier"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_database_session)
):
    """
    List all users with pagination and filters
    
    Query Parameters:
    - skip: Number of records to skip (default: 0)
    - limit: Maximum records to return (default: 100, max: 1000)
    - customer_tier: Filter by tier (regular, premium, vip)
    - is_active: Filter by active status
    """
    try:
        user_repo = UserRepository(db)
        
        # Get all users with pagination
        users = user_repo.get_all(skip=skip, limit=limit)
        
        # Apply filters
        if customer_tier:
            users = [u for u in users if u.customer_tier == customer_tier]
        if is_active is not None:
            users = [u for u in users if u.is_active == is_active]
        
        logger.info(f"📋 Listed {len(users)} users")
        
        return {
            "total": len(users),
            "skip": skip,
            "limit": limit,
            "users": [
                {
                    "id": str(u.id),
                    "whatsapp_phone": u.whatsapp_phone,
                    "display_name": u.display_name,
                    "business_name": u.business_name,
                    "customer_tier": u.customer_tier,
                    "tags": u.tags or [],
                    "is_active": u.is_active,
                    "total_messages": u.total_messages,
                    "last_interaction": u.last_interaction.isoformat() if u.last_interaction else None
                }
                for u in users
            ]
        }
    except Exception as e:
        logger.error(f"❌ Failed to list users: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list users: {str(e)}")


@router.get("/search/query")
async def search_users(
    q: str = Query(..., min_length=1, description="Search query for business name or display name"),
    db: Session = Depends(get_database_session)
):
    """
    Search users by business name or display name
    
    Used by: Search features in frontend
    
    Example:
    ```
    GET /api/users/search/query?q=Doe's
    ```
    """
    try:
        with WhatsAppService(db) as service:
            users = service.search_users(q)
            
            logger.info(f"🔍 Search for '{q}' found {len(users)} users")
            
            return {
                "query": q,
                "results_count": len(users),
                "users": users
            }
    except Exception as e:
        logger.error(f"❌ Failed to search users: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to search users: {str(e)}")


# ============================================================================
# BULK IMPORT
# ============================================================================

@router.post("/bulk-import")
async def bulk_import_users(
    file: UploadFile = File(...),
    db: Session = Depends(get_database_session)
):
    """
    Bulk import users from CSV file
    
    Used by: BulkImportUsers.js
    
    CSV Format:
    ```csv
    whatsapp_phone,display_name,business_name,email,customer_tier,tags,notes
    +1234567890,John Doe,Doe's Store,john@example.com,premium,"vip,regular",Great customer
    ```
    
    Returns:
    - total: Total rows processed
    - success: Number of successfully imported users
    - failed: Number of failed imports
    - skipped: Number of skipped (duplicate) users
    - errors: List of errors with row numbers
    - created_users: List of successfully created users
    """
    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted")
    
    logger.info(f"📥 Starting bulk import from file: {file.filename}")
    
    try:
        # Read CSV file
        contents = await file.read()
        csv_file = io.StringIO(contents.decode('utf-8'))
        csv_reader = csv.DictReader(csv_file)
        
        user_repo = UserRepository(db)
        results = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "skipped": 0,
            "errors": [],
            "created_users": []
        }
        
        for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 (header is row 1)
            results["total"] += 1
            
            try:
                # Validate required field
                phone = row.get('whatsapp_phone', '').strip()
                if not phone:
                    results["failed"] += 1
                    results["errors"].append({
                        "row": row_num,
                        "error": "Missing required field: whatsapp_phone"
                    })
                    continue
                
                # Check if user already exists
                existing_user = user_repo.get_by_phone_number(phone)
                if existing_user:
                    results["skipped"] += 1
                    results["errors"].append({
                        "row": row_num,
                        "phone": phone,
                        "error": "User already exists"
                    })
                    continue
                
                # Parse tags (comma-separated in quotes or plain)
                tags_str = row.get('tags', '').strip()
                tags = []
                if tags_str:
                    # Remove quotes if present
                    tags_str = tags_str.strip('"').strip("'")
                    tags = [tag.strip() for tag in tags_str.split(',') if tag.strip()]
                
                # Create user profile
                user_profile = UserProfile(
                    whatsapp_phone=phone,
                    display_name=row.get('display_name', '').strip() or None,
                    business_name=row.get('business_name', '').strip() or None,
                    email=row.get('email', '').strip() or None,
                    customer_tier=row.get('customer_tier', 'regular').strip() or 'regular',
                    tags=tags if tags else [],
                    notes=row.get('notes', '').strip() or None,
                    subscription=row.get('subscription', 'subscribed').strip() or 'subscribed',
                    first_contact=datetime.utcnow(),
                    last_interaction=datetime.utcnow(),
                    total_messages=0
                )
                
                # Create user in database
                created_user = user_repo.create(user_profile)
                
                results["success"] += 1
                results["created_users"].append({
                    "row": row_num,
                    "phone": phone,
                    "name": created_user.display_name or created_user.business_name or phone
                })
                
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({
                    "row": row_num,
                    "phone": row.get('whatsapp_phone', 'N/A'),
                    "error": str(e)
                })
        
        logger.info(f"✅ Bulk import completed: {results['success']} created, {results['skipped']} skipped, {results['failed']} failed")
        
        return {
            "status": "completed",
            "message": f"Processed {results['total']} rows: {results['success']} created, {results['skipped']} skipped, {results['failed']} failed",
            **results
        }
        
    except Exception as e:
        logger.error(f"❌ Bulk import failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process CSV file: {str(e)}"
        )


# ============================================================================
# USER CONVERSATION & MESSAGES
# ============================================================================

@router.get("/{phone_number}/conversation")
async def get_user_conversation(
    phone_number: str,
    limit: int = Query(50, ge=1, le=500, description="Number of messages to retrieve"),
    db: Session = Depends(get_database_session)
):
    """
    Get conversation history for a specific user
    
    Used by: Conversation viewer
    
    Returns both incoming and outgoing messages ordered chronologically
    """
    try:
        with WhatsAppService(db) as service:
            messages = service.get_user_conversation(phone_number, limit)
            
            logger.info(f"💬 Retrieved {len(messages)} messages for {phone_number}")
            
            return {
                "phone_number": phone_number,
                "message_count": len(messages),
                "messages": messages
            }
    except Exception as e:
        logger.error(f"❌ Failed to get conversation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get conversation: {str(e)}")


@router.get("/{phone_number}/stats")
async def get_user_stats(
    phone_number: str,
    db: Session = Depends(get_database_session)
):
    """
    Get statistics for a specific user
    
    Returns:
    - Total messages sent/received
    - Last interaction time
    - Average response time
    - Most active hours
    """
    try:
        user_repo = UserRepository(db)
        user = user_repo.get_by_phone_number(phone_number)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        with WhatsAppService(db) as service:
            messages = service.get_user_conversation(phone_number, limit=1000)
        
        # Calculate stats
        incoming = [m for m in messages if m.get('direction') == 'incoming']
        outgoing = [m for m in messages if m.get('direction') == 'outgoing']
        
        stats = {
            "phone_number": phone_number,
            "display_name": user.display_name,
            "business_name": user.business_name,
            "customer_tier": user.customer_tier,
            "total_messages": user.total_messages,
            "messages_received": len(incoming),
            "messages_sent": len(outgoing),
            "first_contact": user.first_contact.isoformat() if user.first_contact else None,
            "last_interaction": user.last_interaction.isoformat() if user.last_interaction else None,
            "is_active": user.is_active,
            "subscription": user.subscription,
            "tags": user.tags or []
        }
        
        logger.info(f"📊 Retrieved stats for {phone_number}")
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get user stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


# ============================================================================
# USER TAGS & SUBSCRIPTION
# ============================================================================

@router.post("/{phone_number}/tags")
async def add_tags(
    phone_number: str,
    tags: List[str],
    db: Session = Depends(get_database_session)
):
    """
    Add tags to a user
    
    Example:
    ```json
    {
        "tags": ["vip", "loyal", "premium"]
    }
    ```
    """
    try:
        user_repo = UserRepository(db)
        user = user_repo.get_by_phone_number(phone_number)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Merge existing tags with new tags (unique)
        existing_tags = set(user.tags or [])
        new_tags = existing_tags.union(set(tags))
        
        user_repo.update(user.id, {"tags": list(new_tags)})
        
        logger.info(f"🏷️ Added tags to {phone_number}: {tags}")
        
        return {
            "success": True,
            "phone_number": phone_number,
            "tags": list(new_tags)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to add tags: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add tags: {str(e)}")


@router.delete("/{phone_number}/tags")
async def remove_tags(
    phone_number: str,
    tags: List[str],
    db: Session = Depends(get_database_session)
):
    """Remove specific tags from a user"""
    try:
        user_repo = UserRepository(db)
        user = user_repo.get_by_phone_number(phone_number)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Remove specified tags
        existing_tags = set(user.tags or [])
        remaining_tags = existing_tags - set(tags)
        
        user_repo.update(user.id, {"tags": list(remaining_tags)})
        
        logger.info(f"🏷️ Removed tags from {phone_number}: {tags}")
        
        return {
            "success": True,
            "phone_number": phone_number,
            "tags": list(remaining_tags)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to remove tags: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to remove tags: {str(e)}")


@router.post("/{phone_number}/subscribe")
async def subscribe_user(
    phone_number: str,
    db: Session = Depends(get_database_session)
):
    """Subscribe user to template messages"""
    try:
        user_repo = UserRepository(db)
        user = user_repo.resubscribe_user(phone_number)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        logger.info(f"✅ User subscribed: {phone_number}")
        
        return {
            "success": True,
            "phone_number": phone_number,
            "subscription": "subscribed"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to subscribe user: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to subscribe: {str(e)}")


@router.post("/{phone_number}/unsubscribe")
async def unsubscribe_user(
    phone_number: str,
    db: Session = Depends(get_database_session)
):
    """Unsubscribe user from template messages"""
    try:
        user_repo = UserRepository(db)
        user = user_repo.unsubscribe_user(phone_number)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        logger.info(f"📵 User unsubscribed: {phone_number}")
        
        return {
            "success": True,
            "phone_number": phone_number,
            "subscription": "unsubscribed"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to unsubscribe user: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to unsubscribe: {str(e)}")
