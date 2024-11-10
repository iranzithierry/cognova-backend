import json
from datetime import datetime
import datetime as base_datetime
from app.logger import logger
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
                datetime.now(base_datetime.timezone.utc),
                vector.updated_at
            )
            for vector in vectors
        ]

        try:
            self.db.executemany(query, vector_tuples)
        except Exception as e:
            raise DatabaseError(f"Failed to create vectors: {str(e)}")
        
class VectorRepository:
    def __init__(self, db: Database):
        self.db = db

    def execute_search(
        self,
        query: str,
        params: List[Any]
    ) -> List[Tuple]:
        """Execute semantic search query with proper error handling"""
        try:
            # Input validation
            if not query or not query.strip():
                return []
            
            if not params or not isinstance(params, list):
                return []

            # Execute query and immediately convert results to list
            results = self.db.execute(query, params, fetch=True)
            
            # Handle None results
            if results is None:
                return []
                
            return results

        except DatabaseError as e:
            logger.error(f"Database search error: {str(e)}")
            raise DatabaseError(f"Search query failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in execute_search: {str(e)}")
            raise DatabaseError(f"Search query failed: {str(e)}")