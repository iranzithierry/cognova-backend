from app.core.database import db
from app.utils import split_camel_case, is_positive_integer
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
            formatted_query = " | ".join(f"{word}:*" for word in query.lower().split())
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
        
        order = [{"name": "asc"}]
        if query != "*LATEST*":
            order = [
                {
                    "_relevance": {
                        "fields": ["name"],
                        "search": formatted_query,
                        "sort": "desc"
                    }
                }
            ]
        
        products = await self.prisma.businessproduct.find_many(
            where=where,
            include={"category": True},
            take=15,
            order=order
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

        in_stock = "No"
        stock_value = product.stock
        if is_positive_integer(stock_value):
            in_stock = int(stock_value) > 0 
        elif stock_value == "IN_STOCK":
            in_stock = "Yes"
        else:
            in_stock = "No"
        return {
            "product_name": in_stock,
            "in_stock": stock_value,
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

        if total_amount < config.minDeliveryOrderAmount:
            return {
                "available": False,
                "message": f"Minimum order amount for delivery is {config.minDeliveryOrderAmount}",
                "min_amount": config.minDeliveryOrderAmount,
            }

        return {
            "available": True,
            "delivery_fee": config.deliveryFee,
            "estimated_delivery_arrival": config.estimatedDeliveryArrival,
            "total_with_delivery": total_amount + config.deliveryFee,
        }

    async def get_categories(self) -> List[Dict[str, Any]]:
        """Get all product categories."""
        categories = await self.prisma.productcategory.find_many(
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
                "available": config.acceptsReturns,
                "period_days": config.returnPeriod,
                "conditions": "Item must be unused and in original packaging",
            },
            "warranty": {
                "available": config.hasWarranty,
                "period_days": config.warrantyPeriod,
                "conditions": "Covers manufacturing defects",
            },
            "delivery": {
                "available": config.hasDelivery,
                "min_amount": config.minDeliveryOrderAmount,
                "fee": config.deliveryFee,
            },
        }

        return policies[policy_type] if policy_type else policies
