from fastapi import FastAPI
from fastapi.responses import JSONResponse
import os

app = FastAPI()

@app.get("/health")
def health_check():
	return JSONResponse(content={"status": "ok"}, status_code=200)

@app.get("/")
def root():
	return {"message": "WhatsApp Business API Backend is running"}

# Only include routers if their dependencies are available
try:
	from app.websocket import router as websocket_router
	app.include_router(websocket_router)
	print("WebSocket router loaded", flush=True)
except Exception as e:
	print(f"WebSocket router failed to load: {e}", flush=True)

try:
	from app.whatsapp_webhook import router as whatsapp_router
	app.include_router(whatsapp_router)
	print("WhatsApp webhook router loaded", flush=True)
except Exception as e:
	print(f"WhatsApp webhook router failed to load: {e}", flush=True)
