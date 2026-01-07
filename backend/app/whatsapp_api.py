import httpx
import os
import json
from typing import Dict, Any, Optional, List

from app.core.logging import logger
from app.core.config import get_settings
from app.utils.constants import WHATSAPP_BASE_URL

# Get settings instance
settings = get_settings()
WHATSAPP_TOKEN = settings.whatsapp_token
PHONE_NUMBER_ID = settings.whatsapp_phone_number_id or settings.phone_number_id

def _get_whatsapp_api_url() -> str:
    """Get the WhatsApp API URL with configurable version"""
    return f"{WHATSAPP_BASE_URL}/{settings.whatsapp_api_version}/{PHONE_NUMBER_ID}/messages"

def _validate_whatsapp_config():
    """Validate WhatsApp configuration before API calls"""
    if not WHATSAPP_TOKEN:
        logger.error("❌ WHATSAPP_TOKEN not configured")
        raise ValueError("WHATSAPP_TOKEN environment variable is required")
    
    if not PHONE_NUMBER_ID:
        logger.error("❌ PHONE_NUMBER_ID not configured")
        raise ValueError("PHONE_NUMBER_ID or WHATSAPP_PHONE_NUMBER_ID environment variable is required")


async def send_template_message(
    to: str, 
    template_name: str, 
    language_code: str = "en_US",
    components: Optional[List[Dict[str, Any]]] = None,
    parameters: Optional[List[Dict]] = None
):
    """
    Send a WhatsApp template message with full component support
    
    Args:
        to: Recipient phone number
        template_name: Name of the approved WhatsApp template
        language_code: Language code (default: en_US). Examples: en, es, fr, de, pt_BR, etc.
        components: Full component structure for complex templates (headers, body, buttons)
        parameters: Simplified body parameters (backward compatibility)
    
    Component Structure Examples:
        - Header with text: {"type": "header", "parameters": [{"type": "text", "text": "value"}]}
        - Header with image: {"type": "header", "parameters": [{"type": "image", "image": {"link": "url"}}]}
        - Body with params: {"type": "body", "parameters": [{"type": "text", "text": "value"}]}
        - Button with URL: {"type": "button", "sub_type": "url", "index": 0, "parameters": [...]}
    
    Returns:
        WhatsApp API response with message ID
    """
    
    # Validate configuration
    _validate_whatsapp_config()
    
    url = _get_whatsapp_api_url()
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    
    template_data = {
        "name": template_name,
        "language": {"code": language_code}
    }
    
    # Handle backward compatibility: if simple parameters provided, convert to body component
    if parameters and not components:
        template_data["components"] = [{
            "type": "body",
            "parameters": parameters
        }]
        logger.debug(f"Converting simple parameters to body component for template {template_name}")
    
    # Use full component structure if provided
    elif components:
        template_data["components"] = components
        logger.debug(f"Using full component structure for template {template_name}: {len(components)} components")
    
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "template",
        "template": template_data
    }
    
    try:
        async with httpx.AsyncClient() as client:
            logger.debug(f"Sending template {template_name} to {to} with language {language_code}")
            logger.debug(f"Template payload: {json.dumps(payload, indent=2)}")
            
            response = await client.post(url, headers=headers, json=payload)
            
            # Log response for debugging
            if response.status_code != 200:
                error_body = response.text
                logger.error(f"❌ WhatsApp API Error {response.status_code} for template {template_name}: {error_body}")
                logger.error(f"Request payload was: {json.dumps(payload, indent=2)}")
            
            response.raise_for_status()
            result = response.json()
            message_id = result.get('messages', [{}])[0].get('id', 'unknown_id')
            logger.info(f"✅ Template message '{template_name}' sent to {to}: {message_id}")
            return result
            
    except httpx.HTTPStatusError as e:
        logger.error(f"❌ Failed to send template {template_name} to {to}: HTTP {e.response.status_code}")
        logger.error(f"Response body: {e.response.text}")
        raise
    except Exception as e:
        logger.error(f"❌ Failed to send template message to {to}: {e}")
        raise


async def send_text_message(to: str, text: str) -> Dict[str, Any]:
    """Send a WhatsApp text message"""
    _validate_whatsapp_config()
    
    url = _get_whatsapp_api_url()
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text}
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            
            # Log the request details for debugging
            logger.debug(f"WhatsApp API Request - URL: {url}, Payload: {payload}")
            
            # Check response before raising
            if response.status_code != 200:
                error_body = response.text
                logger.error(f"❌ WhatsApp API Error {response.status_code} for {to}: {error_body}")
                logger.error(f"Request payload was: {json.dumps(payload, indent=2)}")
            
            response.raise_for_status()
            result = response.json()
            logger.info(f"✅ Text message sent to {to}: {result.get('messages', [{}])[0].get('id', 'unknown_id')}")
            return result
    except httpx.HTTPStatusError as e:
        logger.error(f"❌ Failed to send text message to {to}: HTTP {e.response.status_code}")
        logger.error(f"Response body: {e.response.text}")
        raise
    except Exception as e:
        logger.error(f"❌ Failed to send text message to {to}: {e}")
        raise

async def send_image_message(to: str, image_url: str, caption: Optional[str] = None) -> Dict[str, Any]:
    """Send a WhatsApp image message"""
    url = _get_whatsapp_api_url()
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    
    image_data = {"link": image_url}
    if caption:
        image_data["caption"] = caption
    
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "image",
        "image": image_data
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            logger.info(f"✅ Image message sent to {to}: {result.get('messages', [{}])[0].get('id', 'unknown_id')}")
            return result
    except Exception as e:
        logger.error(f"❌ Failed to send image message to {to}: {e}")
        raise

async def send_document_message(to: str, document_url: str, filename: str, caption: Optional[str] = None) -> Dict[str, Any]:
    """Send a WhatsApp document message (PDFs, Word docs, etc.)"""
    url = _get_whatsapp_api_url()
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    
    document_data = {"link": document_url, "filename": filename}
    if caption:
        document_data["caption"] = caption
    
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "document",
        "document": document_data
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            logger.info(f"✅ Document message sent to {to}: {result.get('messages', [{}])[0].get('id', 'unknown_id')}")
            return result
    except Exception as e:
        logger.error(f"❌ Failed to send document message to {to}: {e}")
        raise

async def send_audio_message(to: str, audio_url: str) -> Dict[str, Any]:
    """Send a WhatsApp audio message"""
    url = _get_whatsapp_api_url()
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "audio",
        "audio": {"link": audio_url}
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            logger.info(f"✅ Audio message sent to {to}: {result.get('messages', [{}])[0].get('id', 'unknown_id')}")
            return result
    except Exception as e:
        logger.error(f"❌ Failed to send audio message to {to}: {e}")
        raise

async def send_video_message(to: str, video_url: str, caption: Optional[str] = None) -> Dict[str, Any]:
    """Send a WhatsApp video message"""
    url = _get_whatsapp_api_url()
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    
    video_data = {"link": video_url}
    if caption:
        video_data["caption"] = caption
    
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "video",
        "video": video_data
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            logger.info(f"✅ Video message sent to {to}: {result.get('messages', [{}])[0].get('id', 'unknown_id')}")
            return result
    except Exception as e:
        logger.error(f"❌ Failed to send video message to {to}: {e}")
        raise

async def send_location_message(to: str, latitude: float, longitude: float, name: Optional[str] = None, address: Optional[str] = None) -> Dict[str, Any]:
    """Send a WhatsApp location message"""
    url = _get_whatsapp_api_url()
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    
    location_data = {
        "latitude": latitude,
        "longitude": longitude
    }
    if name:
        location_data["name"] = name
    if address:
        location_data["address"] = address
    
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "location",
        "location": location_data
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            logger.info(f"✅ Location message sent to {to}: {result.get('messages', [{}])[0].get('id', 'unknown_id')}")
            return result
    except Exception as e:
        logger.error(f"❌ Failed to send location message to {to}: {e}")
        raise

async def send_interactive_message(to: str, interactive_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send a WhatsApp interactive message (buttons or lists)
    
    Args:
        to: Recipient phone number
        interactive_data: Interactive message structure
            For buttons: {
                "type": "button",
                "body": {"text": "Body text"},
                "action": {
                    "buttons": [
                        {"type": "reply", "reply": {"id": "id1", "title": "Button 1"}},
                        ...
                    ]
                }
            }
            For lists: {
                "type": "list",
                "body": {"text": "Body text"},
                "action": {
                    "button": "Button text",
                    "sections": [
                        {
                            "title": "Section 1",
                            "rows": [
                                {"id": "id1", "title": "Option 1", "description": "Description"}
                            ]
                        }
                    ]
                }
            }
    
    Returns:
        WhatsApp API response
    """
    _validate_whatsapp_config()
    
    url = _get_whatsapp_api_url()
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": interactive_data
    }
    
    try:
        logger.info(f"📤 Sending interactive message to {to}, type: {interactive_data.get('type')}")
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            message_id = result.get('messages', [{}])[0].get('id', 'unknown_id')
            logger.info(f"✅ Interactive message sent to {to}: {message_id}")
            return result
    except httpx.HTTPStatusError as e:
        logger.error(f"❌ HTTP error sending interactive message to {to}: {e.response.status_code} - {e.response.text}")
        raise
    except Exception as e:
        logger.error(f"❌ Failed to send interactive message to {to}: {e}")
        raise

async def send_whatsapp_message(to: str, message_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Universal message sender - routes to appropriate function based on message type
    
    Args:
        to: Recipient phone number
        message_data: Dictionary containing message type and data
        
    Returns:
        WhatsApp API response
    """
    message_type = message_data.get("type", "text")
    
    try:
        if message_type == "text":
            content = message_data.get("content", message_data.get("text", ""))
            return await send_text_message(to, content)
            
        elif message_type == "image":
            image_url = message_data.get("media_url", message_data.get("image_url"))
            caption = message_data.get("content", message_data.get("caption"))
            if not image_url:
                raise ValueError("Image URL is required for image messages")
            return await send_image_message(to, image_url, caption)
            
        elif message_type == "document":
            document_url = message_data.get("media_url", message_data.get("document_url"))
            filename = message_data.get("filename", "document")
            caption = message_data.get("content", message_data.get("caption"))
            if not document_url:
                raise ValueError("Document URL is required for document messages")
            return await send_document_message(to, document_url, filename, caption)
            
        elif message_type == "audio":
            audio_url = message_data.get("media_url", message_data.get("audio_url"))
            if not audio_url:
                raise ValueError("Audio URL is required for audio messages")
            return await send_audio_message(to, audio_url)
            
        elif message_type == "video":
            video_url = message_data.get("media_url", message_data.get("video_url"))
            caption = message_data.get("content", message_data.get("caption"))
            if not video_url:
                raise ValueError("Video URL is required for video messages")
            return await send_video_message(to, video_url, caption)
            
        elif message_type == "location":
            lat = message_data.get("latitude")
            lng = message_data.get("longitude")
            name = message_data.get("name")
            address = message_data.get("address")
            if lat is None or lng is None:
                raise ValueError("Latitude and longitude are required for location messages")
            return await send_location_message(to, lat, lng, name, address)
            
        elif message_type == "template":
            template_name = message_data.get("template_name", message_data.get("template"))
            language_code = message_data.get("language_code", message_data.get("language", "en_US"))
            components = message_data.get("components")
            parameters = message_data.get("parameters")
            
            if not template_name:
                raise ValueError("Template name is required for template messages")
            
            return await send_template_message(
                to=to,
                template_name=template_name,
                language_code=language_code,
                components=components,
                parameters=parameters
            )
            
        elif message_type == "interactive":
            # Interactive message (buttons or lists)
            interactive_data = message_data.get("interactive")
            if not interactive_data:
                raise ValueError("Interactive data is required for interactive messages")
            
            return await send_interactive_message(to, interactive_data)
            
        else:
            raise ValueError(f"Unsupported message type: {message_type}")
            
    except Exception as e:
        logger.error(f"❌ Failed to send {message_type} message to {to}: {e}")
        raise