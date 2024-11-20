from functools import lru_cache
from app.core.database import db
from app.core.config import Config
from app.repositories.chat import ChatRepository
from app.repositories.vector import VectorRepository
from app.repositories.source import SourceRepository
from app.repositories.business import BusinessRepository

@lru_cache()
def get_config() -> Config:
    return Config()


@lru_cache()
def get_vector_repo() -> VectorRepository:
    return VectorRepository(db.prisma)

@lru_cache()
def get_sources_repo() -> SourceRepository:
    return SourceRepository(db.prisma)

@lru_cache()
def get_chat_repository() -> ChatRepository:
    return ChatRepository(db.prisma)

@lru_cache()
def get_business_repository() -> BusinessRepository:
    return BusinessRepository(db.prisma)