import httpagentparser
from prisma import Prisma
from typing import List, Optional
from prisma.models import Chat, Bot
from app.utils import generate_cuid
from fastapi import Response, Request
from app.domain.requests import ChatRequest
from fastapi.exceptions import HTTPException
from app.domain.validators import CuidValidator
from app.domain.errors import PrismaExecutionError


class ChatRepository:
    def __init__(self, db: Prisma):
        self.db = db

    async def get_chats(self, conversation_id: str) -> List[Chat]:
        try:
            chats = await self.db.chat.find_many(
                where={"conversationId": conversation_id}, order={"createdAt": "asc"}
            )
            return chats
        except Exception as e:
            raise PrismaExecutionError(f"Failed to get chat history: {str(e)}")

    async def save_chat_message(self, chat: Chat) -> Chat:
        try:
            created_chat = await self.db.chat.create(data=chat)
            return created_chat
        except Exception as e:
            raise PrismaExecutionError(f"Failed to save chat message: {str(e)}")

    async def get_bot(self, bot_id: str) -> Optional[Bot]:
        try:
            bot = await self.db.bot.find_unique(
                where={"id": bot_id},
                include={"model": {"include": {"aiProvider": True}}},
            )
            return bot
        except Exception as e:
            raise PrismaExecutionError(f"Failed to get bot: {str(e)}")

    async def delete_chat(self, chat_id: str):
        try:
            await self.db.chat.delete(where={"id": chat_id})
        except Exception as e:
            raise PrismaExecutionError(f"Failed to delete chat: {str(e)}")
        
    async def delete_latest_message(self, conversationId: str, role: str = None):
        try:
            where = {"conversationId": conversationId}
            if role:
                where["role"] = role
            latest_message = await self.db.chat.find_first(
                where=where,
                order={"createdAt": "desc"}
            )
            if latest_message:
                await self.db.chat.delete(where={"id": latest_message.id})
        except Exception as e:
            raise PrismaExecutionError(f"Failed to delete latest message: {str(e)}")

    async def get_conversation(self, conversation_id: str):
        try:
            conversation = await self.db.conversation.find_first(
                where={"id": conversation_id}
            )
            if not conversation:
                print("No Conversation for ID", conversation_id)
            return conversation
        except Exception as e:
            raise PrismaExecutionError(f"Failed to get conversation: {str(e)}")

    async def create_conversation(
        self,
        bot_id: str,
        chat_request: ChatRequest,
        request: Request,
        response: Response,
        conversation_id=None,
    ):
        session_id = await self.get_or_create_session_id(request, response)
        conversation_data = {
            "botId": bot_id,
            "sessionId": session_id,
            "countryCode": request.headers.get("CF-IPCountry"),
        }
        if conversation_id is not None:
            if not CuidValidator.validate_cuid(conversation_id):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid conversation ID format. Must be a valid CUID.",
                )
            conversation_data["id"] = conversation_id

        conversation = await self.db.conversation.create(
            data=conversation_data,
            include={"bot": True},
        )

        return conversation

    async def get_or_create_conversation(
        self,
        bot_id: str,
        conversation_id: str,
        chat_request: ChatRequest,
        request: Request,
        response: Response,
    ):
        current_conversation = await self.get_conversation(conversation_id)
        if current_conversation:
            return current_conversation

        session_id = await self.get_or_create_session_id(request, response)

        existing_conversation = await self.db.conversation.find_first(
            where={"botId": bot_id, "sessionId": session_id},
            order={"createdAt": "desc"},
            include={"bot": True},
        )

        if existing_conversation:
            return existing_conversation

        return await self.create_conversation(
            bot_id=bot_id,
            chat_request=chat_request,
            request=request,
            response=response,
            conversation_id=conversation_id,
        )

    async def get_browser_metadata(self, request: Request):
        user_agent = request.headers.get("user-agent", "")
        parsed_agent = httpagentparser.detect(user_agent)

        return {
            "browser": parsed_agent.get("browser", {}).get("name"),
            "os": parsed_agent.get("os", {}).get("name"),
            "device": "mobile" if "mobile" in user_agent.lower() else "desktop",
        }

    async def get_or_create_session_id(
        self, request: Request, response: Response
    ) -> str:
        session_id = request.cookies.get("headless.session.id")

        if not session_id:
            session_id = generate_cuid()
            response.set_cookie(
                key="headless.session.id",
                value=session_id,
                httponly=True,
                secure=True,
                samesite="lax",
                max_age=30 * 24 * 60 * 60,  # 30 days
            )

        return session_id

    async def get_recent_chats(
        self, conversation_id: str, limit: int = 2
    ) -> List[Chat]:
        """Get the most recent chat messages for a conversation"""
        return await self.db.chat.find_many(
            where={"conversationId": conversation_id},
            order={"createdAt": "desc"},
            take=limit,
        )
