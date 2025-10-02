"""
AWS Secrets Manager utility for secure credential management.
"""
import json
import boto3
from typing import Dict, Optional
from botocore.exceptions import ClientError, NoCredentialsError
import os

from app.core.logging import logger

class SecretsManager:
    """AWS Secrets Manager client for retrieving application secrets"""
    
    def __init__(self, region_name: Optional[str] = None):
        """
        Initialize Secrets Manager client
        
        Args:
            region_name: AWS region. If None, uses AWS_REGION env var or default region
        """
        self.region_name = region_name or os.getenv('AWS_REGION', 'us-east-1')
        self._client = None
        self._secrets_cache = {}
        
    @property
    def client(self):
        """Lazy initialize boto3 client"""
        if self._client is None:
            try:
                self._client = boto3.client('secretsmanager', region_name=self.region_name)
            except NoCredentialsError:
                logger.warning("AWS credentials not found. Secrets Manager will not be available.")
                return None
        return self._client
    
    def get_secret(self, secret_name: str, force_refresh: bool = False) -> Optional[Dict]:
        """
        Retrieve secret from AWS Secrets Manager
        
        Args:
            secret_name: Name or ARN of the secret
            force_refresh: If True, bypasses cache and fetches fresh secret
            
        Returns:
            Dictionary containing secret data or None if secret not found/accessible
        """
        # Return cached secret if available and not forcing refresh
        if not force_refresh and secret_name in self._secrets_cache:
            logger.debug(f"Returning cached secret for: {secret_name}")
            return self._secrets_cache[secret_name]
            
        if not self.client:
            logger.warning("Secrets Manager client not available")
            return None
            
        try:
            logger.info(f"Fetching secret from AWS Secrets Manager: {secret_name}")
            response = self.client.get_secret_value(SecretId=secret_name)
            
            # Parse the secret string as JSON
            secret_data = json.loads(response['SecretString'])
            
            # Cache the secret
            self._secrets_cache[secret_name] = secret_data
            
            logger.info(f"Successfully retrieved secret: {secret_name}")
            return secret_data
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'ResourceNotFoundException':
                logger.error(f"Secret not found: {secret_name}")
            elif error_code == 'InvalidRequestException':
                logger.error(f"Invalid request for secret: {secret_name}")
            elif error_code == 'InvalidParameterException':
                logger.error(f"Invalid parameter for secret: {secret_name}")
            elif error_code == 'DecryptionFailure':
                logger.error(f"Cannot decrypt secret: {secret_name}")
            elif error_code == 'InternalServiceError':
                logger.error(f"AWS internal error retrieving secret: {secret_name}")
            else:
                logger.error(f"Error retrieving secret {secret_name}: {e}")
            return None
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse secret JSON for {secret_name}: {e}")
            return None
            
        except Exception as e:
            logger.error(f"Unexpected error retrieving secret {secret_name}: {e}")
            return None
    
    def get_whatsapp_credentials(self) -> Optional[Dict]:
        """
        Get WhatsApp credentials from the configured secret
        
        Returns:
            Dictionary with WhatsApp credentials or None if not available
        """
        secret_name = os.getenv('WHATSAPP_SECRETS_NAME')
        if not secret_name:
            logger.warning("WHATSAPP_SECRETS_NAME environment variable not set")
            return None
            
        return self.get_secret(secret_name)
    
    def clear_cache(self):
        """Clear the secrets cache"""
        self._secrets_cache.clear()
        logger.info("Secrets cache cleared")

# Global secrets manager instance
secrets_manager = SecretsManager()

def get_whatsapp_credentials() -> Dict[str, Optional[str]]:
    """
    Get WhatsApp credentials, falling back to environment variables for local development
    
    Returns:
        Dictionary containing WHATSAPP_TOKEN, VERIFY_TOKEN, and PHONE_NUMBER_ID
    """
    # Try to get from Secrets Manager first
    credentials = secrets_manager.get_whatsapp_credentials()
    
    if credentials:
        logger.info("Using WhatsApp credentials from AWS Secrets Manager")
        return {
            'WHATSAPP_TOKEN': credentials.get('WHATSAPP_TOKEN'),
            'VERIFY_TOKEN': credentials.get('VERIFY_TOKEN'),
            'PHONE_NUMBER_ID': credentials.get('PHONE_NUMBER_ID')
        }
    
    # Fallback to environment variables (for local development)
    logger.info("Falling back to environment variables for WhatsApp credentials")
    return {
        'WHATSAPP_TOKEN': os.getenv('WHATSAPP_TOKEN'),
        'VERIFY_TOKEN': os.getenv('VERIFY_TOKEN'),
        'PHONE_NUMBER_ID': os.getenv('PHONE_NUMBER_ID') or os.getenv('WHATSAPP_PHONE_NUMBER_ID')
    }

def validate_whatsapp_credentials() -> bool:
    """
    Validate that required WhatsApp credentials are available
    
    Returns:
        True if all required credentials are present, False otherwise
    """
    credentials = get_whatsapp_credentials()
    
    required_fields = ['WHATSAPP_TOKEN', 'VERIFY_TOKEN', 'PHONE_NUMBER_ID']
    missing_fields = [field for field in required_fields if not credentials.get(field)]
    
    if missing_fields:
        logger.error(f"Missing WhatsApp credentials: {', '.join(missing_fields)}")
        return False
        
    logger.info("All WhatsApp credentials validated successfully")
    return True