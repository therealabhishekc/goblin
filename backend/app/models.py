from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class Message(BaseModel):
    message_id: str
    chat_id: str
    sender: str
    content: str
    timestamp: datetime
    type: str = "text"  # or "media"
    media_url: Optional[str] = None

class Chat(BaseModel):
    chat_id: str
    participants: List[str]
    last_message: Optional[Message] = None
