import json
from openai import OpenAI
from app.domain.interfaces import (
    StreamResponse,
    StreamResponseType,
    Completion,
)
from . import ChatProvider
from app.api.dependencies import logger
from app.domain.interfaces import Message
from typing import List, Dict, Any, AsyncGenerator
from app.domain.errors import StreamProcessingError


class CloudflareProvider(ChatProvider):
    """
    CloudflareProvider handles chat completions using OpenAI's API through Cloudflare
    """

    def __init__(self, client: OpenAI, model: str):
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

    async def generate_suggestions(
        self, conversation_history: List[Message], business_system_prompt: str
    ) -> List[str]:
        formatted_history = "\n".join(
            [f"{msg.role}: {msg.content}" for msg in conversation_history[-4:]]
        )
        prompt = f"""You are a helpful AI assistant. Use ONLY the provided business context and conversation history to generate 3 natural follow-up questions that a customer would ask. The questions must be strictly based on information present in the business details and previous conversation.

Note: For languages other than English or French, return an empty string.
IMPORTANT: Do not generate questions about features, services, or policies (like promotions, discounts, delivery options, payment methods) unless they are explicitly mentioned in the business context.

Business Context:
{business_system_prompt}

Conversation history:
{formatted_history}

Generate only customer questions, one per line, without any numbering or additional text. The questions should be specific to this business and conversation. Focus on:
- Questions about products or services explicitly mentioned
- Questions about business hours or locations provided
- Questions seeking clarification about information already discussed

Only generate questions that can be answered using the provided business context."""

        messages = [
            {"role": "system", "content": prompt},
        ]
        suggestions_str = ""
        async for chunk in self.request(
            messages=messages,
        ):
            chunk_data = self._parse_chunk(chunk=chunk)
            if "token" in chunk_data:
                suggestions_str += chunk_data["token"]

        suggestions = [q.strip() for q in suggestions_str.replace("<|im_end|>", "").replace("-", "").split("\n") if q.strip()][
            :3
        ]
        return suggestions

    def _parse_chunk(self, chunk: str) -> Dict[str, Any]:
        """Parse streaming chunk data"""
        try:
            if chunk.startswith("data: "):
                chunk = chunk[6:]
            return json.loads(chunk)
        except json.JSONDecodeError:
            return {"token": chunk}