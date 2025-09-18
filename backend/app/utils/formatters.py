"""
Data formatting utilities.
"""
from datetime import datetime
from typing import Any, Dict, Optional

def format_phone_display(phone: str) -> str:
    """Format phone number for display"""
    clean = phone.replace('+', '')
    if len(clean) >= 10:
        return f"+{clean[:1]} {clean[1:4]} {clean[4:7]} {clean[7:]}"
    return phone

def format_timestamp(dt: datetime) -> str:
    """Format datetime for API responses"""
    return dt.isoformat() if dt else None

def format_message_preview(content: str, max_length: int = 50) -> str:
    """Create message preview with truncation"""
    if not content:
        return ""
    
    if len(content) <= max_length:
        return content
    
    return content[:max_length-3] + "..."

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def format_response_time(seconds: float) -> str:
    """Format response time for display"""
    if seconds < 1:
        return f"{int(seconds * 1000)}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    else:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"

def clean_text_content(text: str) -> str:
    """Clean and normalize text content"""
    if not text:
        return ""
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    # Remove special characters that might cause issues
    text = text.replace('\x00', '').replace('\r', '\n')
    
    return text.strip()
