from app.config import Config
from typing import List, Dict, Any
from app.services.sources import SourcesService
from app.techniques.webscrapper import WebScraper
from app.services.embeddings import EmbeddingService
from app.repositories.sources import SourceRepository
from app.repositories.vectors import VectorRepository

class WebSourcesController:
    def __init__(
        self,
        workspace_id: str,
        technique_id: str,
        config: Config,
        source_repo: SourceRepository,
        vector_repo: VectorRepository
    ):
        self.workspace_id = workspace_id
        self.technique_id = technique_id
        self.config = config
        self.source_repo = source_repo
        self.vector_repo = vector_repo
        self.sources_ids: List[str] = []
        self.scrapped_urls: List[Dict[str, Any]] = []
        
        # Initialize services
        self.webscraper = WebScraper(scrapper_path="./bin/scrapper")
        self.sources_service = SourcesService()
        self.embedding_service = EmbeddingService()

    def start_scrapping(self, urls: List[str]) -> None:
        """Start the scrapping process for given URLs"""
        self.scrapped_urls = self.webscraper.scrape(urls)
        self.create_web_sources()
        self.generate_web_sources_embeddings()

    def create_web_sources(self) -> None:
        """Create web sources from scrapped URLs"""
        self.sources_ids = self.sources_service.store_web_sources(
            scrapped_urls=self.scrapped_urls,
            workspace_id=self.workspace_id,
            technique_id=self.technique_id,
        )

    def generate_web_sources_embeddings(self) -> None:
        """Generate and store embeddings for web sources"""
        for source_id, url in zip(self.sources_ids, self.scrapped_urls):
            chunks, embeddings, contexts = self.embedding_service.create_embeddings(url["content"])
            self.embedding_service.store_web_source_embeddings(
                workspace_id=self.workspace_id,
                source_id=source_id,
                chunks=chunks,
                embeddings=embeddings,
                chunk_contexts=contexts,
                metadata=url["metadata"]
            )
    # async def sync(self, source_id: str):
    #     source = self.source_repo.get_source(source_id)
    #     if source.type == "website":
    #         scraper = WebScraper(scrapper_path="./bin/scrapper")
    #         new_content = scraper.scrape(source.url)
    #         if new_content != source.content:
    #             self.source_repo.update_content(source_id, new_content)
    #             await self.embedding_service.update_embeddings(source_id, new_content)