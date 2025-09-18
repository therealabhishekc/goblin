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
