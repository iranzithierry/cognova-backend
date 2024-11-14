from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, Any, List, TypeVar, Generic

class StreamResponseType(Enum):
    TOKEN = "token"
    TOOL_CALL = "tool_call"
    ERROR = "error"

@dataclass
class ToolParameter:
    name: str
    type: str
    description: str
    required: bool = False

@dataclass
class ToolDefinition:
    name: str
    description: str
    parameters: List[ToolParameter]

@dataclass
class ToolCall:
    name: str
    arguments: Dict[str, Any]

@dataclass
class StreamResponse:
    type: StreamResponseType
    content: str
    tool_call: Optional[ToolCall] = None
    error: Optional[str] = None

T = TypeVar('T')

@dataclass
class ChatResponse(Generic[T]):
    content: T
    error: Optional[str] = None

@dataclass
class Completion:
    response: str