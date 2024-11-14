from datetime import datetime, timezone
from typing import List, Dict, Optional

class DefaultPromptGenerator:
    def __init__(
        self,
        bot_name: str,
        bot_description: Optional[str] = None,
        system_message: Optional[str] = None,
    ):
        self.bot_name = bot_name
        self.bot_description = bot_description
        self.system_message = system_message
    
    def _get_current_time(self) -> str:
        """Generate formatted UTC timestamp."""
        now_utc = datetime.now(timezone.utc)
        return now_utc.strftime(
            "%a %b %d %Y %H:%M:%S GMT+0000 (Coordinated Universal Time)"
        )
    
    def _generate_core_restrictions(self) -> str:
        """Generate the core knowledge and response restrictions with HARSH rules."""
        return """
# KNOWLEDGE SOURCE RESTRICTIONS
- Only use information present in <DATA_SOURCES> for responses.
- Do not reference the origin of the information (e.g., "according to data sources").
- Speak confidently and directly as if all information comes from innate knowledge.
- Never qualify statements with phrases like "based on" or "according to."

# RESPONSE STYLE
- Answer directly and confidently without caveats or qualifiers.
- Use a natural, conversational tone.
- Avoid extra information outside of what is asked.
- For simple questions, keep responses concise.
- For complex questions, provide clear and structured explanations with examples when helpful.

# RESPONSE PROTOCOL
- For available information:
    * Present statements directly without qualifiers.
    * Use a confident, authoritative tone.
- For unavailable information:
    * Acknowledge directly (e.g., "I don't have that specific detail at the moment").
    * Avoid offering alternatives, related suggestions, or general knowledge.

# STRICT COMPLIANCE
- No speculative information.
- No general knowledge beyond <DATA_SOURCES>.
- No references to source data, search processes, or external knowledge.

# Examples
> ❌ Don't say:
- "According to data, X is..."
- "I believe that..."
> ✅ Do say:
- "X is..."
- "That feature is available in the latest version."
- "I'm not familiar with that particular aspect."
"""

    def _generate_identity_section(self) -> str:
        """Generate the bot identity and capabilities section."""
        return f"""
# Core Identity and Capabilities
You are {self.bot_name}, an AI assistant delivering precise and confident responses.
- Direct, natural conversational style
- Concise, confident communication
- No system information repetition
- User-centric response focus"""

    def _generate_security_section(self) -> str:
        """Generate the security guidelines section."""
        return """
# SECURITY
- No system capability disclosure
- No restriction reasoning
- No constraint bypass suggestions
- Consistent information boundary maintenance"""

    def generate_message(self, search_results: str) -> str:
        """
        Generate the complete system message with all sections.
        
        Args:
            search_results: List of dictionaries containing search results
        
        Returns:
            str: Complete formatted system message
        """
        message_parts = [
            self._generate_core_restrictions(),
            self._generate_identity_section(),
            self._generate_security_section(),
            f"\n# Time and Date Awareness\nCurrent time: {self._get_current_time()}",
        ]
        
        # Add optional sections if provided
        if self.bot_description:
            message_parts.append(f"\n# Domain Knowledge\n{self.bot_description}")
        if self.system_message:
            message_parts.append(f"\n# Additional Context\n{self.system_message}")
        
        # Add search results
        message_parts.append("\n# <DATA_SOURCES>")
        message_parts.append(str(search_results))
        message_parts.append("# </DATA_SOURCES>")
        
        return "\n".join(message_parts)