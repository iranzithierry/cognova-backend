import json
from openai import OpenAI
from app.domain.interfaces import (
    StreamResponse,
    StreamResponseType,
    Completion,
)
from . import ChatProvider
from app.core.config import Config
from typing import List, Dict, Any, AsyncGenerator, Optional
from app.domain.errors import StreamProcessingError, ToolProcessingError


class CloudflareProvider(ChatProvider):
    """
    CloudflareProvider handles chat completions using OpenAI's API through Cloudflare
    """

    def __init__(self, config: Config, client: OpenAI, model: str):
        self.config = config
        self.model = model
        self.client = client

    async def request(
        self, messages: List[Dict[str, str]], **kwargs: Any
    ) -> AsyncGenerator[str, None]:  # Changed return type to str
        """
        Process chat completion request with streaming support
        """
        try:
            completion_params = {
                "model": self.model,
                "messages": messages,
                "stream": True,
            }

            if kwargs:
                completion_params.update(kwargs)

            completion = self.client.with_options(
                max_retries=1, timeout=60 * 2
            ).chat.completions.create(**completion_params)

            async for response in self.stream(completion):
                yield response

        except Exception as e:
            error_msg = f"Chat completion failed: {str(e)}"
            yield f"data: {json.dumps({'error': error_msg})}\n\n"
            raise StreamProcessingError(error_msg)

    async def stream(self, completion: List[Completion]) -> AsyncGenerator[str, None]:
        """
        Process the completion stream and handle different response types
        """
        try:
            for chunk in completion:
                if chunk.response:
                    content = chunk.response
                    response = StreamResponse(
                        type=StreamResponseType.TOKEN, content=content
                    )
                    yield f"data: {json.dumps({'token': response.content})}\n\n"
        except Exception as e:
            error_msg = f"Stream processing failed: {str(e)}"
            yield f"data: {json.dumps({'error': error_msg})}\n\n"
            raise StreamProcessingError(error_msg)
