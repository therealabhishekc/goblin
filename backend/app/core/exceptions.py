"""
Custom exceptions for the application.
"""
from fastapi import HTTPException
from typing import Any, Dict, Optional

class WhatsAppBusinessException(Exception):
    """Base exception for WhatsApp Business application"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

class DatabaseException(WhatsAppBusinessException):
    """Database operation exceptions"""
    pass

class ValidationException(WhatsAppBusinessException):
    """Data validation exceptions"""
    pass

class WebhookException(WhatsAppBusinessException):
    """WhatsApp webhook processing exceptions"""
    pass

class UserNotFoundException(WhatsAppBusinessException):
    """User not found exception"""
    def __init__(self, phone_number: str):
        super().__init__(f"User with phone number {phone_number} not found")
        self.phone_number = phone_number

class MessageNotFoundException(WhatsAppBusinessException):
    """Message not found exception"""
    def __init__(self, message_id: str):
        super().__init__(f"Message with ID {message_id} not found")
        self.message_id = message_id

class DuplicateMessageException(WhatsAppBusinessException):
    """Duplicate message exception"""
    def __init__(self, message_id: str):
        super().__init__(f"Message with ID {message_id} already processed")
        self.message_id = message_id

# HTTP Exception helpers
def create_http_exception(
    status_code: int, 
    message: str, 
    details: Optional[Dict[str, Any]] = None
) -> HTTPException:
    """Create HTTPException with consistent format"""
    return HTTPException(
        status_code=status_code,
        detail={
            "message": message,
            "details": details or {}
        }
    )
