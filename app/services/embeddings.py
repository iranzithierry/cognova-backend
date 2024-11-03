import uuid
import json
from openai import OpenAI
from app.config import Config
from datetime import datetime
from app.models import Vector
from app.models import SearchResult
from typing import List, Tuple, Optional, Dict, Any
from app.repositories.vectors import VectorRepository
from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.dependencies import get_vector_repo, get_config

class EmbeddingService:
    def __init__(self):
        self.client = OpenAI(
            base_url=get_config().EMBEDDING_BASE_URL,
            api_key=get_config().EMBEDDING_API_KEY,
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=20
        )

    def create_embeddings(
        self,
        texts: str,
        batch: bool = True
    ) -> Tuple[List[str], List[List[float]]]:
        """Create embeddings for text content"""
        input_texts = self.text_splitter.split_text(texts) if batch else [texts]
        
        response = self.client.embeddings.create(
            input=input_texts,
            model=get_config().EMBEDDING_MODEL,
            dimensions=1024
        )
        
        embeddings = [data.embedding for data in response.data]
        return (input_texts, embeddings) if batch else ([texts], [embeddings[0]])

    def store_web_source_embeddings(
        self,
        workspace_id: str,
        source_id: str,
        chunks: List[str],
        embeddings: List[List[float]],
        metadata: Dict[str, Any]
    ) -> None:
        """Store embeddings for web source content"""
        vectors = []
        for chunk_content, embedding in zip(chunks, embeddings):
            vector = Vector(
                id=uuid.uuid4(),
                workspace_id=uuid.UUID(workspace_id),
                source_id=uuid.UUID(source_id),
                embedding=embedding,
                chunk_content=chunk_content,
                metadata=metadata,
                chunk_length=len(chunk_content),
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            vectors.append(vector)

        get_vector_repo().create_vectors(vectors)

    def search_embeddings(
        self,
        query_text: str,
        source_ids: List[str],
        top_k: int = 5,
        max_age_days: Optional[int] = None,
        content_types: Optional[List[str]] = None,
    ) -> List[SearchResult]:
        """
        Enhanced semantic search with improved ranking and filtering.
        
        Args:
            query_text: Search query text
            source_ids: List of source IDs to search within
            top_k: Number of results to return
            max_age_days: Optional maximum age of content in days
            content_types: Optional list of content types to filter by
            
        Returns:
            List of SearchResult objects with scores and metadata
        """
        try:
            # Generate query embedding
            _, [query_embedding] = self.create_embeddings(query_text, batch=False)
            
            # Build search query with dynamic filtering
            search_query = self._build_search_query(
                max_age_days=max_age_days,
                content_types=content_types
            )
            
            # Prepare query parameters
            query_params = self._prepare_search_params(
                query_embedding=query_embedding,
                query_text=query_text,
                source_ids=source_ids,
                max_age_days=max_age_days,
                content_types=content_types,
                top_k=top_k
            )
            
            # Execute search query
            results = get_vector_repo().execute_search(
                query=search_query,
                params=query_params
            )
            
            if not results:
                return []
            
            # Process and filter results
            processed_results = self._process_search_results(
                results=results,
                query_text=query_text,
                top_k=top_k
            )
            
            return processed_results

        except Exception as e:
            raise ValueError(f"Search failed: {str(e)}")

    def _build_search_query(
        self,
        max_age_days: Optional[int] = None,
        content_types: Optional[List[str]] = None
    ) -> str:
        """Build the search query with hybrid semantic and text search"""
        where_conditions = [
            "v.\"sourceId\" = ANY(%s)",
            "1 - (v.embedding <-> %s::vector) > 0.000000001",  # Similarity threshold
            "to_tsvector('english', v.\"chunkContent\") @@ plainto_tsquery('english', %s)"
        ]
        
        if max_age_days is not None:
            where_conditions.append("s.\"createdAt\" >= NOW() - INTERVAL '%s days'")
        
        if content_types:
            where_conditions.append("s.\"contentType\" = ANY(%s)")
        
        return f"""
        WITH RankedResults AS (
            SELECT 
                s.id AS "sourceId",
                v."chunkContent",
                v.metadata,
                v."createdAt",
                1 - (v.embedding <-> %s::vector) AS semantic_similarity,
                ts_rank(
                    to_tsvector('english', v."chunkContent"),
                    plainto_tsquery('english', %s)
                ) AS text_similarity
            FROM vectors v
            JOIN sources s ON s.id = v."sourceId"
            WHERE {' AND '.join(where_conditions)}
        )
        SELECT 
            "sourceId",
            "chunkContent",
            metadata,
            "createdAt",
            semantic_similarity,
            text_similarity,
            (semantic_similarity * 0.7 + text_similarity * 0.3) AS combined_score
        FROM RankedResults
        ORDER BY combined_score DESC
        LIMIT %s
        """

    def _prepare_search_params(
        self,
        query_embedding: List[float],
        query_text: str,
        source_ids: List[str],
        max_age_days: Optional[int],
        content_types: Optional[List[str]],
        top_k: int
    ) -> List[Any]:
        """Prepare parameters for the hybrid search query"""
        # Base parameters
        params = [
            json.dumps(query_embedding),  # For semantic similarity calculation
            query_text,                   # For text similarity calculation
            source_ids,
            json.dumps(query_embedding),  # For similarity threshold
            query_text,                   # For text search
        ]
        
        # Add optional filters
        if max_age_days is not None:
            params.append(max_age_days)
        
        if content_types:
            params.append(content_types)
        
        params.append(top_k * 2)  # Double limit for deduplication
        return params

    def _process_search_results(
        self,
        results: List[Tuple],
        query_text: str,
        top_k: int
    ) -> List[SearchResult]:
        """Process and filter search results"""
        seen_contents = set()
        filtered_results = []
        
        for row in results:
            content = row[1]  # chunk_content
            if content not in seen_contents:
                seen_contents.add(content)
                filtered_results.append(
                    SearchResult(
                        source_id=uuid.UUID(row[0]),
                        chunk_content=content,
                        metadata=row[2],
                        semantic_similarity=row[4],
                        text_similarity=row[5],
                        combined_score=row[6],
                        created_at=row[3]
                    )
                )
    
        return filtered_results[:top_k] if len(filtered_results) >= top_k else filtered_results
