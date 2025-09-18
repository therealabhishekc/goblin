
from fastapi import APIRouter, Request, status, Query, HTTPException, Depends
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlalchemy.orm import Session
import os
import json
from app.dynamodb_client import store_message_id, check_message_exists
from app.whatsapp_api import send_template_message
from app.services.whatsapp_service import WhatsAppService
from app.database.connection import get_database_session

router = APIRouter()

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")

@router.get("/webhook", response_class=PlainTextResponse)
def verify(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
):
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        return hub_challenge or ""
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhook")
async def whatsapp_webhook(
    request: Request, 
    db: Session = Depends(get_database_session)
):
    """
    Enhanced webhook handler using PostgreSQL and repository pattern.
    Now stores user profiles, messages, and analytics data.
    """
    payload = await request.json()
    print("Incoming JSON payload:", (json.dumps(payload, indent=2)), flush=True)
    
    try:
        # Process with new service layer
        with WhatsAppService(db) as service:
            result = service.process_incoming_message(payload)
            
            if result["status"] == "error":
                print(f"Service error: {result['message']}", flush=True)
                return JSONResponse(
                    content={"status": "error", "message": result["message"]}, 
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            if result["status"] == "duplicate":
                print(f"Duplicate message detected via PostgreSQL: {result.get('message_id')}", flush=True)
                return JSONResponse(
                    content={"status": "duplicate"}, 
                    status_code=status.HTTP_200_OK
                )
        
        # Legacy WhatsApp webhook structure for backward compatibility
        entry = payload["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]
        
        # Only process if this is a message event (not status update)
        if "messages" not in value:
            print("Ignoring non-message event", flush=True)
            return JSONResponse(content={"status": "ignored"}, status_code=status.HTTP_200_OK) 
            
        messages = value.get("messages", [])
        if not messages:
            print("No messages in payload", flush=True)
            return JSONResponse(content={"status": "no_messages"}, status_code=status.HTTP_200_OK)
            
        message = messages[0]
        message_id = message.get("id")
        from_number = message["from"]
        
        # Store in DynamoDB for fast deduplication (keep for performance)
        if message_id and store_message_id(message_id, ttl_hours=6):
            print(f"Message ID stored in DynamoDB for fast lookup: {message_id}", flush=True)
        
        # Business logic for automated responses
        if message.get("type") == "text":
            text = message.get("text", {}).get("body", "")
            if text and text.strip():
                text = text.strip().lower()
                if text == "hi":
                    await send_template_message(from_number, "hello_world")
                    # Update analytics for sent response
                    with WhatsAppService(get_database_session()) as analytics_service:
                        analytics_service.analytics_repo.increment_responses_sent()
            else:
                print("Empty text message, ignoring", flush=True)
                
        print(f"✅ Message processed successfully: {message_id}", flush=True)
        return JSONResponse(
            content={
                "status": "success", 
                "message": "Message processed and stored in PostgreSQL"
            }, 
            status_code=status.HTTP_200_OK
        )
            
    except Exception as e:
        print("Webhook error:", e, flush=True)
        return JSONResponse(content={"error": str(e)}, status_code=status.HTTP_400_BAD_REQUEST)
