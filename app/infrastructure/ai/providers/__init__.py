from abc import ABC, abstractmethod
from app.domain.interfaces import Completion
from typing import AsyncGenerator, List, Dict, Any

class ChatProvider(ABC):
    @abstractmethod
    async def request(
        self, 
        messages: List[Dict[str, str]], 
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Process and stream chat completion requests"""
        pass

    @abstractmethod
    async def stream(
        self,
        completion: List[Completion]
    ) -> AsyncGenerator[str, None]:
        """Handle streaming of completion responses"""
        pass