from typing import Optional
from pydantic import BaseModel

class ChatRequest(BaseModel):
    prompt: str
    wa_phone_number: Optional[str]
    wa_profile_picture: Optional[str]
    wa_profile_name: Optional[str]