from prisma.enums import BotTypes
from fastapi import Request, Response
from app.services.chat import ChatService
from app.domain.requests import ChatRequest
from fastapi.exceptions import HTTPException
from app.api.dependencies import get_chat_repository


class ChatController:
    def __init__(self):
        self.chat_service = ChatService()
        self.chat_repo = get_chat_repository()
        pass

    async def handle_prompt(
        self,
        bot_id: str,
        conversation_id: str,
        chat_request: ChatRequest,
        request: Request,
        response: Response,
    ):
        bot = await self.chat_repo.get_bot(bot_id=bot_id)
        if not bot:
            raise HTTPException(404, "Bot not found")

        conversation = await self.chat_repo.get_or_create_conversation(
            bot_id=bot_id,
            conversation_id=conversation_id,
            chat_request=chat_request,
            request=request,
            response=response,
        )
        if not conversation:
            raise HTTPException(500, "Creating and Retrieving Conversation failed")
        conversation_id = conversation.id
        return self.chat_service.handle_chat(
            bot=bot,
            prompt=chat_request.prompt,
            conversation_id=conversation_id,
            chat_request=chat_request
        )
