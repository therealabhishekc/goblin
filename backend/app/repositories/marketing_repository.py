"""
Marketing Campaign Repository
Handles all database operations for marketing campaigns
"""
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, text
import uuid

from app.models.marketing import (
    MarketingCampaignDB, CampaignRecipientDB, CampaignSendScheduleDB, CampaignAnalyticsDB,
    CampaignStatus, RecipientStatus, ScheduleStatus
)
from app.repositories.base_repository import BaseRepository
from app.core.logging import logger


class MarketingCampaignRepository(BaseRepository[MarketingCampaignDB]):
    """Repository for marketing campaigns"""
    
    def __init__(self, db: Session):
        super().__init__(db, MarketingCampaignDB)
    
    def create_campaign(
        self,
        name: str,
        template_name: str,
        description: Optional[str] = None,
        language_code: str = "en_US",
        target_audience: Optional[Dict] = None,
        daily_send_limit: int = 250,
        priority: int = 5,
        scheduled_start_date: Optional[datetime] = None,
        scheduled_end_date: Optional[datetime] = None,
        template_components: Optional[List[Dict]] = None,
        created_by: Optional[str] = None
    ) -> MarketingCampaignDB:
        """Create a new marketing campaign"""
        campaign = MarketingCampaignDB(
            name=name,
            template_name=template_name,
            description=description,
            language_code=language_code,
            target_audience=target_audience,
            daily_send_limit=daily_send_limit,
            priority=priority,
            scheduled_start_date=scheduled_start_date,
            scheduled_end_date=scheduled_end_date,
            template_components=template_components,
            created_by=created_by,
            status=CampaignStatus.DRAFT.value
        )
        self.db.add(campaign)
        self.db.commit()
        self.db.refresh(campaign)
        logger.info(f"📊 Campaign created: {campaign.name} (ID: {campaign.id})")
        return campaign
    
    def get_campaign(self, campaign_id: uuid.UUID) -> Optional[MarketingCampaignDB]:
        """Get campaign by ID"""
        return self.db.query(MarketingCampaignDB).filter(
            MarketingCampaignDB.id == campaign_id
        ).first()
    
    def get_active_campaigns(self) -> List[MarketingCampaignDB]:
        """Get all active campaigns ordered by priority"""
        return self.db.query(MarketingCampaignDB).filter(
            MarketingCampaignDB.status == CampaignStatus.ACTIVE.value
        ).order_by(
            MarketingCampaignDB.priority.asc(),
            MarketingCampaignDB.created_at.asc()
        ).all()
    
    def update_campaign_status(
        self,
        campaign_id: uuid.UUID,
        status: CampaignStatus
    ) -> Optional[MarketingCampaignDB]:
        """Update campaign status"""
        campaign = self.get_campaign(campaign_id)
        if campaign:
            campaign.status = status.value
            if status == CampaignStatus.ACTIVE and not campaign.started_at:
                campaign.started_at = datetime.utcnow()
            elif status == CampaignStatus.COMPLETED:
                campaign.completed_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(campaign)
            logger.info(f"📊 Campaign {campaign.name} status updated: {status.value}")
        return campaign
    
    def add_recipients(
        self,
        campaign_id: uuid.UUID,
        phone_numbers: List[str],
        template_parameters: Optional[Dict] = None
    ) -> int:
        """
        Add recipients to a campaign
        Returns count of recipients added (skips duplicates)
        """
        campaign = self.get_campaign(campaign_id)
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")
        
        # Get existing recipients for this campaign
        existing = self.db.query(CampaignRecipientDB.phone_number).filter(
            CampaignRecipientDB.campaign_id == campaign_id
        ).all()
        existing_phones = {r.phone_number for r in existing}
        
        # Filter out duplicates
        new_phones = [p for p in phone_numbers if p not in existing_phones]
        
        if not new_phones:
            logger.warning(f"⚠️ No new recipients to add (all {len(phone_numbers)} already exist)")
            return 0
        
        # Create recipient records
        recipients = []
        for phone in new_phones:
            recipient = CampaignRecipientDB(
                campaign_id=campaign_id,
                phone_number=phone,
                status=RecipientStatus.PENDING.value,
                template_parameters=template_parameters
            )
            recipients.append(recipient)
        
        self.db.bulk_save_objects(recipients)
        
        # Update campaign total count
        campaign.total_target_customers += len(new_phones)
        campaign.messages_pending += len(new_phones)
        
        self.db.commit()
        logger.info(f"📊 Added {len(new_phones)} recipients to campaign {campaign.name} (skipped {len(phone_numbers) - len(new_phones)} duplicates)")
        return len(new_phones)
    
    def get_pending_recipients(
        self,
        campaign_id: uuid.UUID,
        limit: int = 250,
        scheduled_date: Optional[date] = None
    ) -> List[CampaignRecipientDB]:
        """
        Get pending recipients for sending
        If scheduled_date is provided, only get recipients for that date
        """
        query = self.db.query(CampaignRecipientDB).filter(
            and_(
                CampaignRecipientDB.campaign_id == campaign_id,
                CampaignRecipientDB.status == RecipientStatus.PENDING.value
            )
        )
        
        if scheduled_date:
            query = query.filter(CampaignRecipientDB.scheduled_send_date == scheduled_date)
        else:
            # Get recipients without scheduled date or scheduled for today
            query = query.filter(
                or_(
                    CampaignRecipientDB.scheduled_send_date.is_(None),
                    CampaignRecipientDB.scheduled_send_date <= date.today()
                )
            )
        
        return query.limit(limit).all()
    
    def update_recipient_status(
        self,
        recipient_id: uuid.UUID,
        status: RecipientStatus,
        whatsapp_message_id: Optional[str] = None,
        failure_reason: Optional[str] = None
    ) -> Optional[CampaignRecipientDB]:
        """Update recipient send status and campaign counters"""
        recipient = self.db.query(CampaignRecipientDB).filter(
            CampaignRecipientDB.id == recipient_id
        ).first()
        
        if recipient:
            old_status = recipient.status
            recipient.status = status.value
            
            # Get campaign for updating counters
            campaign = self.get_campaign(recipient.campaign_id)
            
            if status == RecipientStatus.QUEUED:
                # Message queued for sending
                recipient.whatsapp_message_id = whatsapp_message_id
            elif status == RecipientStatus.SENT:
                recipient.sent_at = datetime.utcnow()
                if whatsapp_message_id:
                    recipient.whatsapp_message_id = whatsapp_message_id
                # Update campaign counter only if status changed
                if campaign and old_status != RecipientStatus.SENT.value:
                    campaign.messages_sent += 1
                    if old_status == RecipientStatus.PENDING.value:
                        campaign.messages_pending -= 1
            elif status == RecipientStatus.DELIVERED:
                recipient.delivered_at = datetime.utcnow()
                # If sent_at not set, set it now
                if not recipient.sent_at:
                    recipient.sent_at = datetime.utcnow()
                # Update campaign counter only if status changed
                if campaign and old_status != RecipientStatus.DELIVERED.value:
                    campaign.messages_delivered += 1
                    # If jumping from pending/sent to delivered
                    if old_status == RecipientStatus.PENDING.value:
                        campaign.messages_pending -= 1
                        campaign.messages_sent += 1
                    elif old_status == RecipientStatus.SENT.value:
                        # Already counted in sent, just increment delivered
                        pass
            elif status == RecipientStatus.READ:
                recipient.read_at = datetime.utcnow()
                # If delivered_at not set, set it now
                if not recipient.delivered_at:
                    recipient.delivered_at = datetime.utcnow()
                # If sent_at not set, set it now
                if not recipient.sent_at:
                    recipient.sent_at = datetime.utcnow()
                # Update campaign counter only if status changed
                if campaign and old_status != RecipientStatus.READ.value:
                    campaign.messages_read += 1
                    # If jumping from pending/sent/delivered to read
                    if old_status == RecipientStatus.PENDING.value:
                        campaign.messages_pending -= 1
                        campaign.messages_sent += 1
                        campaign.messages_delivered += 1
                    elif old_status == RecipientStatus.SENT.value:
                        campaign.messages_delivered += 1
                    elif old_status == RecipientStatus.DELIVERED.value:
                        # Already counted in delivered, just increment read
                        pass
            elif status == RecipientStatus.FAILED:
                recipient.failed_at = datetime.utcnow()
                recipient.failure_reason = failure_reason
                recipient.retry_count += 1
                # Update campaign counter only if status changed
                if campaign and old_status != RecipientStatus.FAILED.value:
                    campaign.messages_failed += 1
                    if old_status == RecipientStatus.PENDING.value:
                        campaign.messages_pending -= 1
            elif status == RecipientStatus.SKIPPED:
                # User was skipped (e.g., unsubscribed)
                if failure_reason:
                    recipient.failure_reason = failure_reason
                # Update campaign counter
                if campaign and old_status == RecipientStatus.PENDING.value:
                    campaign.messages_pending -= 1
            
            self.db.commit()
            self.db.refresh(recipient)
            logger.info(f"📊 Updated recipient {recipient.phone_number}: {old_status} -> {status.value}")
        return recipient
    
    def schedule_campaign_sends(
        self,
        campaign_id: uuid.UUID,
        start_date: Optional[date] = None
    ) -> int:
        """
        Create send schedule for campaign
        Distributes recipients across days based on daily_send_limit
        Returns number of schedule entries created
        """
        campaign = self.get_campaign(campaign_id)
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")
        
        # Get all pending recipients without scheduled date
        pending_recipients = self.db.query(CampaignRecipientDB).filter(
            and_(
                CampaignRecipientDB.campaign_id == campaign_id,
                CampaignRecipientDB.status == RecipientStatus.PENDING.value,
                CampaignRecipientDB.scheduled_send_date.is_(None)
            )
        ).all()
        
        if not pending_recipients:
            logger.warning(f"⚠️ No pending recipients to schedule for campaign {campaign.name}")
            return 0
        
        # Start date defaults to TODAY (not tomorrow) for immediate sending
        if not start_date:
            start_date = date.today()
        
        # Schedule recipients in batches
        daily_limit = campaign.daily_send_limit
        total_recipients = len(pending_recipients)
        current_date = start_date
        scheduled_count = 0
        
        for i in range(0, total_recipients, daily_limit):
            batch = pending_recipients[i:i + daily_limit]
            
            # Update recipient scheduled dates
            for recipient in batch:
                recipient.scheduled_send_date = current_date
                scheduled_count += 1
            
            # Create schedule entry
            schedule = CampaignSendScheduleDB(
                campaign_id=campaign_id,
                send_date=current_date,
                batch_number=1,
                batch_size=len(batch),
                messages_remaining=len(batch),
                status=ScheduleStatus.PENDING.value
            )
            self.db.add(schedule)
            
            # Move to next day
            current_date += timedelta(days=1)
        
        self.db.commit()
        logger.info(f"📊 Scheduled {scheduled_count} recipients for campaign {campaign.name} over {(current_date - start_date).days} days")
        return scheduled_count
    
    def get_today_schedule(self) -> List[CampaignSendScheduleDB]:
        """Get today's send schedule"""
        return self.db.query(CampaignSendScheduleDB).filter(
            and_(
                CampaignSendScheduleDB.send_date == date.today(),
                CampaignSendScheduleDB.status.in_([ScheduleStatus.PENDING.value, ScheduleStatus.PROCESSING.value])
            )
        ).order_by(CampaignSendScheduleDB.created_at.asc()).all()
    
    def get_campaign_stats(self, campaign_id: uuid.UUID) -> Dict[str, Any]:
        """Get campaign statistics"""
        campaign = self.get_campaign(campaign_id)
        if not campaign:
            return {}
        
        # Calculate rates
        delivery_rate = None
        read_rate = None
        if campaign.messages_sent > 0:
            delivery_rate = round((campaign.messages_delivered / campaign.messages_sent) * 100, 2)
            read_rate = round((campaign.messages_read / campaign.messages_sent) * 100, 2)
        
        # Estimate completion date
        estimated_completion = None
        if campaign.status == CampaignStatus.ACTIVE.value and campaign.messages_pending > 0:
            days_remaining = (campaign.messages_pending // campaign.daily_send_limit) + 1
            estimated_completion = date.today() + timedelta(days=days_remaining)
        
        return {
            "campaign_id": str(campaign.id),
            "campaign_name": campaign.name,
            "status": campaign.status,
            "total_target": campaign.total_target_customers,
            "sent": campaign.messages_sent,
            "delivered": campaign.messages_delivered,
            "read": campaign.messages_read,
            "failed": campaign.messages_failed,
            "pending": campaign.messages_pending,
            "progress_percentage": round((campaign.messages_sent / campaign.total_target_customers) * 100, 2) if campaign.total_target_customers > 0 else 0,
            "delivery_rate": delivery_rate,
            "read_rate": read_rate,
            "estimated_completion_date": estimated_completion
        }
    
    def check_duplicate_send(self, campaign_id: uuid.UUID, phone_number: str) -> bool:
        """
        Check if a message has already been sent to this phone number in this campaign
        Returns True if already sent, False otherwise
        """
        existing = self.db.query(CampaignRecipientDB).filter(
            and_(
                CampaignRecipientDB.campaign_id == campaign_id,
                CampaignRecipientDB.phone_number == phone_number,
                CampaignRecipientDB.status.in_([
                    RecipientStatus.SENT.value,
                    RecipientStatus.DELIVERED.value,
                    RecipientStatus.READ.value
                ])
            )
        ).first()
        
        return existing is not None
    
    def get_subscribed_customers(
        self,
        target_audience: Optional[Dict] = None,
        limit: Optional[int] = None
    ) -> List[str]:
        """
        Get list of subscribed customer phone numbers
        Optionally filter by target audience criteria
        """
        from app.models.user import UserProfileDB
        
        query = self.db.query(UserProfileDB.whatsapp_phone).filter(
            and_(
                UserProfileDB.subscription == "subscribed",
                UserProfileDB.is_active == True
            )
        )
        
        # Apply target audience filters if provided
        if target_audience:
            if "customer_tier" in target_audience:
                query = query.filter(UserProfileDB.customer_tier == target_audience["customer_tier"])
            
            if "tags" in target_audience:
                # Customer has any of the specified tags
                for tag in target_audience["tags"]:
                    query = query.filter(UserProfileDB.tags.contains([tag]))
        
        if limit:
            query = query.limit(limit)
        
        results = query.all()
        return [r.whatsapp_phone for r in results]
    
    def record_analytics(
        self,
        campaign_id: uuid.UUID,
        analytics_date: date
    ) -> CampaignAnalyticsDB:
        """Record daily analytics for campaign"""
        # Get or create analytics record
        analytics = self.db.query(CampaignAnalyticsDB).filter(
            and_(
                CampaignAnalyticsDB.campaign_id == campaign_id,
                CampaignAnalyticsDB.date == analytics_date
            )
        ).first()
        
        if not analytics:
            analytics = CampaignAnalyticsDB(
                campaign_id=campaign_id,
                date=analytics_date
            )
            self.db.add(analytics)
        
        # Calculate metrics for the day
        stats = self.db.query(
            func.count(CampaignRecipientDB.id).filter(
                CampaignRecipientDB.status == RecipientStatus.SENT.value
            ).label('sent'),
            func.count(CampaignRecipientDB.id).filter(
                CampaignRecipientDB.status == RecipientStatus.DELIVERED.value
            ).label('delivered'),
            func.count(CampaignRecipientDB.id).filter(
                CampaignRecipientDB.status == RecipientStatus.READ.value
            ).label('read'),
            func.count(CampaignRecipientDB.id).filter(
                CampaignRecipientDB.status == RecipientStatus.FAILED.value
            ).label('failed')
        ).filter(
            and_(
                CampaignRecipientDB.campaign_id == campaign_id,
                func.date(CampaignRecipientDB.sent_at) == analytics_date
            )
        ).first()
        
        if stats:
            analytics.messages_sent = stats.sent or 0
            analytics.messages_delivered = stats.delivered or 0
            analytics.messages_read = stats.read or 0
            analytics.messages_failed = stats.failed or 0
            
            # Calculate rates
            if analytics.messages_sent > 0:
                analytics.delivery_rate = round((analytics.messages_delivered / analytics.messages_sent) * 100, 2)
                analytics.read_rate = round((analytics.messages_read / analytics.messages_sent) * 100, 2)
        
        self.db.commit()
        self.db.refresh(analytics)
        return analytics
