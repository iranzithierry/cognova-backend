import json
from openai import OpenAI
from . import ChatProvider
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk
from app.domain.interfaces import StreamResponse, StreamResponseType, Message
from typing import List, Dict, Any, AsyncGenerator
from app.domain.errors import StreamProcessingError


class OpenAIProvider(ChatProvider):
    """
    OpenAIProvider handles chat completions using OpenAI's direct API
    """

    def __init__(self, client: OpenAI, model: str):
        self.model = model
        self.client = client

    async def request(
        self, messages: List[Message], **kwargs: Any
    ) -> AsyncGenerator[str, None]:
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
            raise StreamProcessingError(error_msg)

    async def stream(
        self, completion: List[ChatCompletionChunk]
    ) -> AsyncGenerator[str, None]:
        """
        Process the completion stream and handle different response types
        """
        function_call = None
        function_name = ""
        function_arguments = ""
        stream_ended = False
        try:
            for chunk in completion:
                if hasattr(chunk.choices[0].delta, "content"):
                    content = chunk.choices[0].delta.content
                    if content:
                        response = StreamResponse(
                            type=StreamResponseType.TOKEN, content=content
                        )
                        yield f"data: {json.dumps({'token': response.content})}\n\n"

                if hasattr(chunk.choices[0].delta, "tool_calls"):
                    tool_calls = chunk.choices[0].delta.tool_calls
                    if tool_calls:
                        function_call = tool_calls[0].function
                        function_name += function_call.name if function_call.name  else ""
                        function_arguments += function_call.arguments if function_call.arguments else ""
                    if chunk.choices[0].finish_reason == "tool_calls":
                        stream_ended = True

                    if stream_ended:
                        function_name = f'"{function_name}"'
                        response = StreamResponse(
                            type=StreamResponseType.TOKEN,
                            content="""<tool_call>{"name": """
                            + function_name
                            + ""","arguments": """
                            + function_arguments
                            + """}</tool_call>""",
                        )
                        yield f"data: {json.dumps({'token': response.content})}\n\n"
        except Exception as e:
            error_msg = f"Stream processing failed: {str(e)}"
            raise StreamProcessingError(error_msg)
