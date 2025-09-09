from fastapi import FastAPI
from fastapi.responses import JSONResponse
from app.websocket import router as websocket_router
from app.whatsapp_webhook import router as whatsapp_router

app = FastAPI()

@app.get("/health")
def health_check():
	return JSONResponse(content={"status": "ok"}, status_code=200)

app.include_router(websocket_router)
app.include_router(whatsapp_router)
