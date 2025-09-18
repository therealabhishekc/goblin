"""
Input validation utilities.
"""
import re
from typing import Optional

def validate_phone_number(phone: str) -> bool:
    """Validate WhatsApp phone number format"""
    # Remove any non-digit characters
    clean_phone = re.sub(r'\D', '', phone)
    
    # Check if it's a valid international format (7-15 digits)
    return len(clean_phone) >= 7 and len(clean_phone) <= 15

def sanitize_phone_number(phone: str) -> str:
    """Clean and standardize phone number"""
    return re.sub(r'\D', '', phone)

def validate_message_id(message_id: str) -> bool:
    """Validate WhatsApp message ID format"""
    return bool(message_id and len(message_id) > 0 and len(message_id) <= 100)

def validate_email(email: str) -> bool:
    """Basic email validation"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_business_name(name: str) -> bool:
    """Validate business name"""
    return bool(name and len(name.strip()) >= 2 and len(name.strip()) <= 200)
