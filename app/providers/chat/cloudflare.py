import re
import json
from openai import OpenAI
from . import ChatProvider
from .types import (
    StreamResponse,
    StreamResponseType,
    ToolCall,
    ToolDefinition,
    ChatResponse,
    Completion,
    ToolParameter,
)
from app.config import Config
from app.tools import ToolService
from typing import List, Dict, Any, AsyncGenerator, Optional
from app.errors import StreamProcessingError, ToolProcessingError


class CloudflareProvider(ChatProvider):
    """
    CloudflareProvider handles chat completions using OpenAI's API through Cloudflare
    """

    def __init__(self, config: Config, client: OpenAI, model: str):
        self.config = config
        self.model = model
        self.client = client
        self.tools: List[ToolDefinition] = ToolService(self).tools

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

            completion = self.client.with_options(max_retries=1, timeout=60*2).chat.completions.create(**completion_params)
            print(completion)

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
        message = ""
        try:
            for chunk in completion:
                if chunk.response:
                    content = chunk.response
                    message += content
                    response = StreamResponse(
                        type=StreamResponseType.TOKEN, content=content
                    )
                    yield f"data: {json.dumps({'token': response.content})}\n\n"

            tool_call = await self._extract_tool_call(message)
            if tool_call:
                response = StreamResponse(
                    type=StreamResponseType.TOOL_CALL, content="", tool_call=tool_call
                )
                yield f"data: {json.dumps({'tool_calls': response.tool_call})}\n\n"

        except Exception as e:
            error_msg = f"Stream processing failed: {str(e)}"
            yield f"data: {json.dumps({'error': error_msg})}\n\n"
            raise StreamProcessingError(error_msg)

    async def _extract_tool_call(self, message: str) -> Optional[ToolCall]:
        """
        Extract and process tool calls from message

        Args:
            message: Complete message content

        Returns:
            ToolCall object if found, None otherwise

        Raises:
            ToolProcessingError: If tool call processing fails
        """
        try:
            tool_match = re.search(r"<tool_call>(.*?)</tool_call>", message, re.DOTALL)
            if not tool_match:
                return None

            tool_calls_str = tool_match.group(1)
            try:
                tool_calls: dict = json.loads(tool_calls_str)
            except json.JSONDecodeError:
                cleaned_str = tool_calls_str.replace("'", '"').replace("\n", "")
                tool_calls: dict = json.loads(cleaned_str)

            return ToolCall(
                name=tool_calls.get("name"), arguments=tool_calls.get("arguments", {})
            )

        except Exception as e:
            raise ToolProcessingError(f"Failed to process tool call: {str(e)}")

    def make_tool_object(self, tool_call: ToolCall) -> Dict[str, Any]:
        """
        Create a formatted tool call object

        Args:
            tool_call: ToolCall instance

        Returns:
            Formatted tool call object
        """
        return {
            "reason": "execute_tool",
            "function": {
                "name": tool_call.name,
                "arguments": json.dumps(tool_call.arguments),
            },
        }

    def _convert_tool_definition_to_dict(
        self, name: str, description: str, parameters: List[Dict[str, Any]]
    ) -> ToolDefinition:
        """
        Convert ToolDefinition to OpenAI-compatible dictionary format

        Args:
            tool_def: ToolDefinition instance

        Returns:
            Dictionary format of tool definition
        """
        tool_params = []
        for param in parameters:
            param_name = list(param.keys())[0]
            param_info: dict = param[param_name]

            tool_params.append(
                ToolParameter(
                    name=param_name,
                    type=param_info["type"],
                    description=param_info["description"],
                    required=param_info.get("required", False),
                )
            )

        return ToolDefinition(
            name=name, description=description, parameters=tool_params
        )


# def _convert_tool_definition_to_dict(tool_def: ToolDefinition) -> Dict[str, Any]:
#     """
#     Convert ToolDefinition to OpenAI-compatible dictionary format

#     Args:
#         tool_def: ToolDefinition instance

#     Returns:
#         Dictionary format of tool definition
#     """
#     properties = {}
#     required = []

#     for param in tool_def.parameters:
#         properties[param.name] = {
#             "type": param.type,
#             "description": param.description
#         }
#         if param.required:
#             required.append(param.name)

#     return {
#         "name": tool_def.name,
#         "description": tool_def.description,
#         "parameters": {
#             "type": "object",
#             "properties": properties,
#             "required": required
#         }
#     }
