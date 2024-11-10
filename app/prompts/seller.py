from datetime import datetime, timezone
from typing import List, Dict, Optional

class SellerPromptGenerator:
    def __init__(
        self,
        business_name: str,
        business_type: str,
        products_data: Dict,
        business_config: Dict[str, bool] = None,
        operating_hours: Optional[str] = None,
        locations: Optional[List[str]] = None,
    ):
        self.business_name = business_name
        self.business_type = business_type
        self.products_data = products_data
        self.business_config = business_config or {
            "has_delivery": False,
            "has_pickup": False,
            "accepts_returns": False,
            "has_warranty": False
        }
        self.operating_hours = operating_hours
        self.locations = locations

    def _get_current_time(self) -> str:
        """Generate formatted UTC timestamp."""
        now_utc = datetime.now(timezone.utc)
        return now_utc.strftime("%a %b %d %Y %H:%M:%S GMT+0000")

    def _generate_core_rules(self) -> str:
        """Generate the core rules for the seller bot."""
        return f"""
# CORE RULES
- You are a sales assistant for {self.business_name}, a {self.business_type}
- ONLY discuss products and services listed in <BUSINESS_DATA>
- NEVER make assumptions about services not explicitly defined
- If asked about unavailable services, say: "I apologize, but we don't offer that service at this time."
- Keep responses short and focused on sales
- Always mention prices when discussing products
- Respond with "Let me check our data..." if information is unclear

# RESPONSE STRUCTURE
1. Greet customer politely
2. Answer questions directly using only available data
3. Mention relevant products or services
4. Include prices and availability
5. End with a clear call to action"""

    def _generate_service_rules(self) -> str:
        """Generate rules based on available services."""
        rules = []
        
        if self.business_config["has_delivery"]:
            rules.append("- Inform about delivery options and fees when relevant")
        else:
            rules.append("- If asked about delivery, explain we don't offer this service")
            
        if self.business_config["has_pickup"]:
            rules.append("- Provide pickup location and hours when discussing pickup")
        
        if self.business_config["accepts_returns"]:
            rules.append("- Mention return policy when discussing products")
            
        if self.business_config["has_warranty"]:
            rules.append("- Include warranty information for eligible products")
            
        if self.locations:
            rules.append("- Only mention our listed store locations")
            
        if self.operating_hours:
            rules.append("- Include business hours when discussing visit or pickup")
            
        return "\n# SERVICE RULES\n" + "\n".join(rules)

    def _format_business_data(self) -> str:
        """Format all business data for the prompt."""
        data_sections = ["\n# <BUSINESS_DATA>"]
        
        # Add products
        data_sections.append("\nPRODUCTS:")
        for product, details in self.products_data.items():
            data_sections.append(f"- {product}: {details}")
            
        # Add locations if available
        if self.locations:
            data_sections.append("\nLOCATIONS:")
            for location in self.locations:
                data_sections.append(f"- {location}")
                
        # Add hours if available
        if self.operating_hours:
            data_sections.append(f"\nBUSINESS HOURS:\n{self.operating_hours}")
            
        data_sections.append("# </BUSINESS_DATA>")
        return "\n".join(data_sections)

    def generate_prompt(self) -> str:
        """Generate the complete system prompt."""
        sections = [
            self._generate_core_rules(),
            self._generate_service_rules(),
            f"\n# TIME AWARENESS\nCurrent time: {self._get_current_time()}",
            self._format_business_data()
        ]
        return "\n".join(sections)