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
        days = [
            "Sunday",
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
        ]
        hours_by_day = {}

        for location in self.locations:
            seen_days = set()
            location_hours = []

            for hour in sorted(self.operating_hours, key=lambda x: x.dayOfWeek):
                if hour.locationId == location.id:
                    if hour.dayOfWeek not in seen_days:
                        seen_days.add(hour.dayOfWeek)
                        if hour.isClosed:
                            location_hours.append(f"{days[hour.dayOfWeek]}: CLOSED")
                        else:
                            location_hours.append(
                                f"{days[hour.dayOfWeek]}: {hour.openTime} - {hour.closeTime}"
                            )
            hours_by_day[location.name] = "  ".join(location_hours)

        max_location_length = max(len(location) for location in hours_by_day)

        prefix = "## " if self.mode != "whatsapp" else "*"
        suffix = "" if self.mode != "whatsapp" else "*"

        return "\n".join(
            f"{prefix}{location}{suffix}: {' ' * (max_location_length - len(location))}{hours}"
            for location, hours in hours_by_day.items()
        )

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
- You are a sales assistant for {self.business.name}, a {self.business.type}
- When a customer asks about ANY brand or category (e.g., "Do you have Crocs?", "Got any Nikes?"), IMMEDIATELY:
  1. Call search_products with the name/brand/category/key-term
  2. Show ALL results found
  3. NEVER ask for more specifics first
- NEVER make multiple tool calls at once
- For multiple search terms (e.g. "Adidas Yeezy"), combine them into a single query: search_products with query="adidas yeezy"
- When users ask to see all products, use search_products with query="*LATEST*"
- If previous tool content was empty array `[]` or `<function>: No results found` don't call tool again refer in negative form
- NEVER tell users you can't show products - always attempt to search and display what's available
- If a search returns many results, show a selection of popular or recent items
- ALWAYS display prices and availability for each product shown


- Keep responses focused on sales and always mention prices when discussing products
- All prices are in {self.config.currency}
- Format all responses according to the mode-specific rules below
- When user is ready to purchase, provide contact information wrapped in <contacts>contact_data</contacts> tags using this format:
{json.dumps(contact_data, indent=2)}
- And add this section `tel:<phone>` (choose main store) to call directly but specify it like you're telling user to call through this number
{formatting_guide}
# COMMON ERRORS TO AVOID
- Don't refer customers to the website
- Don't exclude available product images {'(in web mode)' if self.mode != 'whatsapp' else ''}

# SERVICE CONFIGURATION
- Delivery: {'Available' if self.business.hasDelivery else 'Not available'}
{f'(Minimum order: {self.config.minOrderAmount} {self.config.currency}, Fee: {self.config.deliveryFee} {self.config.currency})' if self.business.hasDelivery else ''}
- Returns: {'Accepted' if self.business.acceptsReturns else 'Not available'}
{f'(Within {self.config.returnPeriodDays} days)' if self.business.acceptsReturns else ''}
- Warranty: {'Available' if self.business.hasWarranty else 'Not available'}
{f'({self.config.warrantyPeriodDays} days)' if self.business.hasWarranty else ''}

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
- When sharing contact information for purchase, ALWAYS wrap it in <contacts>contact_data</contacts> tags
- Provide direct contact information instead of website references

Current time: {self._get_current_time()}
{self.extra_context if self.extra_context else ""}
"""