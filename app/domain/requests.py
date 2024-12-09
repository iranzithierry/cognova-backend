from typing import Optional, Literal
from pydantic import BaseModel

class ChatRequest(BaseModel):
    prompt: str
    chat_mode: Literal["whatsapp", "web"] = "web"