from datetime import datetime
from typing import List, Dict, Any, Optional

tools = [
    {
        "name": "get_business_info",
        "description": "Get basic information about the business",
        "parameters": [
            {
                "business_id": {
                    "type": "string",
                    "description": "The ID of the business to retrieve information for",
                    "required": True,
                }
            }
        ],
    },
    {
        "name": "search_products",
        "description": "Search for products in the business catalog",
        "parameters": [
            {
                "query": {
                    "type": "string",
                    "description": "Search term for products (name, category, or description)",
                    "required": True,
                }
            },
            {
                "category": {
                    "type": "string",
                    "description": "Filter by category name",
                    "required": False,
                }
            },
            {
                "max_price": {
                    "type": "number",
                    "description": "Maximum price filter",
                    "required": False,
                }
            }
        ],
    },
    {
        "name": "check_product_availability",
        "description": "Check if a specific product is in stock",
        "parameters": [
            {
                "product_id": {
                    "type": "string",
                    "description": "The ID of the product to check",
                    "required": True,
                }
            },
            {
                "location_id": {
                    "type": "string",
                    "description": "Specific location to check stock (optional)",
                    "required": False,
                }
            }
        ],
    },
    {
        "name": "get_locations",
        "description": "Get list of business locations and their details",
        "parameters": [
            {
                "city": {
                    "type": "string",
                    "description": "Filter locations by city",
                    "required": False,
                }
            }
        ],
    },
    {
        "name": "check_operating_hours",
        "description": "Check if a location is open at a specific time",
        "parameters": [
            {
                "location_id": {
                    "type": "string",
                    "description": "The ID of the location to check",
                    "required": True,
                }
            },
            {
                "datetime": {
                    "type": "string",
                    "description": "ISO datetime string to check (defaults to current time if not provided)",
                    "required": False,
                }
            }
        ],
    },
    {
        "name": "get_delivery_info",
        "description": "Get delivery availability and fees for a location",
        "parameters": [
            {
                "postal_code": {
                    "type": "string",
                    "description": "Postal code to check delivery for",
                    "required": True,
                }
            },
            {
                "total_amount": {
                    "type": "number",
                    "description": "Order total to calculate delivery fees",
                    "required": True,
                }
            }
        ],
    },
    {
        "name": "get_categories",
        "description": "Get list of product categories",
        "parameters": [],
    },
    {
        "name": "get_business_policies",
        "description": "Get business policies like returns, warranty, etc.",
        "parameters": [
            {
                "policy_type": {
                    "type": "string",
                    "description": "Specific policy to retrieve (returns, warranty, delivery)",
                    "required": False,
                }
            }
        ],
    }
]