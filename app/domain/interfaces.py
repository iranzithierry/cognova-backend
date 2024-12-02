import json
from enum import Enum
from dataclasses import dataclass
from prisma.enums import ChatFeedback
from typing import Optional, Dict, Any, List, TypeVar, Generic
from prisma.fields import Json


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


T = TypeVar("T")


@dataclass
class ChatResponse(Generic[T]):
    content: T
    error: Optional[str] = None


@dataclass
class Completion:
    response: str


class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class ToolCall:
    name: str
    arguments: Dict[str, Any]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolCall":
        return cls(name=data.get("name"), arguments=data.get("arguments", {}))


@dataclass
class Message:
    role: str
    content: str
    toolCalls: Optional[list[dict]] = None
    toolCallId: Optional[str] = None
    tokens: Optional[int] = None
    feedback: Optional[str] = ChatFeedback.NONE.value

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "content": str(self.content),
            "toolCalls": json.dumps(self.toolCalls if self.toolCalls else []),
            "toolCallId": self.toolCallId,
            "tokens": self.tokens or len(str(self.content).split()),
            "feedback": self.feedback,
        }
