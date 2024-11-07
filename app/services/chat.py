import json
from uuid import uuid4
from openai import OpenAI
from datetime import datetime
from app.config import Config
import datetime as base_datetime
from app.utils import generate_system_message
from app.tools.functions import ToolFunctions
from app.models import Chat, Bot, FeedbackType
from app.repositories.chats import ChatRepository
from typing import AsyncGenerator, Dict, Any, List
from app.providers.chat.cloudflare import CloudflareProvider
from app.dependencies import get_chat_repository, get_config


class ChatService:
    def __init__(self):
        self.chat_repo = get_chat_repository()
        self.config = get_config()
        self.client = OpenAI(
            base_url=self.config.OPENAI_BASE_URL,
            api_key=self.config.OPENAI_API_KEY,
        )

    def prepare_chat_context(
        self, bot: Bot, conversation_history: List[Chat], search_results: str
    ) -> List[Dict[str, str]]:
        messages = []

        messages.append(
            {
                "role": "system",
                "content": generate_system_message(
                    system_message=bot.system_message if bot.system_message else None,
                    bot_description=bot.description,
                    bot_name=bot.name,
                    search_results=search_results,
                ),
            }
        )

        messages.extend(
            [
                {"role": chat.role, "content": chat.content}
                for chat in conversation_history
            ]
        )

        return messages

    async def handle_tool_call(self, tool_calls: Dict[str, Any]) -> str:
        try:
            tool_functions = ToolFunctions(self.chat_repo.db)
            result = await tool_functions.execute_function(
                tool_calls["function"]["name"], tool_calls["function"]["arguments"]
            )
            return json.dumps(result)
        except Exception as e:
            return json.dumps({"error": f"Tool execution failed: {str(e)}"})

    async def handle_chat(
        self,
        bot_id: str,
        conversation_id: str,
        prompt: str,
        search_results: str = None,
        source_urls: list[str] = [],
    ) -> AsyncGenerator[str, None]:
        try:
            bot = self.chat_repo.get_bot(bot_id)
            if not bot:
                raise ValueError(f"Bot not found with id: {bot_id}")

            # Save user message
            user_message = Chat(
                id=uuid4(),
                conversation_id=conversation_id,
                role="user",
                content=prompt,
                tokens=len(prompt.split()),
                feedback=FeedbackType.NONE.value,
                source_urls=[],
                created_at=datetime.now(base_datetime.timezone.utc),
                updated_at=datetime.now(base_datetime.timezone.utc),
            )
            self.chat_repo.save_chat_message(user_message)

            history = self.chat_repo.get_chat_history(conversation_id)

            messages = self.prepare_chat_context(bot, history, search_results)
            chat_provider = CloudflareProvider(self.config, self.client, bot.model_name)

            assistant_message = ""

            async for chunk in chat_provider.request(messages):
                yield chunk
                try:
                    chunk_data = json.loads(chunk.replace("data: ", "").strip())
                    if "token" in chunk_data:
                        assistant_message += chunk_data["token"]
                    elif "tool_calls" in chunk_data:
                        tool_result = await self.handle_tool_call(
                            chunk_data["tool_calls"]
                        )
                        yield f"data: {json.dumps({'token': tool_result})}\n\n"
                        assistant_message += tool_result
                except json.JSONDecodeError:
                    continue

            # Save assistant message
            if assistant_message:
                assistant_chat = Chat(
                    id=uuid4(),
                    conversation_id=conversation_id,
                    role="assistant",
                    content=assistant_message.replace("<|im_end|>", ""),
                    tokens=len(assistant_message.split()),
                    feedback=FeedbackType.NONE.value,
                    source_urls=source_urls,
                    created_at=datetime.now(base_datetime.timezone.utc),
                    updated_at=datetime.now(base_datetime.timezone.utc),
                )
                saved_chat = self.chat_repo.save_chat_message(assistant_chat)

            # Send final message with sources
            yield f"data: {json.dumps({ 'complete': True,  'source_urls': source_urls,  'chat_id': str(saved_chat.id)})}\n\n"

            yield f"data: {json.dumps({ 'question_suggestions': [],  'chat_id': str(saved_chat.id)})}\n\n"

        except Exception as e:
            error_message = f"Error processing chat: {str(e)}"
            yield f"data: {json.dumps({'error': error_message})}\n\n"
            if user_message:
                self.chat_repo.delete_chat(str(user_message.id))
