from openai import OpenAI
from typing import List, Tuple
from app.domain.models import SearchResult
from app.utils import clean_text_for_search
from app.api.dependencies import get_vector_repo, get_config
from langchain.text_splitter import RecursiveCharacterTextSplitter



class VectorService:
    MAX_CHUNK_SIZE = 2000

    def __init__(self):
        self.client = OpenAI(
            base_url=get_config().EMBEDDING_BASE_URL,
            api_key=get_config().EMBEDDING_API_KEY,
            default_headers={
                "Accept-Encoding": "gzip",
                "Content-Type": "application/json",
            }
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.MAX_CHUNK_SIZE,
            chunk_overlap=50,
            separators=[
                "\n## ",
                "\n### ",
                "\n\n",
                "\n",
                ". ",
                "? ",
                "! ",
                " ",
            ],
            length_function=len,
            is_separator_regex=False,
        )

    def create_embeddings(
        self, texts: str, batch: bool = True
    ) -> Tuple[List[str], List[List[float]]]:
        """Create embeddings ensuring complete text coverage with 2K chunk limit"""
        if not texts or not isinstance(texts, str):
            raise ValueError("Input texts must be a non-empty string")

        cleaned_text = clean_text_for_search(texts)
        if not cleaned_text:
            raise ValueError("Cleaned text is empty")

        # Split text into chunks, ensuring complete coverage
        input_texts = []
        
        if batch:
            remaining_text = cleaned_text
            
            while remaining_text:
                chunks = self.text_splitter.split_text(remaining_text)
                if not chunks:
                    # If splitting failed, force split at MAX_CHUNK_SIZE
                    chunks = [remaining_text[:self.MAX_CHUNK_SIZE]]
                    
                chunk = chunks[0]
                if not chunk:  # Ensure we don't add empty chunks
                    break
                    
                input_texts.append(chunk)
                chunk_pos = remaining_text.find(chunk) + len(chunk)
                remaining_text = remaining_text[chunk_pos:]
        else:
            chunk = cleaned_text[:self.MAX_CHUNK_SIZE]
            if chunk:  # Only append if we have content
                input_texts.append(chunk)

        if not input_texts:
            raise ValueError("No valid text chunks were created")

        batch_size = 100
        input_texts_embeddings = []

        try:
            for i in range(0, len(input_texts), batch_size):
                batch_texts = input_texts[i:i + batch_size]
                response = self.client.embeddings.create(
                    input=batch_texts,
                    model=get_config().EMBEDDING_MODEL,
                    dimensions=1024
                )
                
                if not response or not response.data:
                    raise ValueError("Empty response from embeddings API")
                    
                batch_embeddings = [data.embedding for data in response.data]
                if not batch_embeddings:
                    raise ValueError("No embeddings generated for batch")
                    
                input_texts_embeddings.extend(batch_embeddings)

            if not input_texts_embeddings:
                raise ValueError("No embeddings were generated")

            if batch:
                return input_texts, input_texts_embeddings
            
            # Extra validation for non-batch mode
            if not input_texts[0] or not input_texts_embeddings[0]:
                raise ValueError("Empty result in single-chunk mode")
                
            return [input_texts[0]], [input_texts_embeddings[0]]

        except Exception as e:
            raise RuntimeError(f"Failed to create embeddings: {str(e)}") from e


    async def search_embeddings(
        self,
        query_text: str,
        source_ids: List[str],
        top_k: int = 5,
    ) -> List[SearchResult]:
        """Enhanced semantic search with better deduplication and relevance filtering"""
        try:
            try:
                with open("./data/symbols.txt") as f:
                    symbols = f.read().splitlines()
                    f.close()
                with open("./data/stopwords.txt") as f:
                    stopwords = f.read().splitlines()
                    f.close()
            except FileNotFoundError as e:
                raise ValueError(f"Required data files not found: {str(e)}")

            not_allowed_chars = symbols + stopwords

            filtered_words = [
                word
                for word in query_text.split()
                if word.lower() not in not_allowed_chars
            ]

            processed_query = " ".join(filtered_words)
            if len(processed_query) < 2:
                processed_query = query_text
            try:
                _, query_embedding = self.create_embeddings(processed_query, batch=False)
                if not query_embedding or not query_embedding[0]:
                    raise ValueError("Failed to generate query embedding")
            except Exception as e:
                raise RuntimeError(f"Search failed: Unable to create query embedding: {str(e)}") from e

            query_embedding = query_embedding[0]
            if query_embedding is None:
                raise ValueError("Query embedding is None")

            results = await get_vector_repo().execute_semantic_search(
                embedding=query_embedding,
                source_ids=source_ids,
                limit=top_k,
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
                            source_id=row["sourceId"],
                            chunk_content=row["full_content"],
                            metadata=row["metadata"],
                            created_at=row["createdAt"],
                            semantic_similarity=row["similarity"],
                        )
                    )
                except (ValueError, IndexError, TypeError) as e:
                    continue

            return search_results[:top_k]

        except Exception as e:
            raise ValueError(f"Search failed: {str(e)}")
