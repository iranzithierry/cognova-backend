from app.models import FeedbackType
from typing import Dict, Any, Optional
from fastapi.responses import StreamingResponse
from fastapi import APIRouter, HTTPException, Body
from app.services.chat import ChatService
from app.controllers.chat import ChatController

router = APIRouter()
chat_service = ChatService()

@router.post("/{bot_id}/chat/{conversation_id}", operation_id="chat")
async def chat(
    bot_id: str,
    conversation_id: Optional[str] = None,
    prompt: str = Body(...),
    metadata: str = Body(default=None)
):
    try:
        chat_controller = ChatController()
        response = chat_controller.handle_prompt(
            bot_id=bot_id,
            conversation_id=conversation_id,
            prompt=prompt
        )
        return StreamingResponse(response, media_type="text/event-stream")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))