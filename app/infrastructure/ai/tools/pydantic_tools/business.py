from pydantic.v1 import BaseModel, Field
from langchain.tools import StructuredTool
from langchain_core.utils.function_calling import convert_to_openai_tool
from app.infrastructure.ai.tools.functions.business import BusinessFunctions

class SearchProducts(BaseModel):
    query: str = Field(
        description="The name/brand/category/description key of the product to search for."
    )

def get_all_business_tools() -> list[StructuredTool]:
    business_functions = BusinessFunctions("-")
    search_products = StructuredTool.from_function(description="Search for products with filters.", func=business_functions.search_products, name="search_products", args_schema=SearchProducts)

    business_tools = [
        search_products,
    ]
    return business_tools

def get_all_business_functions():
    """Convert business tools to OpenAI function format."""
    business_tools = get_all_business_tools()
    business_functions = [convert_to_openai_tool(f) for f in business_tools]
    return business_functions