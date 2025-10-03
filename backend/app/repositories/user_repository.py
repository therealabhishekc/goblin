"""
User repository for user profile and customer management operations.
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from .base_repository import BaseRepository
from ..models.user import UserProfileDB
from ..models.user import UserProfile

class UserRepository(BaseRepository[UserProfile]):
    """Repository for user profile operations"""
    
    def __init__(self, db_session: Session):
        super().__init__(db_session, UserProfileDB)
    
    def get_by_phone_number(self, phone_number: str) -> Optional[UserProfileDB]:
        """Get user by WhatsApp phone number"""
        return self.db.query(self.model_class).filter(
            self.model_class.whatsapp_phone == phone_number
        ).first()
    
    def get_by_business_name(self, business_name: str) -> List[UserProfileDB]:
        """Search users by business name"""
        return self.db.query(self.model_class).filter(
            self.model_class.business_name.ilike(f"%{business_name}%")
        ).all()
    
    def get_active_users(self) -> List[UserProfileDB]:
        """Get all active users"""
        return self.db.query(self.model_class).filter(
            self.model_class.is_active == True
        ).all()
    
    def update_last_interaction(self, phone_number: str) -> Optional[UserProfileDB]:
        """Update user's last interaction timestamp"""
        from datetime import datetime
        
        user = self.get_by_phone_number(phone_number)
        if user:
            user.last_interaction = datetime.utcnow()
            self.db.commit()
            self.db.refresh(user)
        return user
    
    def get_customers_by_tags(self, tags: List[str]) -> List[UserProfileDB]:
        """Get customers with specific tags"""
        return self.db.query(self.model_class).filter(
            self.model_class.tags.op('&&')(tags)  # PostgreSQL array overlap operator
        ).all()
    
    def unsubscribe_user(self, phone_number: str) -> Optional[UserProfileDB]:
        """
        Unsubscribe user from template messages (STOP command)
        Does NOT affect automated replies
        """
        from datetime import datetime
        from app.core.logging import logger
        
        user = self.get_by_phone_number(phone_number)
        if user:
            user.subscription = "unsubscribed"
            user.subscription_updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(user)
            logger.info(f"📵 User {phone_number} unsubscribed from template messages")
        return user
    
    def resubscribe_user(self, phone_number: str) -> Optional[UserProfileDB]:
        """
        Resubscribe user to template messages (START command)
        """
        from datetime import datetime
        from app.core.logging import logger
        
        user = self.get_by_phone_number(phone_number)
        if user:
            user.subscription = "subscribed"
            user.subscription_updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(user)
            logger.info(f"✅ User {phone_number} resubscribed to template messages")
        return user
    
    def is_user_subscribed(self, phone_number: str) -> bool:
        """
        Check if user is subscribed to template messages
        Returns True if subscribed or user doesn't exist (default to subscribed)
        """
        user = self.get_by_phone_number(phone_number)
        if not user:
            return True  # Default to subscribed for new users
        return user.subscription == "subscribed"
    
    def get_subscribed_users(self) -> List[UserProfileDB]:
        """Get all users who are subscribed to template messages"""
        return self.db.query(self.model_class).filter(
            self.model_class.subscription == "subscribed"
        ).all()
    
    def get_unsubscribed_users(self) -> List[UserProfileDB]:
        """Get all users who are unsubscribed from template messages"""
        return self.db.query(self.model_class).filter(
            self.model_class.subscription == "unsubscribed"
        ).all()
