from datetime import datetime
from typing import List, Dict, Any, Optional

class BusinessTools:
    def __init__(self, prisma_client):
        self.prisma = prisma_client

    async def get_business_info(self, business_id: str) -> Dict[str, Any]:
        """Get basic business information."""
        business = await self.prisma.business.find_unique(
            where={"id": business_id},
            include={
                "configurations": True,
            }
        )
        return {
            "name": business.name,
            "type": business.type,
            "description": business.description,
            "has_delivery": business.hasDelivery,
            "has_pickup": business.hasPickup,
            "accepts_returns": business.acceptsReturns,
            "has_warranty": business.hasWarranty,
            "currency": business.configurations.currency,
        }

    async def search_products(
        self, 
        query: str, 
        category: Optional[str] = None, 
        max_price: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """Search for products with filters."""
        where = {
            "OR": [
                {"name": {"contains": query, "mode": "insensitive"}},
                {"description": {"contains": query, "mode": "insensitive"}},
            ],
            "isActive": True,
        }
        
        if category:
            where["category"] = {"name": {"equals": category, "mode": "insensitive"}}
        if max_price:
            where["price"] = {"lte": max_price}

        products = await self.prisma.product.find_many(
            where=where,
            include={"category": True}
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
        self, 
        product_id: str, 
        location_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Check product stock availability."""
        product = await self.prisma.product.find_unique(
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
        
        locations = await self.prisma.location.find_many(
            where=where,
            include={"hours": True}
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
                ]
            }
            for loc in locations
        ]

    async def check_operating_hours(
        self, 
        location_id: str, 
        datetime_str: Optional[str] = None
    ) -> Dict[str, Any]:
        """Check if location is open at given time."""
        check_time = (
            datetime.fromisoformat(datetime_str)
            if datetime_str
            else datetime.now()
        )
        
        location = await self.prisma.location.find_unique(
            where={"id": location_id},
            include={"hours": True}
        )
        
        day_hours = next(
            (h for h in location.hours if h.dayOfWeek == check_time.weekday()),
            None
        )
        
        if not day_hours or day_hours.isClosed:
            return {
                "is_open": False,
                "message": "Location is closed today",
            }
        
        current_time = check_time.strftime("%H:%M")
        is_open = day_hours.openTime <= current_time <= day_hours.closeTime
        
        return {
            "is_open": is_open,
            "opens_at": day_hours.openTime,
            "closes_at": day_hours.closeTime,
            "checked_time": current_time,
        }

    async def get_delivery_info(
        self, 
        postal_code: str, 
        total_amount: float
    ) -> Dict[str, Any]:
        """Calculate delivery availability and fees."""
        config = await self.prisma.businessConfig.find_first()
        
        if total_amount < config.minOrderAmount:
            return {
                "available": False,
                "message": f"Minimum order amount for delivery is {config.minOrderAmount}",
                "min_amount": config.minOrderAmount,
            }
        
        return {
            "available": True,
            "delivery_fee": config.deliveryFee,
            "estimated_days": "2-3",
            "total_with_delivery": total_amount + config.deliveryFee,
        }

    async def get_categories(self) -> List[Dict[str, Any]]:
        """Get all product categories."""
        categories = await self.prisma.category.find_many(
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
        self, 
        policy_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get business policies."""
        config = await self.prisma.businessConfig.find_first()
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
            }
        }
        
        return policies[policy_type] if policy_type else policies