import re
from typing import List, Dict, Any
from app.prompts.default import DefaultPromptGenerator
from app.prompts.seller import SellerPromptGenerator


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
    prompt_type: str = None,
) -> str:
    """
    Backwards-compatible wrapper for the new implementation.
    """
    if prompt_type == "default" or prompt_type is None:
        generator = DefaultPromptGenerator(
            bot_name=bot_name,
            bot_description=bot_description,
            system_message=system_message,
        )
        return generator.generate_message(search_results)
    # elif prompt_type == "seller":
    #     generator = SellerPromptGenerator(
    #         bot_name=bot_name,
    #         bot_description=bot_description,
    #         system_message=system_message,
    #     )
    # return generator.generate_message(search_results)
