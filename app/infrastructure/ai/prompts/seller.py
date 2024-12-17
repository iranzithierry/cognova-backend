import json
from datetime import datetime, timezone
from typing import List, Dict, Optional, Literal
from prisma.models import (
    Bot,
    Chat,
    Business,
    BusinessConfig,
    BusinessLocation,
    BusinessOperatingHours,
)


ModeType = Literal["whatsapp", "web", None]


class SellerPromptGenerator:
    def __init__(
        self,
        business: Business,
        config: BusinessConfig,
        locations: List[BusinessLocation],
        operating_hours: List[BusinessOperatingHours],
        mode: ModeType = "whatsapp",
        extra_context: Optional[str] = None,
    ):
        self.business = business
        self.config = config
        self.locations = locations
        self.operating_hours = operating_hours
        self.mode = mode
        self.extra_context = extra_context

    def _get_current_time(self) -> str:
        """Generate formatted UTC timestamp."""
        now_utc = datetime.now(timezone.utc)
        return now_utc.strftime("%a %b %d %Y %H:%M:%S GMT+0000")

    def _format_locations_data(self) -> List[str]:
        """Format locations data from database."""
        return [
            f"{loc.name}: {loc.address}, {loc.city}, {loc.country} "
            f"({loc.phone if loc.phone else 'No phone'})"
            for loc in self.locations
        ]

    def _format_contact_data(self) -> List[Dict]:
        """Format contact data for WhatsApp API."""
        contacts = []
        for loc in self.locations:
            if loc.phone:
                contact = {
                    "name": {
                        "formatted_name": loc.name,
                        "first_name": loc.name
                    },
                    "org": {
                        "company": self.business.name,
                        "department": loc.name,
                        "title": "Store Location"
                    },
                    "phones": [
                        {
                            "phone": loc.phone,
                            "type": "WORK",
                            "wa_id": loc.phone.replace("+", "")
                        }
                    ]
                }
                contacts.append(contact)
        return contacts

    def _format_operating_hours(self) -> str:
        """Format operating hours from the database with proper alignment."""
        hours_by_day = {}

        for location in self.locations:
            seen_days = set()
            location_hours = []

            for hour in sorted(self.operating_hours, key=lambda x: x.dayOfWeek):
                hour: BusinessOperatingHours = hour
                if hour.locationId == location.id:
                    if hour.dayOfWeek not in seen_days:
                        seen_days.add(hour.dayOfWeek)
                        if hour.isClosed:
                            location_hours.append(f"{hour.dayOfWeek}: CLOSED")
                        else:
                            location_hours.append(
                                f"{hour.dayOfWeek}: {hour.openTime} - {hour.closeTime}"
                            )
            hours_by_day[location.name] = "  ".join(location_hours)

        if not hours_by_day:
            return "No operating hours available."

        max_location_length = max(len(location) for location in hours_by_day) if hours_by_day else 0

        prefix = "## " if self.mode != "whatsapp" else "*"
        suffix = "" if self.mode != "whatsapp" else "*"

        return "\n".join(
            f"{prefix}{location}{suffix}: {' ' * (max_location_length - len(location))}{hours}"
            for location, hours in hours_by_day.items()
        ) if hours_by_day else "No operating hours available."

    def _get_formatting_guide(self) -> str:
        """Return formatting guide based on mode."""
        if self.mode == "whatsapp":
            return """
# RESPONSE FORMATTING RULES
- Use *asterisks* for bold text
- Use _underscores_ for italic text
- Use ~tildes~ for strikethrough
- Use ``` for code blocks
- No headers or complex markdown
- Use only single asterisk whatever heading is
- Limited to WhatsApp's supported formatting
- Use numbered lists (1. 2. 3.) or simple bullet points (•) when needed
- Images must be sent separately (no inline images) in<images>[image_url,image_url]</images>
- When sharing contact information for purchase, wrap it in <contacts>[contact_data]</contacts> tags
- And add this section `tel:<phone>` (choose main store) to call directly but specify it like you're telling user to call through this number
"""
        else:
            return """"""

    def generate_prompt(self) -> str:
        locations_data = self._format_locations_data()
        operating_hours_str = self._format_operating_hours()
        formatting_guide = self._get_formatting_guide()
        contact_data = self._format_contact_data()
        return f"""
# CORE RULES
- You are a sales assistant for {self.business.name}, a {self.business.type} chatting {"Via whatsapp business mode" if self.mode == "whatsapp" else "In Website mode"}
- When a customer asks about ANY brand or category, IMMEDIATELY:
  1. Call search_products with the name/brand/category/key-term
  2. Show ALL results found
  3. NEVER ask for more specifics first
  4. To ensure a seamless real-time chat flow during conversations, if a tool responds with "none" or "results not found," you must always invoke the tool again to retrieve results or provide the most relevant information available.
- NEVER make multiple tool calls at once
- For multiple search terms (e.g. "Adidas Yeezy"), combine them into a single query: search_products with query="adidas yeezy"
- When users ask to see all products, use search_products with query="*LATEST*"
- NEVER tell users you can't show products - always attempt to search and display what's available
- If a search returns many results, show a selection of popular or recent items
- ALWAYS display prices and availability for each product shown


- Keep responses focused on sales and always mention prices when discussing products
- All prices are in {self.config.currency if self.config and hasattr(self.config, "currency") else "USD"}
- Format all responses according to the mode-specific rules below
- When user is ready to purchase and in web mode, provide contact information in markdown format and add Telephone in `tel:<tel>` link and link must have label `Call Now`
- When user is ready to purchase and in whatsapp mode, provide contact information wrapped in <contacts>contact_data</contacts> tags and after adding tags add section contained `tel:<phone>` (choose main store) to call directly for the format you will be using this format:
{json.dumps(contact_data, indent=2)}

{formatting_guide}
# COMMON ERRORS TO AVOID
- Don't refer customers to the website
- Don't exclude available product images {'(in web mode)' if self.mode != 'whatsapp' else ''}

# SERVICE CONFIGURATION
- Delivery: {'Available' if self.config.hasDelivery else 'Not available'}
{f'(Minimum order: {self.config.minDeliveryOrderAmount} {self.config.currency}, Fee: {self.config.deliveryFee} {self.config.currency})' if self.config.hasDelivery else ''}
- Returns: {'Accepted' if self.config.acceptsReturns else 'Not available'}
{f'(Within {self.config.returnPeriod})' if self.config.acceptsReturns else ''}
- Warranty: {'Available' if self.config.hasWarranty else 'Not available'}
{f'({self.config.warrantyPeriod})' if self.config.hasWarranty else ''}

# <BUSINESS_DATA>
DESCRIPTION:
{self.business.description}

LOCATIONS:
{chr(10).join(locations_data)}

BUSINESS HOURS:
{operating_hours_str}
# </BUSINESS_DATA>

# IMPORTANT REMINDERS
- NEVER reply about product availability without calling search_products first
- Provide direct contact information instead of website references

Current time: {self._get_current_time()}
{self.extra_context if self.extra_context else ""}
"""