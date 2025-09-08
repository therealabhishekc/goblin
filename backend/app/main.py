from fastapi import FastAPI
from app.websocket import router as websocket_router
from app.whatsapp_webhook import router as whatsapp_router

app = FastAPI()

app.include_router(websocket_router)
app.include_router(whatsapp_router)
