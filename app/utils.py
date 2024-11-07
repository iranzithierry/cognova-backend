import re
from typing import List, Dict, Any
from app.prompting import PromptGenerator


def compress_text(text: str):
    return " ".join(text.split())


def clean_text_for_search(text: str):
    text = re.sub(
        r"(\w+)/(\w+)", r"\1/\2 (\1 \2)", text
    )  # Matches 'word1/word2' pattern
    text = re.sub(
        r"(\w+)-(\w+)", r"\1-\2 (\1 \2)", text
    )  # Matches 'word1-word2' pattern
    text = re.sub(
        r"(\w+)&(\w+)", r"\1-\2 (\1 \2)", text
    )  # Matches 'word1&word2' pattern
    return text


def generate_system_message(
    system_message: str | None,
    bot_description: str,
    bot_name: str,
    search_results: str,
) -> str:
    """
    Backwards-compatible wrapper for the new implementation.
    """
    generator = PromptGenerator(
        bot_name=bot_name,
        bot_description=bot_description,
        system_message=system_message,
    )
    return generator.generate_message(search_results)
