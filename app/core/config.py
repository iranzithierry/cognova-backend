import os
from dotenv import load_dotenv
from typing import Literal


class Config:
    def __init__(self):
        load_dotenv()

        # Database settings
        self.DB_URL = os.getenv("DATABASE_URL")
        self.DB_HOST = os.environ.get("DB_HOST", "localhost")
        self.DB_NAME = os.environ.get("DB_NAME", "cognova")
        self.DB_USER = os.environ.get("DB_USER", "root")
        self.DB_PASSWORD = os.environ.get("DB_PASSWORD", "1234")

        # EMBEDDING settings
        self.EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL")
        self.EMBEDDING_API_KEY = os.environ.get("EMBEDDING_API_KEY")
        self.EMBEDDING_BASE_URL = os.environ.get("EMBEDDING_BASE_URL")
