from uuid import UUID
from enum import Enum
from datetime import datetime
from dataclasses import dataclass
from typing import List, Optional, Dict, Any


class FeedbackType(Enum):
    UPVOTE = "UPVOTED"
    DOWNVOTE = "DOWNVOTED"
    NONE = "NONE"

@dataclass
class Bot:
    id: UUID
    workspace_id: UUID
    name: str
    description: Optional[str]
    language: Optional[str]
    system_message: Optional[str]
    placeholder_message: Optional[str]
    welcome_message: Optional[str]
    starter_questions: List[str]
    model_id: Optional[str]
    model_name: Optional[str] # For chatting
    businessId: Optional[str]
    created_at: datetime
    updated_at: datetime

@dataclass
class Chat:
    id: UUID
    conversation_id: UUID
    role: str
    content: str
    tokens: int
    source_urls: List[str]
    created_at: datetime
    updated_at: datetime
    feedback: FeedbackType

@dataclass
class Conversation:
    id: UUID
    bot_id: UUID
    session_id: str
    browser: Optional[str]
    os: Optional[str]
    device: Optional[str]
    country_code: Optional[str]
    generated_category: Optional[str]
    created_at: datetime
    updated_at: datetime

@dataclass
class ChatResponse:
    message: str
    source_urls: List[str]
    error: Optional[str] = None

# 

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
class Source:
    id: UUID
    workspace_id: UUID
    technique_id: UUID
    title: str
    url: str
    status: str
    content_type: str
    content_length: int
    content_hash: str
    sync_time: datetime
    created_at: datetime
    updated_at: datetime

@dataclass
class Metadata:
    title: Optional[str] = None
    source: Optional[str] = None
    language: Optional[str] = None
    description: Optional[str] = None

@dataclass
class Vector:
    id: UUID
    workspace_id: UUID
    source_id: UUID
    embedding: List[float]
    chunk_content: str
    metadata: Metadata
    chunk_length: int
    created_at: datetime
    updated_at: datetime

@dataclass
class SearchResult:
    source_id: UUID
    chunk_content: str
    metadata: Metadata
    semantic_similarity: float
    created_at: datetime
    
@dataclass
class Technique:
    id: UUID
    name: str
    display_name: str
    plan_id: str
    createdAt: datetime
    updatedAt: datetime