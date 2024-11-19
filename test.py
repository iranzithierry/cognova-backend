import asyncio
from typing import Dict, List, Any, AsyncGenerator
from langchain.schema.runnable import RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate
from app.infrastructure.ai.tools.pydantic_tools import business
from langchain_community.llms.cloudflare_workersai import CloudflareWorkersAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain.agents.format_scratchpad import format_to_openai_function_messages


def generate_hermess_system_prompt(tools_str: str):
    system_prompt = (
        """
You are provided with function signatures within <tools></tools> XML tags. You may call one or more functions to assist with the user query. Don't make assumptions about what values to plug into functions. Here are the available tools:
<tools>
"""
        + f"""
{str(tools_str)}
"""
        + """
</tools>
Use the following pydantic model json schema for each tool call you will make: {'title': 'FunctionCall', 'type': 'object', 'properties': {'arguments': {'title': 'Arguments', 'type': 'object'}, 'name': {'title': 'Name', 'type': 'string'}}, 'required': ['arguments', 'name']} For each function call return a json object with function name and arguments within <tool_call></tool_call> XML tags as follows:
<tool_call>
{'arguments': <args-dict>, 'name': <function-name>}
</tool_call>
"""
    )

    return system_prompt


class ChatService:
    def __init__(self):
        self.business_functions = business

    def generate_system_prompt(self) -> str:
            """Generate the system prompt with tool descriptions."""
            functions = str(self.business_functions.get_all_business_functions())
            
            return f"""You are a helpful AI assistant that can help customers find products and get business information.
    You have access to the following tools:

    To use a tool, format your response as a function call using this structure:
    <tool_call>
    {{{{
        "name": "<tool_name>",
        "arguments": {{{{
            "arg1": "value1",
            "arg2": "value2"
        }}}}
    }}}}
    </tool_call>

    Respond conversationally and use tools when needed to get accurate information.
    """

    async def handle_chat(
        self,
        user_message: str,
    ) -> AsyncGenerator[str, None]:
        llm = CloudflareWorkersAI(
            account_id="no-account-cf",
            api_token="no-api-cf",
            model="@hf/nousresearch/hermes-2-pro-mistral-7b",
            base_url="http://127.0.0.1:8080",
            endpoint_url="",
        )
        business_functions = self.business_functions.get_all_business_functions()
        business_tools = self.business_functions.get_all_business_tools()

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.generate_system_prompt()),
                ("user", "{input}"),
                ("assistant", "{agent_scratchpad}"),
            ]
        )

        llm_with_tools = llm.bind(functions=business_functions)
        # Create agent chain
        agent = (
            {
                "input": lambda x: x["input"],
                "agent_scratchpad": lambda x: format_to_openai_function_messages(
                    x["intermediate_steps"]
                ),
            }
            | prompt
            | llm_with_tools
        )
        agent_executor = AgentExecutor(agent=agent, tools=business_tools, verbose=True)
        async for event in agent_executor.astream_events(
            {"input": user_message}, version="v1"
        ):
            print(event)
            yield event
            # if event.get("type") == "on_chat_model_stream":
            #     yield event.get("data", "")


# Example usage
async def main():
    chat_service = ChatService()
    async for response in chat_service.handle_chat("Do you have any Adidas Yeezy?"):
        print(response)


if __name__ == "__main__":
    asyncio.run(main())
