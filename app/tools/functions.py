import json
from prisma import Prisma
from typing import Dict, Any


class ToolFunctions:
    def __init__(self, db: Prisma):
        self.db = db

    def execute_function(
        self, function_name: str, arguments: Dict[str, Any], **kwargs
    ) -> Dict[str, Any]:
        arguments: Dict[str] = json.loads(arguments)
        if function_name == "say_hello":
            return self.say_hello(arguments["to"], **kwargs)
        else:
            raise ValueError(f"Unknown function: {function_name}")
    
    def say_hello(self, to, **kwargs):
        return f"What's gud, {to}! Nice meeting you again"