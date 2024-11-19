from fastapi import Request, Response
from app.services.chat import ChatService
from fastapi.exceptions import HTTPException
from app.services.vector import VectorService
from app.api.dependencies import get_chat_repository, get_sources_repo


class ChatController:
    def __init__(self):
        self.chat_service = ChatService()
        self.vector_service = VectorService()
        self.chat_repo = get_chat_repository()
        self.sources_repo = get_sources_repo()
        pass

    async def handle_prompt(
        self,
        bot_id: str,
        conversation_id: str,
        prompt: str,
        request: Request,
        response: Response,
    ):
        bot = await self.chat_repo.get_bot(bot_id=bot_id)
        if not bot:
            raise HTTPException(404, "Bot not found")

        conversation = await self.chat_repo.get_or_create_conversation(
            bot_id=bot_id,
            conversation_id=conversation_id,
            request=request,
            response=response,
        )
        if not conversation:
            raise HTTPException(500, "Creating and Retrieving Conversation failed")
        conversation_id = conversation.id

        results = []
        source_urls = []
        search_results = ""
        if bot.businessId is None:
            print("Retrieving Sources")
            source_ids = await self.sources_repo.get_source_ids_of_bot(bot_id=bot_id)
            # :TODO Caching in redis bot and their source ids
            results = await self.vector_service.search_embeddings(
                query_text=prompt, source_ids=source_ids, top_k=5
            )
            source_urls = [
                source.metadata["source"] if "source" in source.metadata else None
                for source in results
            ]
            for source in results:
                search_results += f"""
                ```
                - accuracy: {source.semantic_similarity}
                - title: {source.metadata["title"] if "title" in source.metadata else None}
                - description: {source.metadata["description"]  if "description" in source.metadata else None}
                - url: {source.metadata["source"] if "source" in source.metadata else None}
                - text: {source.chunk_content}
                ```
                """
        return self.chat_service.handle_chat(
            bot=bot,
            prompt=prompt,
            source_urls=source_urls,
            search_results=search_results,
            conversation_id=conversation_id,
        )
