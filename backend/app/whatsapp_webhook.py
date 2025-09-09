import redis
from fastapi import APIRouter, Request, status, Query, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse
import os
import httpx
import json

router = APIRouter()

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

r = redis.Redis.from_url(REDIS_URL)

@router.get("/webhook", response_class=PlainTextResponse)
def verify(
    hub_mode: str | None = Query(None, alias="hub.mode"),
    hub_challenge: str | None = Query(None, alias="hub.challenge"),
    hub_verify_token: str | None = Query(None, alias="hub.verify_token"),
):
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        return hub_challenge or ""
    raise HTTPException(status_code=403, detail="Verification failed")

async def send_template_message(to: str, template_name: str):
    url = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": "en_US"}
        }
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()

@router.post("/webhook")
async def whatsapp_webhook(request: Request):
    payload = await request.json()
    print("Incoming JSON payload:", (json.dumps(payload, indent=2)), flush=True)
    # WhatsApp webhook structure
    try:
        entry = payload["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]
        messages = value.get("messages", [])
        if messages:
            message = messages[0]
            message_id = message.get("id")
            if not message_id:
                return JSONResponse(content={"status": "no_message_id"}, status_code=status.HTTP_200_OK)
            # Check Redis for deduplication (24 hour TTL)
            if r.get(message_id):
                print(f"Duplicate message detected: {message_id}", flush=True)
                return JSONResponse(content={"status": "duplicate"}, status_code=status.HTTP_200_OK)
            r.setex(message_id, 86400, "1")  # 24 hours
            from_number = message["from"]
            text = message.get("text", {}).get("body", "")
            text = text.strip().lower()
            if text == "hi":
                await send_template_message(from_number, "hello_world")
    except Exception as e:
        print("Webhook error:", e, flush=True)
        return JSONResponse(content={"error": str(e)}, status_code=status.HTTP_400_BAD_REQUEST)
    return JSONResponse(content={"status": "received"}, status_code=status.HTTP_200_OK)
