import ast
import json
from dataclasses import dataclass
from enum import Enum
from openai import OpenAI
from prisma.enums import BotTypes
from prisma.models import Bot, Chat
from app.domain.requests import ChatRequest
from typing import Dict, List, Any, AsyncGenerator, Literal, Optional
from app.infrastructure.ai.prompts.seller import SellerPromptGenerator
from app.infrastructure.ai.prompts.default import DefaultPromptGenerator
from app.infrastructure.ai.tools.functions.business import BusinessFunctions
from app.infrastructure.ai.tools.pydantic_tools.business import (
    get_all_business_functions,
)
from app.api.dependencies import (
    get_chat_repository,
    get_business_repository,
)
from app.infrastructure.ai.providers.cloudflare import CloudflareProvider
from app.infrastructure.ai.providers.openai import OpenAIProvider
from app.domain.errors import ToolExecutionError
from app.domain.interfaces import MessageRole, ToolCall, Message
from app.utils import generate_cuid


class ChatService:
    MAX_RECURSION_DEPTH = 2  # Limit recursive function calls

    def __init__(self):
        self.chat_repo = get_chat_repository()
        self.business_repo = get_business_repository()
        self.client = None
        self.business_functions = BusinessFunctions()
        self._recursion_count = 0
        self.chat_request: ChatRequest = None

    async def _get_prompt_generator(self, bot: Bot, search_results: str = None) -> tuple[str, Any]:
        """Get appropriate prompt generator based on bot type"""
        if bot.type == BotTypes.PRODUCTS_BUYER_ASSISTANT.value and bot.businessId:
            business_data = await self.business_repo.get_business_data(bot.businessId)
            generator = SellerPromptGenerator(
                business=business_data,
                config=business_data.configurations,
                locations=business_data.locations,
                operating_hours=business_data.operatingHours,
                mode=self.chat_request.chat_mode
            )
            return generator.generate_prompt(), business_data
        else:
            generator = DefaultPromptGenerator(
                bot_name=bot.name,
                bot_description=bot.description,
                system_message=bot.description,
            )
            return generator.generate_prompt(search_results), None

    async def prepare_chat_context(
        self, bot: Bot, conversation_history: List[Chat], search_results: str = None
    ) -> List[Dict[str, str]]:
        """Prepare chat context with system message and conversation history"""
        system_content, _ = await self._get_prompt_generator(bot, search_results)

        messages = [{"role": MessageRole.SYSTEM.value, "content": system_content}]
        messages.extend([
            {
                "role": chat.role,
                "content": chat.content,
                **({
                    "tool_calls": chat.toolCalls,
                } if chat.toolCalls else {}),
                **({
                    "tool_call_id": chat.toolCallId
                } if chat.toolCallId else {})
            }
            for chat in conversation_history
        ])
        return messages

    def _get_tool_function(self, function_name: str):
        """Get the corresponding tool function based on name"""
        function_mapping = {
            "search_products": self.business_functions.search_products,
        }
        return function_mapping.get(function_name)

    async def handle_tool_call(self, tool_call: ToolCall, conversation_id: str) -> str:
        """Execute tool call and return results"""
        try:
            function = self._get_tool_function(tool_call.name)
            if not function:
                raise ToolExecutionError(f"Unknown function: {tool_call.name}")

            result = await function(**tool_call.arguments)

            if result in ([], None, "", "[]"):
                result = f"No results found."

            tool_id = generate_cuid()
            await self._save_message(
                conversation_id,
                Message(
                    role=MessageRole.ASSISTANT.value,
                    content="",
                    toolCalls=[
                        {
                            "id": tool_id,
                            "type": "function",
                            "function": {
                                "name": tool_call.name,
                                "arguments": json.dumps(tool_call.arguments),
                            },
                        }
                    ],
                    toolCallId=tool_id,
                    source_urls=[],
                ),
            )
            await self._save_message(
                conversation_id,
                Message(
                    role=MessageRole.TOOL.value,
                    content=result,
                    toolCallId=tool_id,
                    source_urls=[],
                ),
            )
        except Exception as e:
            raise ToolExecutionError(f"Tool execution failed: {str(e)}")

    async def _save_message(
        self, conversation_id: str, message: Message
    ) -> Optional[Chat]:
        """Save chat message to repository with duplicate check for empty tool results"""
        try:
            return await self.chat_repo.save_chat_message(
                {"conversationId": conversation_id, **message.to_dict()}
            )
            
        except Exception as e:
            print(f"Error saving message: {str(e)}")
            return None

    async def _handle_tool_response(
        self,
        bot: Bot,
        conversation_id: str,
        tool_call: Dict[str, Any],
    ) -> AsyncGenerator[str, None]:
        """Handle tool execution and subsequent chat responses"""
        try:
            if self._recursion_count >= self.MAX_RECURSION_DEPTH:
                yield self._stream_data(
                    {"warning": "Maximum tool call recursion depth reached"}
                )
                return

            self._recursion_count += 1
            await self.handle_tool_call(ToolCall.from_dict(tool_call), conversation_id)
            async for response in self.handle_chat(bot, conversation_id, prompt="", chat_request=self.chat_request):
                yield response

        except ToolExecutionError as e:
            yield self._stream_data({"error": str(e)})
        finally:
            self._recursion_count -= 1

    def _stream_data(self, data: Dict[str, Any]) -> str:
        """Format data for streaming"""
        return f"data: {json.dumps(data)}\n\n"

    async def handle_chat(
        self,
        bot: Bot,
        conversation_id: str,
        prompt: str,
        chat_request: ChatRequest = None,
        search_results: str = None,
        source_urls: List[str] = None,
    ) -> AsyncGenerator[str, None]:
        """Main chat handling method"""
        user_message = None
        source_urls = source_urls or []
        self.chat_request = chat_request
        try:
            if prompt:
                user_message = await self._save_message(
                    conversation_id,
                    Message(
                        role=MessageRole.USER.value,
                        content=prompt,
                        source_urls=source_urls,
                    ),
                )
            history = await self.chat_repo.get_chats(conversation_id)
            messages = await self.prepare_chat_context(bot, history, search_results)

            chat_params = {}
            if bot.type == BotTypes.PRODUCTS_BUYER_ASSISTANT.value:
                chat_params.update(
                    {
                        "tool_choice": "auto",
                        "tools": get_all_business_functions(),
                        "temperature": 0.0,
                    }
                )

            chat_provider = None
            self.client = OpenAI(
                base_url=bot.model.aiProvider.endpointUrl,
                api_key=bot.model.aiProvider.apiKey,
            )
            if bot.model.aiProvider.provider == "cloudflare":
                chat_provider = CloudflareProvider(self.client, bot.model.name
                )
            elif bot.model.aiProvider.provider == "openai":
                chat_provider = OpenAIProvider(self.client, bot.model.name)
            else:
                # :TODO Throw an error
                pass

            assistant_message = ""
            is_collecting_tool_call = False

            async for chunk in chat_provider.request(messages, **chat_params):
                chunk_data = self._parse_chunk(chunk)

                if "error" in chunk_data:
                    yield self._stream_data({"error": chunk_data["error"]})
                    continue

                if "token" in chunk_data:
                    token: str = chunk_data["token"].replace("<|im_end|>", "")
                    if token.count("tool_call") == 2:
                        is_collecting_tool_call = True
                    elif (
                            token.strip().startswith("<")
                            and len(assistant_message) < 2
                        ):
                            is_collecting_tool_call = True
                            assistant_message += token
                            continue

                    if is_collecting_tool_call:
                        assistant_message += token
                        if "</tool_call>" in assistant_message:
                            is_collecting_tool_call = False
                            tool_call = self._accumulate_tool_call(assistant_message)
                            async for response in self._handle_tool_response(
                                bot, conversation_id, tool_call
                            ):
                                yield response
                        continue

                    assistant_message += token
                    yield self._stream_data({"token": token})

            if "<tool_call>" not in assistant_message:
                assistant_chat = await self._save_message(
                    conversation_id,
                    Message(
                        role=MessageRole.ASSISTANT.value,
                        content=assistant_message,
                        source_urls=source_urls,
                    ),
                )

                if assistant_chat:
                    yield self._stream_data(
                        {
                            "complete": True,
                            "source_urls": source_urls,
                            "question_suggestions": [],
                        }
                    )

        except Exception as e:
            yield self._stream_data({"error": f"Error processing chat: {str(e)}"})
            if user_message:
                await self.chat_repo.delete_chat(user_message.id)

    def _accumulate_tool_call(self, content: str) -> Dict[str, Any]:
        """Parse accumulated tool call content"""
        clean_content = (
            content.replace("<tool_call>", "")
            .replace("</tool_call>", "")
            .replace("None", "null")
            .replace("'", '"')
            .strip()
        )
        try:
            return json.loads(clean_content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid tool call content: {clean_content}") from e

    def _parse_chunk(self, chunk: str) -> Dict[str, Any]:
        """Parse streaming chunk data"""
        try:
            if chunk.startswith("data: "):
                chunk = chunk[6:]
            return json.loads(chunk)
        except json.JSONDecodeError:
            return {"token": chunk}
