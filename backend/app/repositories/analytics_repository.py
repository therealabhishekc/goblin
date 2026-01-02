"""
Analytics repository for business metrics and reporting.
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from .base_repository import BaseRepository
from ..models.business import BusinessMetricsDB
from ..models.business import BusinessMetrics
from ..core.logging import logger

class AnalyticsRepository(BaseRepository[BusinessMetrics]):
    """Repository for business analytics and metrics"""
    
    def __init__(self, db_session: Session):
        super().__init__(db_session, BusinessMetricsDB)
    
    def get_metrics_by_date(self, date: datetime) -> Optional[BusinessMetricsDB]:
        """Get metrics for a specific date"""
        target_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
        return self.db.query(self.model_class).filter(
            self.model_class.date == target_date
        ).first()
    
    def get_date_range_metrics(self, start_date: datetime, end_date: datetime) -> List[BusinessMetricsDB]:
        """Get metrics for a date range"""
        return self.db.query(self.model_class).filter(
            and_(
                self.model_class.date >= start_date.replace(hour=0, minute=0, second=0, microsecond=0),
                self.model_class.date <= end_date.replace(hour=0, minute=0, second=0, microsecond=0)
            )
        ).order_by(self.model_class.date).all()
    
    def get_last_n_days_metrics(self, days: int = 7) -> List[BusinessMetricsDB]:
        """Get metrics for last N days"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        return self.get_date_range_metrics(start_date, end_date)
    
    def increment_messages_received(self, date: datetime = None) -> BusinessMetricsDB:
        """Increment messages received counter for today"""
        if not date:
            date = datetime.utcnow()
        
        target_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
        metrics = self.get_metrics_by_date(target_date)
        
        if not metrics:
            # Create new metrics record for the day
            metrics = BusinessMetricsDB(
                date=target_date,
                total_messages_received=1,
                total_responses_sent=0,
                unique_users=0
            )
            self.db.add(metrics)
        else:
            metrics.total_messages_received += 1
        
        self.db.commit()
        self.db.refresh(metrics)
        return metrics
    
    def increment_responses_sent(self, date: datetime = None) -> BusinessMetricsDB:
        """Increment responses sent counter for today"""
        if not date:
            date = datetime.utcnow()
        
        target_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
        metrics = self.get_metrics_by_date(target_date)
        
        if not metrics:
            metrics = BusinessMetricsDB(
                date=target_date,
                total_messages_received=0,
                total_responses_sent=1,
                unique_users=0
            )
            self.db.add(metrics)
        else:
            metrics.total_responses_sent += 1
        
        self.db.commit()
        self.db.refresh(metrics)
        return metrics
    
    def update_unique_users_count(self, date: datetime = None) -> BusinessMetricsDB:
        """Update unique users count for the day"""
        if not date:
            date = datetime.utcnow()
        
        target_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Count unique users who sent messages today
        from ..models.whatsapp import WhatsAppMessageDB
        unique_count = self.db.query(func.count(func.distinct(WhatsAppMessageDB.from_phone))).filter(
            func.date(WhatsAppMessageDB.timestamp) == target_date.date()
        ).scalar()
        
        metrics = self.get_metrics_by_date(target_date)
        if not metrics:
            metrics = BusinessMetricsDB(
                date=target_date,
                total_messages_received=0,
                total_responses_sent=0,
                unique_users=unique_count or 0
            )
            self.db.add(metrics)
        else:
            metrics.unique_users = unique_count or 0
        
        self.db.commit()
        self.db.refresh(metrics)
        return metrics
    
    def update_response_time_avg(self, date: datetime = None) -> BusinessMetricsDB:
        """
        Calculate and update average response time for a specific date.
        
        Logic:
        1. Find all incoming messages for the day
        2. For each incoming message, find the first outgoing response to the same phone number after it
        3. Calculate time difference between incoming and outgoing messages
        4. Average all response times for the day
        5. Store in minutes (convert from seconds)
        """
        if not date:
            date = datetime.utcnow()
        
        target_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
        next_date = target_date + timedelta(days=1)
        
        from ..models.whatsapp import WhatsAppMessageDB
        
        # Get all incoming messages for the day
        incoming_messages = self.db.query(WhatsAppMessageDB).filter(
            and_(
                WhatsAppMessageDB.direction == "incoming",
                WhatsAppMessageDB.timestamp >= target_date,
                WhatsAppMessageDB.timestamp < next_date
            )
        ).order_by(WhatsAppMessageDB.timestamp).all()
        
        if not incoming_messages:
            logger.info(f"No incoming messages found for {target_date.date()}")
            return self.get_metrics_by_date(target_date)
        
        response_times = []
        
        # For each incoming message, find the first outgoing response
        for incoming_msg in incoming_messages:
            # Find first outgoing message to the same phone number after this incoming message
            outgoing_response = self.db.query(WhatsAppMessageDB).filter(
                and_(
                    WhatsAppMessageDB.direction == "outgoing",
                    WhatsAppMessageDB.to_phone == incoming_msg.from_phone,
                    WhatsAppMessageDB.timestamp > incoming_msg.timestamp,
                    # Only consider responses within 24 hours to avoid skewing data
                    WhatsAppMessageDB.timestamp < incoming_msg.timestamp + timedelta(hours=24)
                )
            ).order_by(WhatsAppMessageDB.timestamp).first()
            
            if outgoing_response:
                # Calculate response time in seconds
                time_diff = (outgoing_response.timestamp - incoming_msg.timestamp).total_seconds()
                response_times.append(time_diff)
        
        if not response_times:
            logger.info(f"No response times found for {target_date.date()}")
            return self.get_metrics_by_date(target_date)
        
        # Calculate average response time in seconds
        avg_response_time_seconds = sum(response_times) / len(response_times)
        
        # Update or create metrics record
        metrics = self.get_metrics_by_date(target_date)
        if not metrics:
            metrics = BusinessMetricsDB(
                date=target_date,
                total_messages_received=0,
                total_responses_sent=0,
                unique_users=0,
                response_time_avg_seconds=avg_response_time_seconds
            )
            self.db.add(metrics)
        else:
            metrics.response_time_avg_seconds = avg_response_time_seconds
        
        self.db.commit()
        self.db.refresh(metrics)
        
        avg_minutes = avg_response_time_seconds / 60
        logger.info(
            f"✅ Updated response time avg for {target_date.date()}: "
            f"{avg_response_time_seconds:.2f}s ({avg_minutes:.2f} minutes) "
            f"based on {len(response_times)} conversation pairs"
        )
        
        return metrics
    
    def get_total_metrics_summary(self) -> Dict[str, int]:
        """Get overall summary of all metrics"""
        total_messages = self.db.query(func.sum(self.model_class.total_messages_received)).scalar() or 0
        total_responses = self.db.query(func.sum(self.model_class.total_responses_sent)).scalar() or 0
        avg_response_time = self.db.query(func.avg(self.model_class.response_time_avg_seconds)).scalar() or 0
        
        return {
            "total_messages_received": total_messages,
            "total_responses_sent": total_responses,
            "average_response_time_seconds": round(avg_response_time, 2),
            "total_days_tracked": self.count()
        }
