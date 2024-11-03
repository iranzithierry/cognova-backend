from app.db import Database
from app.config import Config
from functools import lru_cache
from app.repositories.chats import ChatRepository
from app.repositories.vectors import VectorRepository
from app.repositories.sources import SourceRepository

@lru_cache()
def get_config() -> Config:
    return Config("cognova")

@lru_cache()
def get_database() -> Database:
    return Database(get_config())

@lru_cache()
def get_vector_repo() -> VectorRepository:
    return VectorRepository(get_database())

@lru_cache()
def get_sources_repo() -> SourceRepository:
    return SourceRepository(get_database())

@lru_cache()
def get_chat_repository() -> ChatRepository:
    return ChatRepository(get_database())