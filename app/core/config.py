import os
from dotenv import load_dotenv
from typing import Literal


class Config:
    def __init__(self, selected_config: Literal["azure", "cognova", "openai"] = None):
        load_dotenv()

        # Database settings
        self.DB_URL = os.getenv("DATABASE_URL")
        self.DB_HOST = os.environ.get("DB_HOST", "localhost")
        self.DB_NAME = os.environ.get("DB_NAME", "cognova")
        self.DB_USER = os.environ.get("DB_USER", "root")
        self.DB_PASSWORD = os.environ.get("DB_PASSWORD", "1234")

        # API settings
        self.API_CONFIG = {
            "azure": {
                "endpoint": "https://models.inference.ai.azure.com",
                "api_key": os.environ.get("AZURE_API_KEY", ""),
                "provider": "openai",
            },
            "cognova": {
                "endpoint": "https://generative.ai.cognova.io",
                # "endpoint": "http://localhost:8080",
                "api_key": os.environ.get("COGNOVA_API_KEY", "sk-no-key-required"),
                "provider": "cloudflare",
            },
            "openai": {
                "endpoint": "https://api.openai.com/v1",
                "api_key": os.environ.get("OPENAI_API_KEY", ""),
                "provider": "openai",
            },
        }

        # OpenAI settings
        self.OPENAI_API_KEY = (
            self.API_CONFIG[selected_config]["api_key"] if selected_config else None
        )
        self.OPENAI_BASE_URL = (
            self.API_CONFIG[selected_config]["endpoint"] if selected_config else None
        )
        self.OPENAI_PROVIDER: Literal["cloudflare", "openai", "azure"] = (
            self.API_CONFIG[selected_config]["provider"] if selected_config else None
        )

        # EMBEDDING settings
        self.EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL")
        self.EMBEDDING_API_KEY = os.environ.get("EMBEDDING_API_KEY")
        self.EMBEDDING_BASE_URL = os.environ.get("EMBEDDING_BASE_URL")
