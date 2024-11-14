import logging
from prisma import Prisma
from typing import AsyncGenerator
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self._prisma = Prisma()
        self._is_connected = False

    async def connect(self) -> None:
        try:
            if not self._is_connected:
                await self._prisma.connect()
                self._is_connected = True
                logger.info("Successfully connected to database")
        except Exception as e:
            logger.error(f"Failed to connect to database: {str(e)}")
            raise

    async def disconnect(self) -> None:
        try:
            if self._is_connected:
                await self._prisma.disconnect()
                self._is_connected = False
                logger.info("Successfully disconnected from database")
        except Exception as e:
            logger.error(f"Error disconnecting from database: {str(e)}")
            raise

    @property
    def prisma(self) -> Prisma:
        return self._prisma

    async def verify_connection(self) -> bool:
        """Verify database connection is still alive"""
        try:
            await self._prisma.query_raw("SELECT 1")
            return True
        except Exception:
            self._is_connected = False
            return False

    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[Prisma, None]:
        """Context manager for database transactions"""
        try:
            await self.connect()
            yield self._prisma
        finally:
            await self.disconnect()

db = Database()