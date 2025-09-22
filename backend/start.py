#!/usr/bin/env python3
"""
Startup script for the WhatsApp Business API application.
This script handles the Python path configuration and starts the uvicorn server.
"""
import sys
import os

# Add the backend directory to Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

if __name__ == "__main__":
    import uvicorn
    # Import the FastAPI app from the app module
    from app.main import app
    
    # Get port from environment or default to 8000
    port = int(os.environ.get("PORT", 8000))
    
    # Start the uvicorn server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=True
    )