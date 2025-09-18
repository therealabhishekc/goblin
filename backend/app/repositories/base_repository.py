"""
Base repository class for common database operations.
"""
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List, Any
from sqlalchemy.orm import Session

T = TypeVar('T')

class BaseRepository(ABC, Generic[T]):
    """Abstract base repository providing common CRUD operations"""
    
    def __init__(self, db_session: Session, model_class):
        self.db = db_session
        self.model_class = model_class
    
    def create(self, entity: T) -> T:
        """Create a new record"""
        db_obj = self.model_class(**entity.dict())
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
    
    def get_by_id(self, id: Any) -> Optional[T]:
        """Get record by ID"""
        return self.db.query(self.model_class).filter(self.model_class.id == id).first()
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Get all records with pagination"""
        return self.db.query(self.model_class).offset(skip).limit(limit).all()
    
    def update(self, id: Any, update_data: dict) -> Optional[T]:
        """Update record by ID"""
        db_obj = self.get_by_id(id)
        if db_obj:
            for field, value in update_data.items():
                setattr(db_obj, field, value)
            self.db.commit()
            self.db.refresh(db_obj)
        return db_obj
    
    def delete(self, id: Any) -> bool:
        """Delete record by ID"""
        db_obj = self.get_by_id(id)
        if db_obj:
            self.db.delete(db_obj)
            self.db.commit()
            return True
        return False
    
    def count(self) -> int:
        """Count total records"""
        return self.db.query(self.model_class).count()
