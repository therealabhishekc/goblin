"""
Configuration management for the application.
Handles environment variables and application settings.
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from app.utils.secrets import get_whatsapp_credentials

class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # Application environment
    environment: str = "development"
    
    # Database settings - REQUIRED, no default with credentials
    database_url: str = Field(..., description="PostgreSQL database URL - must be provided via DATABASE_URL env var")
    
    # WhatsApp API settings (will be loaded from Secrets Manager or env vars)
    whatsapp_token: Optional[str] = None
    whatsapp_phone_number_id: Optional[str] = None
    phone_number_id: Optional[str] = None  # Alternative field name
    verify_token: Optional[str] = None
    whatsapp_api_version: str = "v22.0"  # WhatsApp Graph API version
    
    # AWS settings
    aws_region: str = "us-east-1"
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    dynamodb_table_name: str = "whatsapp-dedup-dev"
    
    # Redis settings
    redis_url: Optional[str] = None
    
    # SQS Configuration
    incoming_queue_url: Optional[str] = None
    outgoing_queue_url: Optional[str] = None
    analytics_queue_url: Optional[str] = None
    incoming_dlq_url: Optional[str] = None
    outgoing_dlq_url: Optional[str] = None
    analytics_dlq_url: Optional[str] = None
    
    # Application settings
    debug: bool = False
    log_level: str = "INFO"
    app_name: str = "WhatsApp Business API"
    app_version: str = "2.0.0"
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    
    @field_validator('database_url')
    @classmethod
    def validate_database_url(cls, v):
        if not v:
            raise ValueError('DATABASE_URL environment variable is required and must be set to a valid PostgreSQL connection string')
        
        # Security check: warn about insecure defaults
        if 'password' in v.lower() and ('postgres:password' in v or 'user:password' in v):
            raise ValueError('DATABASE_URL contains insecure default credentials. Please use a secure database URL.')
            
        return v
    
    @field_validator('whatsapp_token')
    @classmethod
    def validate_whatsapp_token(cls, v):
        if not v:
            print("⚠️  WHATSAPP_TOKEN not set - WhatsApp API features will be disabled")
        return v
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False
    }
    
    def load_whatsapp_credentials(self):
        """Load WhatsApp credentials from AWS Secrets Manager or environment variables"""
        try:
            credentials = get_whatsapp_credentials()
            
            # Update settings with retrieved credentials
            if credentials.get('WHATSAPP_TOKEN'):
                self.whatsapp_token = credentials['WHATSAPP_TOKEN']
            if credentials.get('VERIFY_TOKEN'):
                self.verify_token = credentials['VERIFY_TOKEN']
            if credentials.get('PHONE_NUMBER_ID'):
                self.phone_number_id = credentials['PHONE_NUMBER_ID']
                self.whatsapp_phone_number_id = credentials['PHONE_NUMBER_ID']
                
        except Exception as e:
            print(f"⚠️  Error loading WhatsApp credentials: {e}")

# Global settings instance
settings = Settings()

# Load WhatsApp credentials on startup
settings.load_whatsapp_credentials()

def get_settings() -> Settings:
    """Get application settings"""
    return settings
