import json
import faiss
import numpy as np
from collections import defaultdict
from typing import List, Dict, Union
from app.services.embeddings import EmbeddingService
from app.dependencies import get_vector_repo, get_database, get_config

class SearchService:
    index_cache = {}
    def __init__(self, workspace_id: str):
        self.db = get_database()
        self.config = get_config()
        self.workspace_id = workspace_id
        self.vector_repo = get_vector_repo()
        self.embedding_service = EmbeddingService()
    
        self.index = None
        self.embeddings = []

    def setup_faiss_index(self) -> None:
        """Set up FAISS index with embeddings from the database."""

        if self.workspace_id in self.index_cache:
            self.index, self.embeddings = self.index_cache[self.workspace_id]
            return
        
        embeddings_data = self.get_workspace_embeddings()
        
        embeddings_array = np.array([data['embedding'] for data in embeddings_data], dtype=np.float32)

        data_size = embeddings_array.shape[0]
        dimension = embeddings_array.shape[1]
        nlist = max(1, data_size // 10)
        quantizer = faiss.IndexFlatL2(dimension)
        self.index = faiss.IndexIVFFlat(quantizer, dimension, nlist, faiss.METRIC_L2)
        
        if embeddings_array.shape[0] >= nlist:
            self.index.train(embeddings_array)
            self.index.add(embeddings_array)
        else:
            raise ValueError(f"Not enough embeddings to train with nlist={nlist}. Available embeddings: {embeddings_array.shape[0]}")
        
        self.embeddings = embeddings_data
        self.index_cache[self.workspace_id] = (self.index, self.embeddings)

    def search_similar_items(self, query_text: str,  query_embedding: List[float], k: int = 5) -> List[Dict]:
        """Search for items similar to the query embedding."""
        query_embedding_array = np.array([query_embedding], dtype=np.float32)
        
        if self.index is None or query_embedding_array.shape[1] != self.index.d:
            raise ValueError("Embedding dimension mismatch or index not initialized.")
        
        distances, indices = self.index.search(query_embedding_array, k * 2)
        
        closest_matches = defaultdict(lambda: {"distance": float('inf')})
        keyword = query_text.lower()

        for idx, i in enumerate(indices[0]):
            source_id = self.embeddings[i]["source_id"]
            content: str = self.embeddings[i]["chunk_content"]
            distance = float(distances[0][idx])
            
            if keyword in content.lower() or distance < closest_matches[source_id]["distance"]:
                closest_matches[source_id] = {
                    "source_id": source_id,
                    "content": self.embeddings[i]["chunk_content"],
                    "metadata": self.embeddings[i]["metadata"],
                    "distance": distance
                }

        deduplicated_results = sorted(closest_matches.values(), key=lambda x: x["distance"])[:k]
        return deduplicated_results

    def get_workspace_embeddings(self) -> List[Dict[str, Union[str, List[float]]]]:
        """Fetch embeddings and metadata from the database."""
        
        search_query = """
        SELECT "sourceId", "chunkContent", metadata, "chunkLength", embedding
        FROM vectors
        WHERE "workspaceId" = %s
        """
        results = self.db.execute(search_query, (self.workspace_id,), fetch=True)
        
        return [
            {
                "source_id": row[0],
                "chunk_content": row[1],
                "metadata": row[2],
                "chunk_length": row[3],
                "embedding": json.loads(row[4])
            }
            for row in results
        ]
