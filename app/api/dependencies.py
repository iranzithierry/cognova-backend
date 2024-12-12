
import logging
from functools import lru_cache
from app.core.database import db
from app.core.config import Config
from app.repositories.chat import ChatRepository
from app.repositories.business import BusinessRepository

@lru_cache()
def get_config() -> Config:
    return Config()

@lru_cache()
def logger():
    return logging.getLogger(__name__)

@lru_cache()
def get_chat_repository() -> ChatRepository:
    return ChatRepository(db.prisma)

@lru_cache()
def get_business_repository() -> BusinessRepository:
    return BusinessRepository(db.prisma)