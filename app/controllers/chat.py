import logging
from fastapi import Request, Response
from app.services.chat import ChatService
from app.domain.requests import ChatRequest
from fastapi.exceptions import HTTPException
from app.api.dependencies import get_chat_repository, logger
from app.domain.errors import ClientDisconnectError, PrismaExecutionError

class ChatController:
    def __init__(self):
        self.chat_service = ChatService()
        self.chat_repo = get_chat_repository()

    async def handle_prompt(
        self,
        bot_id: str,
        conversation_id: str,
        chat_request: ChatRequest,
        request: Request,
        response: Response,
    ):
        try:
            bot = await self.chat_repo.get_bot(bot_id=bot_id)
            if not bot:
                logger().warning(f"Bot not found: {bot_id}")
                raise HTTPException(404, "Bot not found")

            conversation = await self.chat_repo.get_or_create_conversation(
                bot_id=bot_id,
                conversation_id=conversation_id,
                chat_request=chat_request,
                request=request,
                response=response,
            )
            if not conversation:
                logger().error("Failed to create or retrieve conversation")
                raise HTTPException(500, "Creating and Retrieving Conversation failed")

            async def stream_with_error_handling():
                try:
                    async for chunk in self.chat_service.handle_chat(
                        bot=bot,
                        prompt=chat_request.prompt,
                        conversation_id=conversation.id,
                        chat_request=chat_request,
                    ):
                        if await request.is_disconnected():
                            logger().info(f"Client disconnected from conversation {conversation.id}")
                            raise ClientDisconnectError("Client disconnected")
                        yield chunk
                except ClientDisconnectError:
                    logger().info("Client disconnected, stopping stream")
                    await self.chat_repo.delete_latest_message(conversationId=conversation.id, role="user")
                except Exception as e:
                    logger().error(f"Error in stream: {str(e)}", exc_info=True)
                    yield self.chat_service._stream_data({"error": str(e)})

            return stream_with_error_handling()

        except Exception as e:
            if isinstance(e, PrismaExecutionError):
                logger().error(f"Prisma Execution error {str(e)}", exc_info=True)
                raise HTTPException(500, "Internal Server Error")
            if isinstance(e, HTTPException):
                logger().warning(f"HTTP Exception: {str(e)}")
                raise e
            
            logger().error(f"Error handling prompt: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))
