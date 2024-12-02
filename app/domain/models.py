from datetime import datetime
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

@dataclass
class ChatResponse:
    message: str
    error: Optional[str] = None

