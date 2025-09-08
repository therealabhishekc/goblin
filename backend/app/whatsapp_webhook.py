from fastapi import APIRouter, Request, status, Query, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse
import os

router = APIRouter()

VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "your_verify_token")

@router.get("/webhook", response_class=PlainTextResponse)
def verify(
    hub_mode: str | None = Query(None, alias="hub.mode"),
    hub_challenge: str | None = Query(None, alias="hub.challenge"),
    hub_verify_token: str | None = Query(None, alias="hub.verify_token"),
):
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        return hub_challenge or ""
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request):
    payload = await request.json()
    # Process WhatsApp message here
    # Save to DB, forward to WebSocket, etc.
    return JSONResponse(content={"status": "received"}, status_code=status.HTTP_200_OK)
