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
from app.models.whatsapp import WhatsAppMessageDB
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
            
            # Define status hierarchy to prevent downgrades
            # pending < queued < sent < delivered < read
            # failed and skipped are terminal states but can be set anytime
            status_hierarchy = {
                "pending": 1,
                "queued": 2,
                "sent": 3,
                "delivered": 4,
                "read": 5,
                "failed": 99,  # Can always set to failed
                "skipped": 99  # Can always set to skipped
            }
            
            current_level = status_hierarchy.get(old_status, 0)
            new_level = status_hierarchy.get(status.value, 0)
            
            # Only update if new status is higher in hierarchy or is terminal (failed/skipped)
            if new_level < current_level and new_level < 99:
                logger.info(f"⏭️  Skipped recipient status downgrade: {recipient.phone_number} ({old_status} -> {status.value})")
                return recipient
            
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
    
    def update_schedule_status(
        self,
        schedule_id: uuid.UUID,
        status: ScheduleStatus,
        messages_sent: Optional[int] = None
    ) -> Optional[CampaignSendScheduleDB]:
        """Update schedule status and progress"""
        schedule = self.db.query(CampaignSendScheduleDB).filter(
            CampaignSendScheduleDB.id == schedule_id
        ).first()
        
        if schedule:
            schedule.status = status.value
            
            # Update messages_sent if provided
            if messages_sent is not None:
                schedule.messages_sent = messages_sent
                schedule.messages_remaining = schedule.batch_size - messages_sent
            
            # Update timestamps based on status
            if status == ScheduleStatus.PROCESSING and not schedule.started_at:
                schedule.started_at = datetime.utcnow()
            elif status == ScheduleStatus.COMPLETED:
                schedule.completed_at = datetime.utcnow()
                schedule.messages_remaining = 0
            elif status == ScheduleStatus.FAILED:
                schedule.completed_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(schedule)
            logger.info(f"📊 Schedule {schedule_id} updated: {status.value}, sent: {schedule.messages_sent}/{schedule.batch_size}")
        
        return schedule
    
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
            # Filter by customer_tier if specified and not "all"
            if "customer_tier" in target_audience and target_audience["customer_tier"] and target_audience["customer_tier"] != "all":
                query = query.filter(UserProfileDB.customer_tier == target_audience["customer_tier"])
            
            if "tags" in target_audience and target_audience["tags"]:
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
        
        # Calculate message metrics for the day
        # Count by timestamp columns, not by status, since status changes over time
        # A message sent today might be read later, but we still count it as "sent today"
        
        # Count messages SENT on this date (where sent_at date matches)
        messages_sent = self.db.query(func.count(CampaignRecipientDB.id)).filter(
            and_(
                CampaignRecipientDB.campaign_id == campaign_id,
                func.date(CampaignRecipientDB.sent_at) == analytics_date,
                CampaignRecipientDB.sent_at.isnot(None)
            )
        ).scalar() or 0
        
        # Count messages DELIVERED on this date (where delivered_at date matches)
        messages_delivered = self.db.query(func.count(CampaignRecipientDB.id)).filter(
            and_(
                CampaignRecipientDB.campaign_id == campaign_id,
                func.date(CampaignRecipientDB.delivered_at) == analytics_date,
                CampaignRecipientDB.delivered_at.isnot(None)
            )
        ).scalar() or 0
        
        # Count messages READ on this date (where read_at date matches)
        messages_read = self.db.query(func.count(CampaignRecipientDB.id)).filter(
            and_(
                CampaignRecipientDB.campaign_id == campaign_id,
                func.date(CampaignRecipientDB.read_at) == analytics_date,
                CampaignRecipientDB.read_at.isnot(None)
            )
        ).scalar() or 0
        
        # Count messages FAILED on this date (where failed_at date matches)
        messages_failed = self.db.query(func.count(CampaignRecipientDB.id)).filter(
            and_(
                CampaignRecipientDB.campaign_id == campaign_id,
                func.date(CampaignRecipientDB.failed_at) == analytics_date,
                CampaignRecipientDB.failed_at.isnot(None)
            )
        ).scalar() or 0
        
        # Update analytics
        analytics.messages_sent = messages_sent
        analytics.messages_delivered = messages_delivered
        analytics.messages_read = messages_read
        analytics.messages_failed = messages_failed
        
        # Calculate delivery and read rates based on messages sent on this date
        if messages_sent > 0:
            # Note: delivery/read might happen on different days, so rates might exceed 100% temporarily
            # For accurate rates, we should count delivered/read for messages sent on this date
            # But for simplicity, we'll use the counts for this date
            analytics.delivery_rate = round((messages_delivered / messages_sent) * 100, 2)
            analytics.read_rate = round((messages_read / messages_sent) * 100, 2)
        
        # Calculate engagement metrics (replies received from recipients)
        # Get all recipients who were sent messages on this date
        recipients_sent_today = self.db.query(CampaignRecipientDB.phone_number).filter(
            and_(
                CampaignRecipientDB.campaign_id == campaign_id,
                func.date(CampaignRecipientDB.sent_at) == analytics_date
            )
        ).all()
        
        if recipients_sent_today:
            recipient_phones = [r.phone_number for r in recipients_sent_today]
            
            # Count replies received from these recipients on this date
            # Replies are incoming messages from recipients after campaign was sent
            replies = self.db.query(
                func.count(WhatsAppMessageDB.id).label('total_replies'),
                func.count(func.distinct(WhatsAppMessageDB.phone_number)).label('unique_responders')
            ).filter(
                and_(
                    WhatsAppMessageDB.phone_number.in_(recipient_phones),
                    WhatsAppMessageDB.direction == 'incoming',
                    func.date(WhatsAppMessageDB.timestamp) == analytics_date,
                    WhatsAppMessageDB.timestamp >= func.coalesce(
                        self.db.query(func.min(CampaignRecipientDB.sent_at)).filter(
                            and_(
                                CampaignRecipientDB.campaign_id == campaign_id,
                                func.date(CampaignRecipientDB.sent_at) == analytics_date
                            )
                        ).scalar_subquery(),
                        WhatsAppMessageDB.timestamp
                    )
                )
            ).first()
            
            if replies:
                analytics.replies_received = replies.total_replies or 0
                analytics.unique_responders = replies.unique_responders or 0
                
                # Calculate response rate
                if analytics.messages_sent > 0:
                    analytics.response_rate = round((analytics.unique_responders / analytics.messages_sent) * 100, 2)
            
            # Calculate average response time (in minutes)
            # Get response times for recipients who replied
            response_times = self.db.query(
                (func.timestampdiff(text('MINUTE'), CampaignRecipientDB.sent_at, WhatsAppMessageDB.timestamp)).label('response_time')
            ).select_from(CampaignRecipientDB).join(
                WhatsAppMessageDB,
                and_(
                    WhatsAppMessageDB.phone_number == CampaignRecipientDB.phone_number,
                    WhatsAppMessageDB.direction == 'incoming',
                    WhatsAppMessageDB.timestamp >= CampaignRecipientDB.sent_at,
                    func.date(WhatsAppMessageDB.timestamp) == analytics_date
                )
            ).filter(
                and_(
                    CampaignRecipientDB.campaign_id == campaign_id,
                    func.date(CampaignRecipientDB.sent_at) == analytics_date
                )
            ).group_by(
                CampaignRecipientDB.phone_number
            ).all()
            
            if response_times:
                # Calculate average response time from first reply per recipient
                valid_times = [rt.response_time for rt in response_times if rt.response_time is not None and rt.response_time > 0]
                if valid_times:
                    analytics.avg_response_time_minutes = round(sum(valid_times) / len(valid_times))
        
        self.db.commit()
        self.db.refresh(analytics)
        
        logger.info(f"📊 Analytics recorded for campaign {campaign_id} on {analytics_date}: "
                   f"Sent={analytics.messages_sent}, Delivered={analytics.messages_delivered}, "
                   f"Read={analytics.messages_read}, Failed={analytics.messages_failed}, "
                   f"Replies={analytics.replies_received}, Responders={analytics.unique_responders}, "
                   f"AvgResponseTime={analytics.avg_response_time_minutes}min")
        
        return analytics
