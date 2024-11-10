import json
from datetime import datetime
import datetime as base_datetime
from app.models import Vector
from typing import List, Tuple, Any
from app.db import Database, DatabaseError

class VectorRepository:
    def __init__(self, db: Database):
        self.db = db

    def create_vectors(self, vectors: List[Vector]) -> None:
        """Store vector embeddings in the database"""
        query = """
        INSERT INTO vectors (
            id, "workspaceId", "sourceId", embedding, "chunkContent",
            metadata, "chunkLength", "createdAt", "updatedAt"
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        vector_tuples = [
            (
                str(vector.id),
                str(vector.workspace_id),
                str(vector.source_id),
                json.dumps(vector.embedding),
                vector.chunk_content,
                json.dumps(vector.metadata),
                vector.chunk_length,
                datetime.now(base_datetime.timezone.utc), # For delay and knowing which inserted first
                vector.updated_at
            )
            for vector in vectors
        ]

        try:
            self.db.executemany(query, vector_tuples)
        except Exception as e:
            raise DatabaseError(f"Failed to create vectors: {str(e)}")
        
    def execute_search(
        self,
        query: str,
        params: List[Any]
    ) -> List[Tuple]:
        """Execute semantic search query"""
        try:
            results =  self.db.execute(query, params, fetch=True)
            return results
        except Exception as e:
            raise DatabaseError(f"Search query failed: {str(e)}")