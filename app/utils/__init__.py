import re
import datetime
from cuid2 import Cuid
from fastapi import Request

def compress_text(text: str):
    return " ".join(text.split())

CUID_GENERATOR: Cuid = Cuid(length=25)
def generate_cuid():
    return CUID_GENERATOR.generate()

def clean_text_for_search(text: str):
    text = re.sub(r"(\w+)/(\w+)", r"\1/\2 (\1 \2)", text)
    text = re.sub(r"(\w+)-(\w+)", r"\1-\2 (\1 \2)", text)
    text = re.sub(r"(\w+)&(\w+)", r"\1-\2 (\1 \2)", text)
    return text


def split_camel_case(text: str) -> str:
    result = []
    current_word = text[0]
    
    for char in text[1:]:
        if char.isupper():
            result.append(current_word)
            current_word = char
        else:
            current_word += char
            
    result.append(current_word)
    return ' '.join(result)

def is_positive_integer(value):
    try:
        if not value:
            return False
        
        num = int(value)
        return num > 0
    except (ValueError, TypeError):
        return False

from fastapi import Request

async def is_disconnected(request: Request) -> bool:
    """Check if the client has disconnected"""
    try:
        # Try to get client disconnection state
        return await request.is_disconnected()
    except:
        # If we can't determine the state, assume connected
        return False
    
def now():
    return datetime.datetime.now(datetime.timezone.utc)