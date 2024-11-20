from typing import Optional, Literal
from pydantic import BaseModel

class ChatRequest(BaseModel):
    prompt: str
    wa_phone_number: Optional[str] = None
    wa_profile_picture: Optional[str] = None
    wa_profile_name: Optional[str] = None
    chat_mode: Literal["whatsapp", "web"] = "web"