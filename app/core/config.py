from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from os import getenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    DATABASE_URL: str = getenv("DATABASE_URL")
    