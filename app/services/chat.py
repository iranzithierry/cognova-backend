import re
import json
from openai import OpenAI
from prisma.models import Bot, Chat
from app.domain.requests import ChatRequest
from typing import Dict, List, Any, AsyncGenerator, Literal, Optional
from app.infrastructure.ai.prompts.seller import SellerPromptGenerator
from app.infrastructure.ai.tools.functions.business import BusinessFunctions
from app.infrastructure.ai.tools.pydantic_tools.business import (
    get_all_business_functions,
)
from app.api.dependencies import (
    get_chat_repository,
    get_business_repository,
    logger,
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
        self._recursion_count = 0
        self.chat_request: ChatRequest = None
        self.business_functions: BusinessFunctions = None
        self.business_system_prompt = ""

    async def _get_prompt_generator(self, bot: Bot) -> tuple[str, Any]:
        """Get appropriate prompt generator based on bot type"""
        if bot.businessId:
            business_data = await self.business_repo.get_business_data(bot.businessId)
            generator = SellerPromptGenerator(
                business=business_data,
                config=business_data.configurations,
                locations=business_data.locations,
                operating_hours=business_data.operatingHours,
                mode=self.chat_request.chat_mode,
            )
            self.business_system_prompt = generator.generate_prompt()
            return self.business_system_prompt, business_data

    async def prepare_chat_context(
        self, bot: Bot, conversation_history: List[Chat]
    ) -> List[Dict[str, str]]:
        """Prepare chat context with system message and conversation history"""
        system_content, _ = await self._get_prompt_generator(bot)

        messages = [{"role": MessageRole.SYSTEM.value, "content": system_content}]
        messages.extend(
            [
                {
                    "role": chat.role,
                    "content": chat.content,
                    **(
                        {
                            "tool_calls": chat.toolCalls,
                        }
                        if chat.toolCalls
                        else {}
                    ),
                    **({"tool_call_id": chat.toolCallId} if chat.toolCallId else {}),
                }
                for chat in conversation_history
            ]
        )
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

            logger().info(f"EXECUTED TOOL: {str(tool_call)}")

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
                ),
            )
            await self._save_message(
                conversation_id,
                Message(
                    role=MessageRole.TOOL.value,
                    content=result,
                    toolCallId=tool_id,
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
            logger().error(f"Error saving message: {str(e)}", exc_info=True)
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
            async for response in self.handle_chat(
                bot,
                conversation_id,
                prompt="",
                chat_request=self.chat_request,
                inside=True,
            ):
                yield response

        except ToolExecutionError as e:
            yield self._stream_data({"error": str(e)})
        finally:
            self._recursion_count -= 1

    def _stream_data(self, data: Dict[str, Any]) -> str:
        """Format data for streaming"""
        if "error" in data:
            try:
                logger().error(
                    f"Error formatting stream data: {data["error"]}", exc_info=True
                )
            except:
                logger().error(f"Error formatting stream data: {data}", exc_info=True)
                pass
        return f"data: {json.dumps(data)}\n\n"

    def send_action(self, action: str):
        return self._stream_data({"action": action})

    async def handle_chat(
        self,
        bot: Bot,
        conversation_id: str,
        prompt: str,
        chat_request: ChatRequest = None,
        inside: bool = False,
    ) -> AsyncGenerator[str, None]:
        """Main chat handling method"""
        user_message = None
        self.chat_request = chat_request
        try:
            if prompt:
                user_message = await self._save_message(
                    conversation_id,
                    Message(
                        role=MessageRole.USER.value,
                        content=prompt,
                    ),
                )
            history = await self.chat_repo.get_chats(conversation_id)
            messages = await self.prepare_chat_context(bot, history)

            chat_params = {}
            if bot.businessId:
                self.business_functions = BusinessFunctions(bot.businessId)
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
            if not inside:
                yield self.send_action("thinking")
            if bot.model.aiProvider.provider == "cloudflare":
                chat_provider = CloudflareProvider(self.client, bot.model.name)
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
                        yield self.send_action("checking-inventory")

                    elif (
                        token.strip().startswith("<")
                        and len(assistant_message) < 2
                        and token.count("tool_call>") != 2
                    ):
                        is_collecting_tool_call = True
                        assistant_message += token
                        yield self.send_action("checking-inventory")
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
                    ),
                )
                if assistant_chat:
                    yield self._stream_data({"complete": True})
                    suggestions = await self._generate_question_suggestions(
                        bot, conversation_id
                    )
                    yield self._stream_data({"suggestions": suggestions})

        except Exception as e:
            yield self._stream_data({"error": f"Error processing chat: {str(e)}"})
            if user_message:
                await self.chat_repo.delete_chat(user_message.id)

    def _accumulate_tool_call(self, content: str) -> Dict[str, Any]:
        """Parse accumulated tool call content"""
        tool_call_match = re.search(r"<tool_call>(.*?)</tool_call>", content, re.DOTALL)
        tool_calls_str = "{}"
        try:
            if tool_call_match:
                tool_call_params = tool_call_match.group(1)
                tool_calls_str = (
                    tool_call_params.replace("None", "null").replace("'", '"').strip()
                )
            return json.loads(tool_calls_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid tool call content: {tool_calls_str}") from e

    def _parse_chunk(self, chunk: str) -> Dict[str, Any]:
        """Parse streaming chunk data"""
        try:
            if chunk.startswith("data: "):
                chunk = chunk[6:]
            return json.loads(chunk)
        except json.JSONDecodeError:
            return {"token": chunk}

    async def _generate_question_suggestions(
        self, bot: Bot, conversation_id: str
    ) -> List[str]:
        """Generate question suggestions based on conversation history"""
        try:
            recent_chats = await self.chat_repo.get_recent_chats(conversation_id, 4)
            if not recent_chats:
                return []

            messages = [
                Message(
                    role=chat.role,
                    content=chat.content,
                    toolCalls=chat.toolCalls,
                    toolCallId=chat.toolCallId,
                )
                for chat in recent_chats
            ]

            cf_provider = CloudflareProvider(
                OpenAI(
                    base_url="https://generative.ai.cognova.io",
                    api_key="sk-no-key-requireda",
                ),
                "@hf/nousresearch/hermes-2-pro-mistral-7b",
            )
            suggestions = await cf_provider.generate_suggestions(messages, self.business_system_prompt)

            return suggestions

        except Exception as e:
            logger().error(f"Error generating suggestions: {str(e)}")
            return []
