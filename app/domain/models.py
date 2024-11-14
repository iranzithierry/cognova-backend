from datetime import datetime
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

@dataclass
class BotWithSourceId:
    sourceId: str

@dataclass
class ChatResponse:
    message: str
    source_urls: List[str]
    error: Optional[str] = None


@dataclass
class ScrappedURL:
    url: str
    content: str
    content_type: str
    content_length: int
    content_hash: str
    sync_time: datetime
    metadata: Dict[str, Any]


@dataclass
class Metadata:
    title: Optional[str] = None
    source: Optional[str] = None
    language: Optional[str] = None
    description: Optional[str] = None


@dataclass
class SearchResult:
    source_id: str
    chunk_content: str
    metadata: Metadata
    created_at: datetime
    semantic_similarity: float


@dataclass
class Technique:
    id: str
    name: str
    display_name: str
    plan_id: str
    createdAt: datetime
    updatedAt: datetime
