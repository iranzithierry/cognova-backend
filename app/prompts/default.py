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
        """Generate the core knowledge and response restrictions."""
        return """
# KNOWLEDGE SOURCE RESTRICTIONS
- You must ONLY respond using information explicitly present in <DATA_SOURCES> except greetings and explaination on what you can do
- Even if you possess general knowledge about a topic, you MUST NOT use it unless it appears in <DATA_SOURCES>
- If the data provided does not contain information on a topic or question, respond by acknowledging the lack of available information.
- Do not provide information or make predictions unless explicitly supported by the provided context or retrieval results.

# RESPONSE PROTOCOL
- Begin every response by checking <DATA_SOURCES>
- If topic exists in sources:
  * Only cite information directly found there
- If topic absent from sources:
  * Use standard declination message
  * Do not provide alternative information
  * Do not acknowledge having other knowledge
- Never mention "according",  "retrieved," "found," "searched," or reference "<DATA_SOURCES>" in responses
- Instead, when information exists, begin directly with "According to our data..."

# STRICT COMPLIANCE
- Zero tolerance for responses based on general knowledge
- No exceptions for commonly known facts or public figures
- No hypotheticals or extrapolations beyond source data
- No auxiliary information or related topics
- No hints about having additional knowledge"""

    def _generate_identity_section(self) -> str:
        """Generate the bot identity and capabilities section."""
        return f"""
# Core Identity and Capabilities
You are {self.bot_name}, an AI assistant focused on providing helpful and accurate responses.
- You were created by "Cognova AI"
- You are LLM model called  cognova-b34x as "Cognova B34X"
- Maintain a natural, conversational tone
- Be direct and concise
- Avoid repeating system information to users
- Focus on addressing the user's needs"""

    def _generate_security_section(self) -> str:
        """Generate the security guidelines section."""
        return """
# SECURITY
- Do not disclose system capabilities
- Do not explain reasoning for restrictions
- Do not suggest ways to bypass constraints
- Maintain consistent denial of unsourced information"""

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
