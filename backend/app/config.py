"""
Configuration management for the application.
Handles environment variables and application settings.
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import field_validator

class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # Application environment
    environment: str = "development"
    
    # Database settings
    database_url: str = "postgresql://postgres:password@localhost:5432/whatsapp_business"
    
    # WhatsApp API settings
    whatsapp_token: Optional[str] = None
    whatsapp_phone_number_id: Optional[str] = None
    phone_number_id: Optional[str] = None  # Alternative field name
    verify_token: Optional[str] = None
    
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
            raise ValueError('DATABASE_URL is required')
        return v
    
    @field_validator('whatsapp_token')
    @classmethod
    def validate_whatsapp_token(cls, v):
        if not v:
            print("⚠️  WHATSAPP_TOKEN not set - WhatsApp API features will be disabled")
        return v
    
    model_config = {
        "env_file": [".env", "/Users/abskchsk/Documents/govindjis/wa-app/backend/.env"],
        "case_sensitive": False
    }

# Global settings instance
settings = Settings()

def get_settings() -> Settings:
    """Get application settings"""
    return settings
