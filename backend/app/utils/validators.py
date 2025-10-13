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

def validate_address_line(address: str) -> bool:
    """Validate address line"""
    return bool(address and len(address.strip()) >= 2 and len(address.strip()) <= 200)

def validate_city(city: str) -> bool:
    """Validate city name"""
    return bool(city and len(city.strip()) >= 2 and len(city.strip()) <= 100)

def validate_state(state: str) -> bool:
    """Validate state (2 letter code or full name)"""
    return bool(state and len(state.strip()) >= 2 and len(state.strip()) <= 50)

def validate_zipcode(zipcode: str) -> bool:
    """Validate ZIP/postal code (flexible format)"""
    # Supports US ZIP (5 or 9 digits), Canadian postal code, and other formats
    pattern = r'^[A-Za-z0-9][A-Za-z0-9\s\-]{2,12}[A-Za-z0-9]$'
    return bool(zipcode and re.match(pattern, zipcode.strip()))
