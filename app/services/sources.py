import uuid
from datetime import datetime
from app.models import Source
from typing import List, Dict, Any
from app.dependencies import get_config, get_sources_repo

class SourcesService:
    def __init__(self):
        self.config = get_config()
        self.source_repo = get_sources_repo()

    def store_web_sources(
        self,
        scrapped_urls: List[Dict[str, Any]],
        workspace_id: str,
        technique_id: str
    ) -> List[str]:
        """Store web sources and return their IDs"""
        sources = []
        for url_data in scrapped_urls:
            source = Source(
                id=uuid.uuid4(),
                workspace_id=uuid.UUID(workspace_id),
                technique_id=uuid.UUID(technique_id),
                title=url_data["metadata"]["title"],
                url=url_data["url"],
                status="DONE",
                content_type=url_data["content_type"],
                content_length=url_data["content_length"],
                content_hash=url_data["content_hash"],
                sync_time=url_data["sync_time"],
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            sources.append(source)

        source_ids = self.source_repo.create_sources(sources)
        return [str(source_id) for source_id in source_ids]