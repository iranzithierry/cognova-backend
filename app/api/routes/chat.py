from fastapi import Response, Request
from app.services.chat import ChatService
from app.domain.requests import ChatRequest
from fastapi.responses import StreamingResponse
from fastapi import APIRouter, HTTPException, Body
from app.controllers.chat import ChatController

router = APIRouter()
chat_service = ChatService()



@router.post("/{bot_id}/chat/{conversation_id}", operation_id="chat")
async def chat(
    bot_id: str,
    request: Request,
    response: Response,
    conversation_id: str = None,
    chat_request: ChatRequest = Body(...)
):
    try:
        chat_controller = ChatController()
        streaming_response = await chat_controller.handle_prompt(
            bot_id=bot_id,
            conversation_id=conversation_id,
            chat_request=chat_request,
            request=request,
            response=response
        )
        return StreamingResponse(streaming_response, media_type="text/event-stream")
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))