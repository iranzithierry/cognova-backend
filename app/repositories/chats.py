import uuid
from datetime import datetime
import datetime as base_datetime
from app.db import Database, DatabaseError
from typing import List, Optional, Dict, Any, Tuple
from app.models import Bot, Chat, Conversation, FeedbackType

class ChatRepository:
    def __init__(self, db: Database):
        self.db = db

    def create_conversation(self, bot_id: str, metadata: Dict[str, Any]) -> Conversation:
        query = """
        INSERT INTO conversations (id, "botId", browser, os, device, "countryCode", "createdAt", "updatedAt")
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING *
        """
        now = datetime.now(base_datetime.timezone.utc)
        values = (
            str(uuid.uuid4()),
            bot_id,
            metadata.get('browser'),
            metadata.get('os'),
            metadata.get('device'),
            metadata.get('country_code'),
            now,
            now
        )
        
        try:
            result = self.db.execute(query, values, fetch=True)
            if not result:
                raise DatabaseError("Failed to create conversation")
            return self._map_to_conversation(result[0])
        except Exception as e:
            raise DatabaseError(f"Failed to create conversation: {str(e)}")

    def get_chat_history(self, conversation_id: str) -> List[Chat]:
        query = """
        SELECT * FROM chats 
        WHERE "conversationId" = %s 
        ORDER BY "createdAt" ASC
        """
        try:
            results = self.db.execute(query, (conversation_id,), fetch=True)
            return [self._map_to_chat(row) for row in results]
        except Exception as e:
            raise DatabaseError(f"Failed to get chat history: {str(e)}")

    def save_chat_message(self, chat: Chat) -> Chat:
        query = """
        INSERT INTO chats (id, "conversationId", role, content, tokens, feedback, "sourceURLs", "createdAt", "updatedAt")
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING *
        """
        values = (
            str(chat.id),
            str(chat.conversation_id),
            chat.role,
            chat.content,
            chat.tokens,
            chat.feedback,
            chat.source_urls,
            chat.created_at,
            chat.updated_at
        )
        
        try:
            result = self.db.execute(query, values, fetch=True)
            return self._map_to_chat(result[0])
        except Exception as e:
            raise DatabaseError(f"Failed to save chat message: {str(e)}")

    def get_bot(self, bot_id: str) -> Optional[Bot]:
        query = """
        SELECT b.*, m."slugName" as model_slug
        FROM bots b
        LEFT JOIN models m ON b."modelId" = m.id
        WHERE b.id = %s
        """
        try:
            result = self.db.execute(query, (bot_id,), fetch=True)
            return self._map_to_bot(result[0]) if result else None
        except Exception as e:
            raise DatabaseError(f"Failed to get bot: {str(e)}")

    def delete_chat(self, chat_id):
        query = """
        DELETE FROM chats where id = %s
        """

        try:
            self.db.execute(query, (chat_id,), fetch=False)
        except Exception as e:
            raise DatabaseError(f"Failed to delete chat: {str(e)}")
        
    def update_chat_feedback(self, chat_id: str, feedback_type: FeedbackType) -> Chat:
            """Update feedback for a chat message"""
            query = """
            UPDATE chats 
            SET feedback = %s, 
                "updatedAt" = %s 
            WHERE id = %s 
            RETURNING *
            """
            try:
                result = self.db.execute(
                    query, 
                    (feedback_type.value, datetime.now(base_datetime.timezone.utc), chat_id), 
                    fetch=True
                )
                if not result:
                    raise DatabaseError(f"Chat not found with id: {chat_id}")
                return self._map_to_chat(result[0])
            except Exception as e:
                raise DatabaseError(f"Failed to update chat feedback: {str(e)}")
            
    def get_chat_sources(self, chat_id: str) -> List[str]:
        """Retrieve source URLs for a chat message"""
        query = """
        SELECT "sourceURLs" 
        FROM chats 
        WHERE id = %s
        """
        try:
            result = self.db.execute(query, (chat_id,), fetch=True)
            return result[0][0] if result else []
        except Exception as e:
            raise DatabaseError(f"Failed to get chat sources: {str(e)}") 
              
    @staticmethod
    def _map_to_conversation(row: Tuple) -> Conversation:
        return Conversation(
            id=row[0],
            bot_id=row[1],
            browser=row[2],
            os=row[3],
            device=row[4],
            country_code=row[5],
            generated_category=row[6],
            created_at=row[7],
            updated_at=row[8]
        )

    @staticmethod
    def _map_to_chat(row: Tuple) -> Chat:
        return Chat(
            id=row[0],
            conversation_id=row[1],
            role=row[2],
            content=row[3],
            tokens=row[4],
            feedback=FeedbackType(row[5] if row[5] else "none"),
            source_urls=row[6] or [],
            created_at=row[7],
            updated_at=row[8]
        )

    @staticmethod
    def _map_to_bot(row: Tuple) -> Bot:
        return Bot(
            id=row[0],
            workspace_id=row[1],
            name=row[2],
            description=row[3],
            language=row[4],
            system_message=row[5],
            placeholder_message=row[6],
            welcome_message=row[7],
            starter_questions=row[8],
            model_id=row[9],
            model_slug=row[12],
            created_at=row[10],
            updated_at=row[11]
        )

