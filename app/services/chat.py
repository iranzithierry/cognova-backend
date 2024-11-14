import json
from openai import OpenAI
from prisma.models import Bot, Chat
from prisma.enums import ChatFeedback
from app.utils import generate_system_message
from app.tools.functions import ToolFunctions
from typing import Dict, List, Any, AsyncGenerator
from app.api.dependencies import get_chat_repository, get_config
from app.infrastructure.external.ai_providers.cloudflare import CloudflareProvider


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
                    system_message=bot.systemMessage if bot.systemMessage else None,
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
        bot: Bot,
        conversation_id: str,
        prompt: str,
        search_results: str = None,
        source_urls: list[str] = [],
    ) -> AsyncGenerator[str, None]:
        
        user_message = None
        try:
            user_message = await self.chat_repo.save_chat_message(
                {
                    "conversationId": conversation_id,
                    "role": "user",
                    "content": prompt,
                    "tokens": len(prompt.split()),
                    "feedback": ChatFeedback.NONE.value,
                    "sourceURLs": [],
                }
            )

            history = await self.chat_repo.get_chats(conversation_id)
            messages = self.prepare_chat_context(bot, history, search_results)

            chat_provider = CloudflareProvider(self.config, self.client, bot.model.name)

            assistant_message = ""

            async for chunk in chat_provider.request(messages):
                yield chunk.replace("<|im_end|>", "")
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

            if assistant_message:
                assistant_chat = await self.chat_repo.save_chat_message(
                    {
                        "conversationId": conversation_id,
                        "role": "assistant",
                        "content": assistant_message.replace("<|im_end|>", ""),
                        "tokens": len(assistant_message.split()),
                        "feedback": ChatFeedback.NONE.value,
                        "sourceURLs": source_urls,
                    }
                )

            if assistant_chat:
                yield f"data: {json.dumps({ 'complete': True,  'source_urls': source_urls})}\n\n"
                yield f"data: {json.dumps({ 'question_suggestions': []})}\n\n"

        except Exception as e:
            error_message = f"Error processing chat: {str(e)}"
            yield f"data: {json.dumps({'error': error_message})}\n\n"
            if user_message:
                await self.chat_repo.delete_chat(user_message.id)
