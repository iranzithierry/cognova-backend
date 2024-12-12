class StreamProcessingError(Exception):
    """Raised when stream processing fails"""
    pass

class ToolProcessingError(Exception):
    """Raised when tool processing fails"""
    pass
class PrismaExecutionError(Exception):
    """Raised when Prisma execution fails"""
    pass
class ToolExecutionError(Exception):
    """Custom exception for tool execution failures"""

    pass
class ClientDisconnectError(Exception):
    """Raised when client disconnects during streaming"""
    pass