from typing import Dict, Any
from app.services.chat import ChatService
from app.dependencies import get_sources_repo
from app.services.embeddings import EmbeddingService


class ChatController:
    def __init__(self):
        self.chat_service = ChatService()
        pass

    def handle_prompt(self, bot_id: str, conversation_id: str, prompt: str):
        source_ids = get_sources_repo().get_source_ids_of_bot(bot_id=bot_id)
        embedding_service = EmbeddingService()
        results = embedding_service.search_embeddings(
            query_text=prompt, source_ids=source_ids, top_k=5
        )
        source_urls = [
            source.metadata["source"] if "source" in source.metadata else None
            for source in results
        ]
        search_results = ""
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
            bot_id, conversation_id, prompt, search_results, source_urls
        )
