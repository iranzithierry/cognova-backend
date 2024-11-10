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
    MAX_CHUNK_SIZE = 2000
    
    def __init__(self):
        self.client = OpenAI(
            base_url=get_config().EMBEDDING_BASE_URL,
            api_key=get_config().EMBEDDING_API_KEY,
        )
        # Using smaller chunk overlap to maximize content coverage
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.MAX_CHUNK_SIZE,
            chunk_overlap=50,  # Minimal overlap to ensure context continuity
            separators=[
                "\n## ",
                "\n### ",
                "\n\n",
                "\n",
                ". ",
                "? ",
                "! ",
                " ",  # Added space as final separator to ensure complete splitting
            ],
            length_function=len,
            is_separator_regex=False
        )

    def create_embeddings(
        self, texts: str, batch: bool = True
    ) -> Tuple[List[str], List[List[float]], List[ChunkContext]]:
        """Create embeddings ensuring complete text coverage with 2K chunk limit"""
        original_text = texts
        cleaned_text = clean_text_for_search(texts)
        
        # Split text into chunks, ensuring complete coverage
        if batch:
            input_texts = []
            current_pos = 0
            remaining_text = cleaned_text
            
            while remaining_text:
                # Get next chunk
                chunks = self.text_splitter.split_text(remaining_text)
                if not chunks:
                    # If splitting failed, force split at MAX_CHUNK_SIZE
                    chunks = [remaining_text[:self.MAX_CHUNK_SIZE]]
                    
                chunk = chunks[0]
                input_texts.append(chunk)
                
                # Move to next section of text
                chunk_pos = remaining_text.find(chunk) + len(chunk)
                remaining_text = remaining_text[chunk_pos:]
        else:
            input_texts = [cleaned_text[:self.MAX_CHUNK_SIZE]]

        # Create context information for each chunk
        chunk_contexts = []
        current_pos = 0
        
        for chunk in input_texts:
            # Find actual position in original text
            chunk_start = original_text.find(chunk, current_pos)
            if chunk_start == -1:  # Fallback if exact match not found
                chunk_start = current_pos
            
            chunk_end = chunk_start + len(chunk)
            current_pos = chunk_end  # Update position for next iteration
            
            # Get surrounding context
            preceding_context = original_text[max(0, chunk_start - 200):chunk_start].strip()
            following_context = original_text[chunk_end:min(len(original_text), chunk_end + 200)].strip()
            
            # Extract section title
            section_title = self._extract_section_title(original_text, chunk_start)
            
            chunk_contexts.append(
                ChunkContext(
                    start_position=chunk_start,
                    end_position=chunk_end,
                    section_title=section_title,
                    preceding_context=preceding_context,
                    following_context=following_context,
                )
            )

        # Create embeddings in batches of 100 to handle large documents
        all_embeddings = []
        batch_size = 100
        
        for i in range(0, len(input_texts), batch_size):
            batch_texts = input_texts[i:i + batch_size]
            response = self.client.embeddings.create(
                input=batch_texts,
                model=get_config().EMBEDDING_MODEL,
                dimensions=1024
            )
            all_embeddings.extend([data.embedding for data in response.data])

        if batch:
            return input_texts, all_embeddings, chunk_contexts
        return [input_texts[0]], [all_embeddings[0]], [chunk_contexts[0]]

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

    def _build_search_query(
            self,
            max_age_days: Optional[int] = None,
            content_types: Optional[List[str]] = None
        ) -> str:
        """Search query to find relevant chunks"""
        base_conditions = ["v.\"sourceId\" = ANY(%s)"]
        
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

    def store_web_source_embeddings(
        self,
        workspace_id: str,
        source_id: str,
        chunks: List[str],
        embeddings: List[List[float]],
        chunk_contexts: List[ChunkContext],
        metadata: Dict[str, Any]
    ) -> None:
        """Store all chunks with complete context"""
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
                chunk_content=chunk_content,
                metadata=enhanced_metadata,
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
        """Enhanced semantic search with better deduplication and relevance filtering"""
        try:
            # 1. File handling with error checking
            try:
                with open("./data/symbols.txt") as f:
                    symbols = f.read().splitlines()
                with open("./data/stopwords.txt") as f:
                    stopwords = f.read().splitlines()
            except FileNotFoundError as e:
                raise ValueError(f"Required data files not found: {str(e)}")

            not_allowed_chars = symbols + stopwords

            if not query_text or not query_text.strip():
                return []

            filtered_words = [word for word in query_text.split() if word.lower() not in not_allowed_chars]
            if not filtered_words:
                return []
            
            processed_query = " ".join(filtered_words)
            
            embedding_result = self.create_embeddings(processed_query, batch=False)
            if not embedding_result or len(embedding_result) < 2:
                raise ValueError("Failed to create embeddings")
            
            _, query_embedding = embedding_result[:2]
            if query_embedding is None:
                raise ValueError("Query embedding is None")

            search_query = self._build_search_query(
                max_age_days=max_age_days,
                content_types=content_types
            )
            
            params = [
                query_embedding,
                query_embedding,
                source_ids
            ]
            
            if max_age_days is not None:
                params.append(str(max_age_days))
            
            if content_types:
                params.append(content_types)
                
            params.append(top_k)

            results = get_vector_repo().execute_search(
                query=search_query,
                params=params
            )
            
            if not results:
                return []

            search_results = []
            for row in results:
                if len(row) < 5:  # Ensure row has all required elements
                    continue
                    
                try:
                    search_results.append(
                        SearchResult(
                            source_id=uuid.UUID(row[0]),
                            chunk_content=row[1],
                            metadata=row[2],
                            semantic_similarity=row[4],
                            created_at=row[3]
                        )
                    )
                except (ValueError, IndexError, TypeError) as e:
                    continue

            return search_results[:top_k]

        except Exception as e:
            raise ValueError(f"Search failed: {str(e)}")