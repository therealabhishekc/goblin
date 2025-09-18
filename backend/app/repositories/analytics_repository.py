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
