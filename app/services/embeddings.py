import uuid
import json
from typing import List, Tuple, Optional, Dict, Any, NamedTuple
from datetime import datetime, timedelta
from openai import OpenAI
from app.utils import clean_text_for_search
from app.models import Vector, SearchResult
from app.repositories.vectors import VectorRepository
from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.dependencies import get_vector_repo, get_config


class ChunkContext(NamedTuple):
    """Stores context information about chunk position in document"""

    start_position: int
    end_position: int
    section_title: Optional[str]
    preceding_context: str
    following_context: str


class EnhancedSearchResult(SearchResult):
    context: ChunkContext


class EmbeddingService:
    def __init__(self):
        self.client = OpenAI(
            base_url=get_config().EMBEDDING_BASE_URL,
            api_key=get_config().EMBEDDING_API_KEY,
        )
        # Increased chunk overlap to capture more context
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,  # Increased overlap
            separators=[
                "\n## ",
                "\n### ",
                "\n\n",
                "\n",
                ". ",
                "? ",
                "! ",
            ],
        )

    def create_embeddings(
        self, texts: str, batch: bool = True
    ) -> Tuple[List[str], List[List[float]], List[ChunkContext]]:
        """Create embeddings with enhanced context tracking"""
        original_text = texts
        texts = clean_text_for_search(texts)
        input_texts = self.text_splitter.split_text(texts) if batch else [texts]

        # Track context for each chunk
        chunk_contexts = []
        for chunk in input_texts:
            start_pos = original_text.find(chunk)
            end_pos = start_pos + len(chunk)

            # Get surrounding context
            preceding_context = original_text[
                max(0, start_pos - 200) : start_pos
            ].strip()
            following_context = original_text[
                end_pos : min(len(original_text), end_pos + 200)
            ].strip()

            # Try to identify section title
            section_title = self._extract_section_title(original_text, start_pos)

            chunk_contexts.append(
                ChunkContext(
                    start_position=start_pos,
                    end_position=end_pos,
                    section_title=section_title,
                    preceding_context=preceding_context,
                    following_context=following_context,
                )
            )

        response = self.client.embeddings.create(
            input=input_texts, model=get_config().EMBEDDING_MODEL, dimensions=1024
        )

        embeddings = [data.embedding for data in response.data]
        if batch:
            return input_texts, embeddings, chunk_contexts
        return [texts], [embeddings[0]], [chunk_contexts[0]]

    def _extract_section_title(self, text: str, chunk_start: int) -> Optional[str]:
        """Extract the nearest preceding section title"""
        text_before = text[:chunk_start]
        header_markers = ["# ", "## ", "### "]

        for marker in header_markers:
            last_header_pos = text_before.rfind(f"\n{marker}")
            if last_header_pos != -1:
                header_end = text_before.find("\n", last_header_pos + 1)
                if header_end == -1:
                    header_end = len(text_before)
                return text_before[last_header_pos:header_end].strip()
        return None

    def store_web_source_embeddings(
        self,
        workspace_id: str,
        source_id: str,
        chunks: List[str],
        embeddings: List[List[float]],
        chunk_contexts: List[ChunkContext],
        metadata: Dict[str, Any]
    ) -> None:
        """Store embeddings with flattened context information in metadata"""
        vectors = []
        for chunk_content, embedding, context in zip(chunks, embeddings, chunk_contexts):
            enhanced_metadata = {
                **metadata,
                "start_position": context.start_position,
                "end_position": context.end_position,
                "section_title": context.section_title,
                "preceding_context": context.preceding_context,
                "following_context": context.following_context
            }
            
            vector = Vector(
                id=uuid.uuid4(),
                workspace_id=uuid.UUID(workspace_id),
                source_id=uuid.UUID(source_id),
                embedding=embedding,
                chunk_content=clean_text_for_search(chunk_content),
                metadata=enhanced_metadata,
                chunk_length=len(chunk_content),
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            vectors.append(vector)

        get_vector_repo().create_vectors(vectors)

    def _build_search_query(
            self,
            max_age_days: Optional[int] = None,
            content_types: Optional[List[str]] = None
        ) -> str:
            """Improved search query with better deduplication and relevance threshold"""
            base_conditions = [
                "v.\"sourceId\" = ANY(%s)",
            ]
            
            if max_age_days is not None:
                base_conditions.append("s.\"createdAt\" >= NOW() - INTERVAL '%s days'")
            
            if content_types:
                base_conditions.append("s.\"contentType\" = ANY(%s)")
            
            return f"""
            WITH RankedResults AS (
                SELECT 
                    v."sourceId",
                    v."chunkContent",
                    v.metadata,
                    v."createdAt",
                    1 - (v.embedding <-> %s::vector) AS similarity,
                    ROW_NUMBER() OVER (
                        PARTITION BY v."sourceId" 
                        ORDER BY 1 - (v.embedding <-> %s::vector) DESC
                    ) as rank
                FROM vectors v
                JOIN sources s ON s.id = v."sourceId"
                WHERE {' AND '.join(base_conditions)}
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
            LIMIT %s;
            """

    def search_embeddings(
            self,
            query_text: str,
            source_ids: List[str],
            top_k: int = 5,
            max_age_days: Optional[int] = None,
            content_types: Optional[List[str]] = None,
        ) -> List[SearchResult]:
            """Enhanced semantic search with better deduplication and relevance filtering"""
            try:
                not_allowed_chars = []
                symbols = open("./data/symbols.txt").read().split("\n")
                stopwords = open("./data/stopwords.txt").read().split("\n")
                not_allowed_chars.extend(symbols)
                not_allowed_chars.extend(stopwords)
                filtered_words = [word for word in query_text.split() if word.lower() not in not_allowed_chars]
                query_text = " ".join(filtered_words)
                _, [query_embedding] = self.create_embeddings(query_text, batch=False)[:2]
                
                search_query = self._build_search_query(
                    max_age_days=max_age_days,
                    content_types=content_types
                )
                
                # Add query embedding twice for both similarity calculations
                params = [
                    query_embedding,  # For main similarity calculation
                    query_embedding,  # For ranking
                    source_ids,
                    *([str(max_age_days)] if max_age_days is not None else []),
                    *([content_types] if content_types else []),
                    top_k
                ]
                
                results = get_vector_repo().execute_search(
                    query=search_query,
                    params=params
                )
                
                if not results:
                    return []
                
                search_results = []
                for row in results:
                    search_results.append(
                        SearchResult(
                            source_id=uuid.UUID(row[0]),
                            chunk_content=row[1],
                            metadata=row[2],
                            semantic_similarity=row[4],
                            created_at=row[3]
                        )
                    )
                
                return search_results[:top_k]

            except Exception as e:
                print(f"Error during search: {e}")
                raise ValueError(f"Search failed: {str(e)}")