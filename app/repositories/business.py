from typing import Dict, Any
from prisma import Prisma
from prisma.models import Business


class BusinessRepository:
    def __init__(self, db: Prisma):
        self.db = db

    async def get_business_data(self, business_id: str)-> (Business | None):
        """Fetch all necessary business data from database."""
        business = await self.db.business.find_unique(
            where={"id": business_id},
            include={"configurations": True, "locations": True, "operatingHours": True},
        )
        return business
