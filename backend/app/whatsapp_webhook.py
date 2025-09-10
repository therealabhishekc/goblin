
from fastapi import APIRouter, Request, status, Query, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse
import os
import json
from app.redis_client import r
from app.whatsapp_api import send_template_message

router = APIRouter()

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")

@router.get("/webhook", response_class=PlainTextResponse)
def verify(
    hub_mode: str | None = Query(None, alias="hub.mode"),
    hub_challenge: str | None = Query(None, alias="hub.challenge"),
    hub_verify_token: str | None = Query(None, alias="hub.verify_token"),
):
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        return hub_challenge or ""
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhook")
async def whatsapp_webhook(request: Request):
    payload = await request.json()
    print("Incoming JSON payload:", (json.dumps(payload, indent=2)), flush=True)
    # WhatsApp webhook structure
    try:
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
        if not message_id:
            return JSONResponse(content={"status": "no_message_id"}, status_code=status.HTTP_200_OK)
            
        # Check Redis for deduplication (24 hour TTL) - only if Redis is available
        if r and r.get(message_id):
            print(f"Duplicate message detected: {message_id}", flush=True)
            return JSONResponse(content={"status": "duplicate"}, status_code=status.HTTP_200_OK)

        # Store message ID in Redis if available
        if r:
            try:
                r.setex(message_id, 21600, "1")  # 6 hours
            except Exception as e:
                print(f"Redis operation failed: {e}", flush=True)
        from_number = message["from"]
        
        # Only process if message type is 'text' and body is not empty
        if message.get("type") == "text":
            text = message.get("text", {}).get("body", "")
            if text and text.strip():  # Ensure text is not empty
                text = text.strip().lower()
                if text == "hi":
                    await send_template_message(from_number, "hello_world")
            else:
                print("Empty text message, ignoring", flush=True)
    except Exception as e:
        print("Webhook error:", e, flush=True)
        return JSONResponse(content={"error": str(e)}, status_code=status.HTTP_400_BAD_REQUEST)
    return JSONResponse(content={"status": "received"}, status_code=status.HTTP_200_OK)
