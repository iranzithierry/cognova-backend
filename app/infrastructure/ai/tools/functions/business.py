from app.core.database import db
from app.utils import split_camel_case
from typing import List, Dict, Any, Optional


class BusinessFunctions:
    def __init__(self, business_id: str):
        self.prisma = db.prisma
        self.business_id = business_id

    async def search_products(
        self,
        query: str,
    ) -> List[Dict[str, Any]]:
        """Search products with filters (name, description, category, brand)."""
        where = {}
        if query == "*LATEST*":
            where = {
                "businessId": self.business_id,
                "isActive": True,
            }
        else:
            query = split_camel_case(query).lower()
            formatted_query = " & ".join(word + ":*" for word in query.split())
            where = {
                "OR": [
                    {"name": {"search": formatted_query}},
                    {"description": {"search": formatted_query}},
                    {
                        "category": {
                            "name": {
                                "search": formatted_query,
                            }
                        }
                    },
                ],

                "businessId": self.business_id,
                "isActive": True,
            }

        products = await self.prisma.businessproduct.find_many(
            where=where, include={"category": True}, take=15
        )

        return [
            {
                "id": product.id,
                "name": product.name,
                "description": product.description,
                "price": product.price,
                "stock": product.stock,
                "category": product.category.name if product.category else None,
                "images": product.images,
            }
            for product in products
        ]

    async def check_product_availability(
        self, product_id: str, location_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Check product stock availability."""
        product = await self.prisma.businessproduct.find_unique(
            where={"id": product_id},
        )

        return {
            "product_name": product.name,
            "in_stock": product.stock > 0,
            "stock_count": product.stock,
            "location": location_id if location_id else "all",
        }

    async def get_locations(self, city: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get business locations with optional city filter."""
        where = {"city": city} if city else {}

        locations = await self.prisma.businesslocation.find_many(
            where=where, include={"hours": True}
        )

        return [
            {
                "id": loc.id,
                "name": loc.name,
                "address": loc.address,
                "city": loc.city,
                "phone": loc.phone,
                "email": loc.email,
                "is_main": loc.isMain,
                "operating_hours": [
                    {
                        "day": hour.dayOfWeek,
                        "open_time": hour.openTime,
                        "close_time": hour.closeTime,
                        "is_closed": hour.isClosed,
                    }
                    for hour in loc.hours
                ],
            }
            for loc in locations
        ]

    async def get_delivery_info(self, total_amount: float) -> Dict[str, Any]:
        """Calculate delivery availability and fees."""
        config = await self.prisma.businessconfig.find_first()

        if total_amount < config.minOrderAmount:
            return {
                "available": False,
                "message": f"Minimum order amount for delivery is {config.minOrderAmount}",
                "min_amount": config.minOrderAmount,
            }

        return {
            "available": True,
            "delivery_fee": config.deliveryFee,
            "estimated_delivery_arrival": config.estimatedDeliveryArrival,
            "total_with_delivery": total_amount + config.deliveryFee,
        }

    async def get_categories(self) -> List[Dict[str, Any]]:
        """Get all product categories."""
        categories = await self.prisma.businessproductscategory.find_many(
            include={"products": {"select": {"id": True}}}
        )

        return [
            {
                "id": cat.id,
                "name": cat.name,
                "description": cat.description,
                "product_count": len(cat.products),
            }
            for cat in categories
        ]

    async def get_business_policies(
        self, policy_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get business policies."""
        config = await self.prisma.businessconfig.find_first()
        business = await self.prisma.business.find_first()

        policies = {
            "returns": {
                "available": business.acceptsReturns,
                "period_days": config.returnPeriodDays,
                "conditions": "Item must be unused and in original packaging",
            },
            "warranty": {
                "available": business.hasWarranty,
                "period_days": config.warrantyPeriodDays,
                "conditions": "Covers manufacturing defects",
            },
            "delivery": {
                "available": business.hasDelivery,
                "min_amount": config.minOrderAmount,
                "fee": config.deliveryFee,
            },
        }

        return policies[policy_type] if policy_type else policies
