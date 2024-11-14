import math
from typing import List, Dict, Any
from prisma.models import Source, Vector
from app.utils import generate_cuid, now
from app.services.vector import VectorService
from app.api.dependencies import get_vector_repo, get_sources_repo
from app.infrastructure.external.web.scraper import WebScraper


class WebSourcesController:
    def __init__(
        self,
        workspace_id: str,
        technique_id: str,
    ):
        self.workspace_id = workspace_id
        self.technique_id = technique_id
        self.source_repo = get_sources_repo()
        self.vector_repo = get_vector_repo()

        # Initialize services
        self.webscraper = WebScraper(scraper_path="./bin/scrapper")
        self.vector_service = VectorService()

        self.sources_ids: List[str] = []
        self.scrapped_urls: List[Dict[str, Any]] = []

    async def start_scrapping(self, urls: List[str], bot_id: None) -> None:
        """Start the scrapping process for given URLs"""
        self.scrapped_urls = self.webscraper.scrape(urls)
        self.sources_ids = await self.create_sources(
            scrapped_urls=self.scrapped_urls,
            workspace_id=self.workspace_id,
            technique_id=self.technique_id,
        )
        if bot_id:
            await self.source_repo.associate_sources_to_bot(bot_id, self.sources_ids)
        await self.create_embeddings()

    async def create_embeddings(self) -> None:
        """Generate and store embeddings for web sources"""
        for source_id, url in zip(self.sources_ids, self.scrapped_urls):
            chunks, embeddings = self.vector_service.create_embeddings(url["content"])
            await self.store_embeddings(
                source_id=source_id,
                workspace_id=self.workspace_id,
                chunks=chunks,
                embeddings=embeddings,
                metadata=url["metadata"],
            )

    async def create_sources(
        self, scrapped_urls: List[Dict[str, Any]], workspace_id: str, technique_id: str
    ) -> List[str]:
        """Create web sources and return their IDs"""
        sources_list: List[Source] = []
        for url_data in scrapped_urls:
            source = {
                "id": generate_cuid(),
                "workspaceId": workspace_id,
                "techniqueId": technique_id,
                "title": url_data["metadata"]["title"],
                "url": url_data["url"],
                "status": "DONE",
                "contentType": url_data["content_type"],
                "contentLength": url_data["content_length"],
                "contentHash": url_data["content_hash"],
                "syncTime": math.floor(int(url_data["sync_time"])),
                "createdAt": now(),
                "updatedAt": now(),
            }
            sources_list.append(source)
        created = await self.source_repo.create_sources(sources_list)
        if created == len(sources_list):
            return [source["id"] if "id" in source else None for source in sources_list]
        else:
            return []

    async def store_embeddings(
        self,
        source_id: str,
        workspace_id: str,
        chunks: List[str],
        embeddings: List[List[float]],
        metadata: Dict[str, Any],
    ) -> None:
        """Store all chunks with complete context"""
        vectors = []
        for chunk_content, embedding in zip(chunks, embeddings):
            vector = {
                "workspaceId": workspace_id,
                "embedding": embedding,
                "sourceId": source_id,
                "chunkContent": chunk_content,
                "metadata": metadata,
                "chunkLength": len(chunk_content),
            }
            vectors.append(vector)

        await self.vector_repo.create_vectors(vectors)
