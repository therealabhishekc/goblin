"""
Marketing Campaign Service
Business logic for sending marketing messages with rate limiting
"""
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
import uuid

from app.repositories.marketing_repository import MarketingCampaignRepository
from app.repositories.user_repository import UserRepository
from app.models.marketing import CampaignStatus, RecipientStatus, ScheduleStatus
from app.services.sqs_service import send_outgoing_message
from app.core.logging import logger
from app.core.database import get_db_session


class MarketingCampaignService:
    """Service for managing marketing campaigns"""
    
    @staticmethod
    def create_campaign(
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
    ) -> Dict[str, Any]:
        """
        Create a new marketing campaign
        Note: scheduled_start_date and scheduled_end_date will be auto-populated
        during activation if not provided during creation.
        """
        with get_db_session() as db:
            repo = MarketingCampaignRepository(db)
            
            # Create campaign
            campaign = repo.create_campaign(
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
                created_by=created_by
            )
            
            logger.info(f"✅ Campaign created: {campaign.name} (ID: {campaign.id})")
            
            return {
                "id": str(campaign.id),
                "name": campaign.name,
                "status": campaign.status,
                "template_name": campaign.template_name,
                "message": f"Campaign '{campaign.name}' created successfully"
            }
    
    @staticmethod
    def add_recipients_to_campaign(
        campaign_id: str,
        phone_numbers: Optional[List[str]] = None,
        use_target_audience: bool = False,
        template_parameters: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Add recipients to a campaign
        Either provide explicit phone_numbers OR use_target_audience=True
        """
        with get_db_session() as db:
            repo = MarketingCampaignRepository(db)
            
            campaign_uuid = uuid.UUID(campaign_id)
            campaign = repo.get_campaign(campaign_uuid)
            
            if not campaign:
                raise ValueError(f"Campaign {campaign_id} not found")
            
            # Get phone numbers based on input
            if use_target_audience:
                # Get subscribed customers based on target audience
                phone_numbers = repo.get_subscribed_customers(
                    target_audience=campaign.target_audience
                )
                logger.info(f"📊 Found {len(phone_numbers)} subscribed customers matching target audience")
            
            if not phone_numbers:
                raise ValueError("No phone numbers provided and no customers match target audience")
            
            # Add recipients
            added_count = repo.add_recipients(
                campaign_id=campaign_uuid,
                phone_numbers=phone_numbers,
                template_parameters=template_parameters
            )
            
            return {
                "campaign_id": campaign_id,
                "recipients_added": added_count,
                "total_recipients": campaign.total_target_customers,
                "message": f"Added {added_count} recipients to campaign"
            }
    
    @staticmethod
    def activate_campaign(
        campaign_id: str,
        start_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Activate a campaign and create send schedule
        """
        with get_db_session() as db:
            repo = MarketingCampaignRepository(db)
            
            campaign_uuid = uuid.UUID(campaign_id)
            campaign = repo.get_campaign(campaign_uuid)
            
            if not campaign:
                raise ValueError(f"Campaign {campaign_id} not found")
            
            if campaign.total_target_customers == 0:
                raise ValueError("Campaign has no recipients. Add recipients before activating.")
            
            # Default to today if no start_date provided
            if not start_date:
                start_date = date.today()
            
            # Calculate estimated duration
            days_to_complete = (campaign.total_target_customers // campaign.daily_send_limit) + 1
            estimated_completion = start_date + timedelta(days=days_to_complete)
            
            # Update campaign with scheduled dates
            campaign.scheduled_start_date = datetime.combine(start_date, datetime.min.time())
            campaign.scheduled_end_date = datetime.combine(estimated_completion, datetime.min.time())
            db.commit()
            db.refresh(campaign)
            
            # Create send schedule
            scheduled_count = repo.schedule_campaign_sends(
                campaign_id=campaign_uuid,
                start_date=start_date
            )
            
            # Activate campaign
            repo.update_campaign_status(campaign_uuid, CampaignStatus.ACTIVE)
            
            logger.info(f"✅ Campaign activated: {campaign.name}")
            logger.info(f"📊 {scheduled_count} recipients scheduled over {days_to_complete} days")
            logger.info(f"📅 Schedule: {start_date} to {estimated_completion}")
            
            return {
                "campaign_id": campaign_id,
                "status": "active",
                "recipients_scheduled": scheduled_count,
                "daily_limit": campaign.daily_send_limit,
                "estimated_days": days_to_complete,
                "scheduled_start_date": start_date.isoformat(),
                "estimated_completion_date": estimated_completion.isoformat(),
                "message": f"Campaign activated. Sending {campaign.daily_send_limit} messages/day starting {start_date}"
            }
    
    @staticmethod
    async def process_daily_campaigns() -> Dict[str, Any]:
        """
        Process today's campaigns - send messages according to schedule
        This should be run by a scheduled job/worker
        """
        with get_db_session() as db:
            repo = MarketingCampaignRepository(db)
            
            # Get today's schedule
            schedules = repo.get_today_schedule()
            
            total_sent = 0
            campaigns_processed = 0
            
            # Process scheduled campaigns
            if schedules:
                for schedule in schedules:
                try:
                    # Update schedule status to PROCESSING
                    repo.update_schedule_status(schedule.id, ScheduleStatus.PROCESSING)
                    
                    # Get campaign
                    campaign = repo.get_campaign(schedule.campaign_id)
                    if not campaign or campaign.status != CampaignStatus.ACTIVE.value:
                        logger.warning(f"⚠️ Skipping schedule for inactive campaign {schedule.campaign_id}")
                        repo.update_schedule_status(schedule.id, ScheduleStatus.FAILED)
                        continue
                    
                    logger.info(f"🔍 Processing campaign: {campaign.name} (ID: {campaign.id})")
                    logger.info(f"📊 Campaign stats: total={campaign.total_target_customers}, sent={campaign.messages_sent}, pending={campaign.messages_pending}")
                    
                    # Get pending recipients for today
                    recipients = repo.get_pending_recipients(
                        campaign_id=schedule.campaign_id,
                        limit=schedule.batch_size,
                        scheduled_date=date.today()
                    )
                    
                    # Get failed recipients eligible for retry
                    failed_recipients = repo.get_failed_recipients_for_retry(
                        campaign_id=schedule.campaign_id,
                        limit=max(0, schedule.batch_size - len(recipients))  # Fill remaining capacity
                    )
                    
                    # Reset failed recipients to pending for retry
                    for failed_recipient in failed_recipients:
                        repo.reset_recipient_for_retry(failed_recipient.id)
                    
                    # Refresh recipients list to include retries
                    if failed_recipients:
                        recipients = repo.get_pending_recipients(
                            campaign_id=schedule.campaign_id,
                            limit=schedule.batch_size,
                            scheduled_date=date.today()
                        )
                    
                    logger.info(f"📤 Found {len(recipients)} pending recipients for campaign: {campaign.name} (including {len(failed_recipients)} retries)")
                    if len(recipients) == 0:
                        logger.warning(f"⚠️ No recipients found for today. Schedule: {schedule.send_date}, Batch size: {schedule.batch_size}")
                        # Mark schedule as completed if no recipients
                        repo.update_schedule_status(schedule.id, ScheduleStatus.COMPLETED, messages_sent=0)
                        continue
                    
                    # Send messages
                    sent_count = 0
                    for recipient in recipients:
                        try:
                            logger.info(f"🔄 Checking recipient: {recipient.phone_number}")
                            
                            # Check subscription status before sending
                            user_repo = UserRepository(db)
                            is_subscribed = user_repo.is_user_subscribed(recipient.phone_number)
                            
                            logger.info(f"📋 Subscription status for {recipient.phone_number}: {is_subscribed}")
                            
                            if not is_subscribed:
                                # Skip unsubscribed users
                                repo.update_recipient_status(
                                    recipient.id,
                                    RecipientStatus.SKIPPED,
                                    failure_reason="User unsubscribed"
                                )
                                logger.warning(f"📵 Skipped unsubscribed user: {recipient.phone_number}")
                                continue
                            
                            # Prepare message data
                            message_data = {
                                "type": "template",
                                "template_name": campaign.template_name,
                                "language_code": campaign.language_code
                            }
                            
                            # Add components or parameters
                            if campaign.template_components:
                                message_data["components"] = campaign.template_components
                            
                            # Send via SQS
                            sqs_message_id = await send_outgoing_message(
                                phone_number=recipient.phone_number,
                                message_data=message_data,
                                metadata={
                                    "campaign_id": str(campaign.id),
                                    "campaign_name": campaign.name,
                                    "recipient_id": str(recipient.id),
                                    "source": "marketing_campaign"
                                }
                            )
                            
                            if sqs_message_id:
                                # Update recipient status to QUEUED (will be updated to SENT with WhatsApp message ID by outgoing processor)
                                repo.update_recipient_status(
                                    recipient.id,
                                    RecipientStatus.QUEUED
                                )
                                sent_count += 1
                                logger.info(f"✅ Queued message for {recipient.phone_number} (SQS: {sqs_message_id})")
                            
                        except Exception as e:
                            logger.error(f"❌ Failed to send to {recipient.phone_number}: {e}")
                            repo.update_recipient_status(
                                recipient.id,
                                RecipientStatus.FAILED,
                                failure_reason=str(e)
                            )
                    
                    total_sent += sent_count
                    campaigns_processed += 1
                    
                    logger.info(f"✅ Campaign {campaign.name}: Sent {sent_count}/{len(recipients)} messages")
                    
                    # Update schedule with sent count and mark as completed
                    repo.update_schedule_status(schedule.id, ScheduleStatus.COMPLETED, messages_sent=sent_count)
                    
                    # Record analytics
                    repo.record_analytics(schedule.campaign_id, date.today())
                    
                    # Check if campaign is completed (no more pending messages)
                    db.refresh(campaign)  # Refresh to get updated counts
                    if campaign.messages_pending == 0:
                        repo.update_campaign_status(campaign.id, CampaignStatus.COMPLETED)
                        logger.info(f"✅ Campaign {campaign.name} completed: All messages have been sent!")
                    
                except Exception as e:
                    logger.error(f"❌ Error processing schedule {schedule.id}: {e}")
                    # Mark schedule as failed
                    try:
                        repo.update_schedule_status(schedule.id, ScheduleStatus.FAILED)
                    except Exception as update_error:
                        logger.error(f"❌ Failed to update schedule status: {update_error}")
            
            # Process retries for active campaigns with failed recipients (even without schedule)
            logger.info("🔄 Checking for failed recipients in active campaigns...")
            active_campaigns = repo.get_active_campaigns()
            
            for campaign in active_campaigns:
                try:
                    # Skip if campaign was already processed in the schedule
                    if any(schedule.campaign_id == campaign.id for schedule in (schedules or [])):
                        continue
                    
                    # Get failed recipients eligible for retry
                    failed_recipients = repo.get_failed_recipients_for_retry(
                        campaign_id=campaign.id,
                        limit=50  # Process up to 50 retries per campaign per cycle
                    )
                    
                    if not failed_recipients:
                        continue
                    
                    logger.info(f"🔄 Found {len(failed_recipients)} failed recipients to retry in campaign: {campaign.name}")
                    
                    # Reset failed recipients to pending for retry
                    for failed_recipient in failed_recipients:
                        repo.reset_recipient_for_retry(failed_recipient.id)
                    
                    # Get refreshed list of pending recipients
                    recipients = repo.get_pending_recipients(
                        campaign_id=campaign.id,
                        limit=50,
                        scheduled_date=None  # Don't filter by date for retries
                    )
                    
                    sent_count = 0
                    for recipient in recipients:
                        try:
                            # Send via SQS
                            sqs_message_id = sqs_service.send_outgoing_message({
                                "phone_number": recipient.phone_number,
                                "template_name": campaign.message_template,
                                "template_language": campaign.template_language or "en",
                                "campaign_id": str(campaign.id),
                                "recipient_id": str(recipient.id),
                                "message_type": "template"
                            })
                            
                            if sqs_message_id:
                                # Update recipient status to QUEUED
                                repo.update_recipient_status(
                                    recipient.id,
                                    RecipientStatus.QUEUED
                                )
                                sent_count += 1
                                logger.info(f"✅ Queued retry for {recipient.phone_number} (SQS: {sqs_message_id})")
                            
                        except Exception as e:
                            logger.error(f"❌ Failed to retry {recipient.phone_number}: {e}")
                            repo.update_recipient_status(
                                recipient.id,
                                RecipientStatus.FAILED,
                                failure_reason=str(e)
                            )
                    
                    if sent_count > 0:
                        total_sent += sent_count
                        campaigns_processed += 1
                        logger.info(f"✅ Campaign {campaign.name}: Retried {sent_count} messages")
                        
                        # Record analytics
                        repo.record_analytics(campaign.id, date.today())
                        
                except Exception as e:
                    logger.error(f"❌ Error processing retries for campaign {campaign.id}: {e}")
            
            if campaigns_processed > 0:
                return {
                    "date": date.today().isoformat(),
                    "campaigns_processed": campaigns_processed,
                    "messages_sent": total_sent,
                    "message": f"Processed {campaigns_processed} campaigns, sent {total_sent} messages"
                }
            else:
                logger.info("📊 No campaigns scheduled for today and no retries needed")
                return {
                    "date": date.today().isoformat(),
                    "campaigns_processed": 0,
                    "messages_sent": 0
                }
    
    @staticmethod
    def get_campaign_stats(campaign_id: str) -> Dict[str, Any]:
        """Get campaign statistics"""
        with get_db_session() as db:
            repo = MarketingCampaignRepository(db)
            campaign_uuid = uuid.UUID(campaign_id)
            return repo.get_campaign_stats(campaign_uuid)
    
    @staticmethod
    def pause_campaign(campaign_id: str) -> Dict[str, Any]:
        """Pause a campaign"""
        with get_db_session() as db:
            repo = MarketingCampaignRepository(db)
            campaign_uuid = uuid.UUID(campaign_id)
            campaign = repo.update_campaign_status(campaign_uuid, CampaignStatus.PAUSED)
            
            if not campaign:
                raise ValueError(f"Campaign {campaign_id} not found")
            
            return {
                "campaign_id": campaign_id,
                "status": "paused",
                "message": f"Campaign '{campaign.name}' paused"
            }
    
    @staticmethod
    def resume_campaign(campaign_id: str) -> Dict[str, Any]:
        """Resume a paused campaign"""
        with get_db_session() as db:
            repo = MarketingCampaignRepository(db)
            campaign_uuid = uuid.UUID(campaign_id)
            campaign = repo.update_campaign_status(campaign_uuid, CampaignStatus.ACTIVE)
            
            if not campaign:
                raise ValueError(f"Campaign {campaign_id} not found")
            
            return {
                "campaign_id": campaign_id,
                "status": "active",
                "message": f"Campaign '{campaign.name}' resumed"
            }
    
    @staticmethod
    def cancel_campaign(campaign_id: str) -> Dict[str, Any]:
        """Cancel a campaign"""
        with get_db_session() as db:
            repo = MarketingCampaignRepository(db)
            campaign_uuid = uuid.UUID(campaign_id)
            campaign = repo.update_campaign_status(campaign_uuid, CampaignStatus.CANCELLED)
            
            if not campaign:
                raise ValueError(f"Campaign {campaign_id} not found")
            
            return {
                "campaign_id": campaign_id,
                "status": "cancelled",
                "message": f"Campaign '{campaign.name}' cancelled"
            }
    
    @staticmethod
    def list_campaigns(
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """List campaigns with optional status filter"""
        with get_db_session() as db:
            repo = MarketingCampaignRepository(db)
            
            if status:
                query = db.query(repo.model_class).filter(repo.model_class.status == status)
            else:
                query = db.query(repo.model_class)
            
            campaigns = query.order_by(
                repo.model_class.priority.asc(),
                repo.model_class.created_at.desc()
            ).limit(limit).all()
            
            return [
                {
                    "id": str(c.id),
                    "name": c.name,
                    "status": c.status,
                    "template_name": c.template_name,
                    "total_target": c.total_target_customers,
                    "messages_sent": c.messages_sent,
                    "messages_pending": c.messages_pending,
                    "progress": round((c.messages_sent / c.total_target_customers * 100), 2) if c.total_target_customers > 0 else 0,
                    "created_at": c.created_at.isoformat()
                }
                for c in campaigns
            ]
