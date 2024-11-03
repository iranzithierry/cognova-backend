from app.providers.chat import ChatProvider
from .tools import tools

class ToolService:
    def __init__(self, provider: ChatProvider) -> None:
        self.provider = provider
        self.tools: list[dict] = self.initialize()

    def initialize(self):
        tools_list = []
        for tool in tools:
            tool_object = self.add_tool(tool["name"], tool["description"], tool["parameters"])
            tools_list.append(tool_object)
        return  tools_list


    def add_tool(self, tool_name: str, tool_description: str, tool_parameters: list[dict[str, str]]):
        tool_object = self.generate_tool_object(tool_name, tool_description, tool_parameters)
        return tool_object
        
    def generate_tool_object(self, tool_name: str, tool_description: str, tool_parameters: list[dict[str, str]]) -> dict:
        if isinstance(self.provider, ChatProvider):
            return self.provider._convert_tool_definition_to_dict(tool_name, tool_description, tool_parameters)
        else:
            raise ValueError("Unsupported provider.")
        

