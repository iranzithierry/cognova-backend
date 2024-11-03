import psycopg2
from psycopg2.extras import execute_values
import numpy as np
from openai import OpenAI
import click
from typing import List, Tuple, Union
import asyncio
from concurrent.futures import ThreadPoolExecutor


class SemanticSearchComparison:
    def __init__(self, db_connection_string: str, llama_base_url: str):
        """
        Initialize the semantic search comparison tool.

        Args:
            db_connection_string: PostgreSQL connection string
            cloudflare_worker_url: URL of the Cloudflare Worker
            llama_base_url: Base URL for local Llama server
        """
        self.db_conn = psycopg2.connect(db_connection_string)
        self.llama_client = OpenAI(base_url=llama_base_url, api_key="not-needed")
        self.executor = ThreadPoolExecutor(max_workers=3)

    async def create_embedding(self, texts: Union[str, List[str]]) -> List[List[float]]:
        """
        Get embeddings from local Llama model.
        Supports both single text and batch processing.
        """
        try:
            response = self.llama_client.embeddings.create(
                model="text-embedding-3-large",
                input=texts,
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            raise Exception(f"Error getting Llama embeddings: {str(e)}")

    def search_similar(
        self, query_embedding: List[float], limit: int = 5
    ) -> List[Tuple[str, float]]:
        """Search for similar content using cosine similarity."""
        with self.db_conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT "chunkContent", 1 - (embedding <-> %s::vector) as similarity
                FROM vectors
                ORDER BY similarity DESC
                LIMIT %s
            """,
                (query_embedding, limit),
            )
            return cur.fetchall()


async def main():
    # Configuration
    db_config = "postgresql://root:1234@localhost:5432/cognova"
    llama_url = "http://localhost:8080/v1"

    # Initialize comparison tool
    searcher = SemanticSearchComparison(db_config, llama_url)
    prompt_input = input("Prompt: ")
    prompt_embedding = await searcher.create_embedding(prompt_input)
    results = searcher.search_similar(prompt_embedding[0], 5)
    for item in results:
        print(click.style(item[0]+"\n", "green", bold=True))
        print(click.style(item[1], "red", bold=True))
        print("\n\n")


if __name__ == "__main__":
    asyncio.run(main())
