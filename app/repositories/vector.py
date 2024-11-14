import json
from prisma import Prisma
from prisma.models import Vector
from typing import List, Any, Dict
from app.utils import generate_cuid, now
from app.domain.errors import PrismaExecutionError


class VectorRepository:
    def __init__(self, db: Prisma):
        self.db = db

    async def create_vectors(self, vectors: List[Dict[str, Any]]) -> None:
        """Store vector embeddings in the database using raw SQL"""
        try:
            for vector in vectors:
                query = """
                INSERT INTO vectors (
                    "id",
                    "workspaceId",
                    "sourceId",
                    embedding,
                    "chunkContent",
                    metadata,
                    "chunkLength",
                    "createdAt",
                    "updatedAt"
                )
                VALUES (
                    $1,
                    $2,
                    $3,
                    $4::vector,
                    $5,
                    $6::jsonb,
                    $7,
                    $8::timestamp,
                    $9::timestamp
                );
                """
                current_time = now()
                params = [
                    str(generate_cuid()),
                    str(vector["workspaceId"]),
                    str(vector["sourceId"]),
                    vector["embedding"],
                    vector["chunkContent"],
                    json.dumps(vector["metadata"]),
                    vector["chunkLength"],
                    current_time,
                    current_time,
                ]

                await self.db.execute_raw(query, *params)

        except Exception as e:
            raise PrismaExecutionError(f"Failed to create vectors: {str(e)}")

    async def execute_semantic_search(
        self,
        embedding: List[float],
        source_ids: List[str],
        limit: int = 5,
    ) -> List[Vector]:
        """
        Execute semantic search using cosine similarity
        Note: This assumes you have a PostgreSQL database with pgvector extension
        """
        try:

            results = await self.db.query_raw(
                SEMANTIC_SEARCH_QUERY,
                json.dumps(embedding),
                json.dumps(embedding),
                source_ids,
                limit,
            )

            return results
        except Exception as e:
            raise PrismaExecutionError(f"Semantic search query failed: {str(e)}")

    async def get_vectors_by_source_id(self, source_id: str) -> List[Vector]:
        """Get all vectors for a specific source"""
        try:
            vectors = await self.db.vector.find_many(where={"sourceId": source_id})
            return vectors
        except Exception as e:
            raise PrismaExecutionError(f"Failed to get vectors: {str(e)}")


SEMANTIC_SEARCH_QUERY = """
        WITH RankedResults AS (
            SELECT 
                v."sourceId",
                v."chunkContent",
                v.metadata,
                v."createdAt",
                1 - (v.embedding <-> $1::vector) AS similarity,
                ROW_NUMBER() OVER (
                    PARTITION BY v."sourceId" 
                    ORDER BY 1 - (v.embedding <-> $2::vector) DESC
                ) as rank
            FROM vectors v
            JOIN sources s ON s.id = v."sourceId"
            WHERE v."sourceId" = ANY($3)
        ),
        ContextualResults AS (
            SELECT 
                r1."sourceId",
                r1."chunkContent",
                r1.metadata,
                r1."createdAt",
                r1.similarity,
                ARRAY_AGG(
                    CASE 
                        WHEN r2.rank <= 2 AND r2.rank != r1.rank 
                        THEN r2."chunkContent" 
                    END
                ) FILTER (WHERE r2.rank <= 2 AND r2.rank != r1.rank) as context_chunks
            FROM RankedResults r1
            LEFT JOIN RankedResults r2 
                ON r1."sourceId" = r2."sourceId"
            WHERE r1.rank = 1
            GROUP BY 
                r1."sourceId",
                r1."chunkContent",
                r1.metadata,
                r1."createdAt",
                r1.similarity
        )
        SELECT 
            "sourceId",
            CASE 
                WHEN context_chunks IS NOT NULL AND array_length(context_chunks, 1) > 0
                THEN "chunkContent" || ' ... ' || array_to_string(context_chunks, ' ... ')
                ELSE "chunkContent"
            END as full_content,
            metadata,
            "createdAt",
            similarity
        FROM ContextualResults
        WHERE similarity > 0.001
        ORDER BY similarity DESC
        LIMIT $4;
        """
