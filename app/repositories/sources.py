from uuid import uuid4
from typing import List, Tuple, Optional
from app.models import Source, UUID, Technique
from app.db import Database, DatabaseError


class SourceRepository:
    def __init__(self, db: Database):
        self.db = db

    def create_sources(self, sources: List[Source]) -> List[UUID]:
        """Create multiple sources in the database"""
        query = """
        INSERT INTO sources (
            id, "workspaceId", "techniqueId", title, url, status,
            "contentType", "contentLength", "contentHash", "syncTime", "updatedAt"
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        source_tuples = [
            (
                str(source.id),
                str(source.workspace_id),
                str(source.technique_id),
                source.title,
                source.url,
                source.status,
                source.content_type,
                source.content_length,
                source.content_hash,
                source.sync_time,
                source.updated_at,
            )
            for source in sources
        ]

        try:
            self.db.executemany(query, source_tuples)
            return [source.id for source in sources]
        except Exception as e:
            raise DatabaseError(f"Failed to create sources: {str(e)}")

    def get_source_ids_of_bot(self, bot_id: str):
        """Get source ids associated with a specific bot"""
        query = """
        SELECT "sourceId" FROM bot_sources WHERE "botId" = %s
        """
        try:
            results = self.db.execute(query, (bot_id,), fetch=True)
            return [row[0] for row in results]
        except Exception as e:
            raise DatabaseError(f"Failed to get source ids for bot: {str(e)}")
    
    def associate_sources_to_bot(self, bot_id: str, source_ids: List[str]):
        """Associate sources to a bot"""
        query = """
        INSERT INTO bot_sources (id, "botId", "sourceId") VALUES (%s, %s, %s)
        """
        bot_source_tuples = [(str(uuid4()), bot_id, source_id) for source_id in source_ids]
        try:
            self.db.executemany(query, bot_source_tuples)
        except Exception as e:
            raise DatabaseError(f"Failed to associate sources to bot: {str(e)}")

    def get_source_ids_of_workspace(self, workspace_id: str):
        """Get source ids by given workspace ids"""
        query = """
        SELECT id FROM sources WHERE "workspaceId" = %s
        """
        try:
            results = self.db.execute(query, (workspace_id,), fetch=True)
            return [row[0] for row in results]
        except Exception as e:
            raise DatabaseError(f"Failed to source ids: {str(e)}")

    def get_sources_by_ids(self, source_ids: List[str]) -> List[Source]:
        """Get sources by given source ids"""
        query = """
        SELECT * FROM sources WHERE id IN %s
        """
        try:
            results = self.db.execute(query, (tuple(source_ids),), fetch=True)
            return [Source(row) for row in results]
        except Exception as e:
            raise DatabaseError(f"Failed to get sources: {str(e)}")

    def get_technique(self, technique_name: str) -> Optional[Technique]:
        query = """
            SELECT * FROM techniques WHERE name = %s
        """
        try:
            result = self.db.execute(query, (technique_name,), fetch=True)
            return self._map_to_techniques(result[0]) if result else None
        except Exception as e:
            raise DatabaseError(f"Failed to get bot: {str(e)}")

    @staticmethod
    def _map_to_sources(row: Tuple) -> Source:
        return Source(
            id=row[0],
            workspace_id=row[1],
            technique_id=row[2],
            title=row[3],
            url=row[4],
            status=row[5],
            content_type=row[6],
            content_length=row[7],
            content_hash=row[8],
            sync_time=row[9],
            created_at=row[10],
            updated_at=row[11],
        )

    @staticmethod
    def _map_to_techniques(row: Tuple) -> Technique:
        return Technique(
            id=row[0],
            name=row[1],
            display_name=row[2],
            plan_id=row[3],
            createdAt=row[4],
            updatedAt=row[5],
        )
