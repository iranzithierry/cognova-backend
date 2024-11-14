from prisma import Prisma
from typing import List, Optional
from prisma.models import Source, Technique
from app.domain.errors import PrismaExecutionError
from app.domain.models import BotWithSourceId


class SourceRepository:
    def __init__(self, db: Prisma):
        self.db = db

    async def create_sources(self, sources: List[Source]):
        """Create multiple sources in the database"""
        try:
            created_sources = await self.db.source.create_many(data=sources)
            return created_sources
        except Exception as e:
            raise PrismaExecutionError(f"Failed to create sources: {str(e)}")

    async def get_source_ids_of_bot(self, bot_id: str) -> List[str]:
        """Get source ids associated with a specific bot"""
        try:
            bot_sources = await self.db.botsources.find_many(
                where={"botId": bot_id}
            )
            return [bot_source.sourceId for bot_source in bot_sources]
        except Exception as e:
            raise PrismaExecutionError(f"Failed to get source ids for bot: {str(e)}")

    async def associate_sources_to_bot(self, bot_id: str, source_ids: List[str]):
        """Associate sources to a bot"""
        try:
            await self.db.botsources.create_many(
                data=[
                    {
                        "botId": bot_id,
                        "sourceId": source_id,
                    }
                    for source_id in source_ids
                ]
            )
        except Exception as e:
            raise PrismaExecutionError(f"Failed to associate sources to bot: {str(e)}")

    async def get_technique(self, technique_name: str) -> Optional[Technique]:
        """Get technique by name"""
        try:
            technique = await self.db.technique.find_unique(
                where={"name": technique_name}
            )
            return technique
        except Exception as e:
            raise PrismaExecutionError(f"Failed to get technique: {str(e)}")
