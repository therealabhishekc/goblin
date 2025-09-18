"""
Application constants and configuration values.
"""

# WhatsApp API Constants
WHATSAPP_API_VERSION = "v18.0"
WHATSAPP_BASE_URL = "https://graph.facebook.com"

# Message Types
MESSAGE_TYPES = {
    "TEXT": "text",
    "IMAGE": "image", 
    "DOCUMENT": "document",
    "AUDIO": "audio",
    "VIDEO": "video",
    "VOICE": "voice",
    "STICKER": "sticker",
    "LOCATION": "location",
    "CONTACTS": "contacts",
    "BUTTON": "button",
    "INTERACTIVE": "interactive"
}

# Message Status
MESSAGE_STATUS = {
    "RECEIVED": "received",
    "DELIVERED": "delivered", 
    "READ": "read",
    "FAILED": "failed",
    "SENT": "sent"
}

# Customer Tiers
CUSTOMER_TIERS = {
    "REGULAR": "regular",
    "PREMIUM": "premium",
    "VIP": "vip"
}

# File Size Limits (in bytes)
MAX_FILE_SIZES = {
    "image": 5 * 1024 * 1024,    # 5MB
    "document": 100 * 1024 * 1024,  # 100MB
    "audio": 16 * 1024 * 1024,   # 16MB
    "video": 16 * 1024 * 1024,   # 16MB
    "voice": 16 * 1024 * 1024    # 16MB
}

# Supported Media Types
SUPPORTED_MEDIA_TYPES = {
    "image": ["image/jpeg", "image/png", "image/webp"],
    "document": ["application/pdf", "text/plain", "application/msword", 
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document"],
    "audio": ["audio/aac", "audio/mp4", "audio/mpeg", "audio/amr", "audio/ogg"],
    "video": ["video/mp4", "video/3gp"],
    "voice": ["audio/ogg"]
}

# Database Limits
DB_LIMITS = {
    "PHONE_NUMBER_LENGTH": 20,
    "MESSAGE_ID_LENGTH": 100,
    "DISPLAY_NAME_LENGTH": 100,
    "BUSINESS_NAME_LENGTH": 200,
    "EMAIL_LENGTH": 255,
    "TEMPLATE_NAME_LENGTH": 100,
    "TEMPLATE_TEXT_LENGTH": 1000
}

# Cache TTL (Time To Live) in seconds
CACHE_TTL = {
    "USER_PROFILE": 300,        # 5 minutes
    "MESSAGE_DEDUP": 21600,     # 6 hours
    "ANALYTICS": 3600,          # 1 hour
    "TEMPLATE": 1800            # 30 minutes
}

# Rate Limits
RATE_LIMITS = {
    "WEBHOOK_PER_MINUTE": 1000,
    "API_PER_MINUTE": 100,
    "MESSAGES_PER_DAY": 10000
}

# Response Templates
RESPONSE_TEMPLATES = {
    "WELCOME": "Welcome to our WhatsApp Business service! How can we help you today?",
    "HELP": "Here are the commands you can use:\n• Type 'hi' for greeting\n• Type 'help' for this message",
    "ERROR": "Sorry, we encountered an error processing your message. Please try again later.",
    "NOT_UNDERSTOOD": "I didn't understand that message. Type 'help' for available commands."
}
