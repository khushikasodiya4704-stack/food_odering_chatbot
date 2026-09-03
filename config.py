"""
Configuration settings for AI Food Ordering Chatbot and Analytics.
Supports multiple LLM providers (OpenAI, Google Gemini, Groq) with fallbacks.
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Base Directory
BASE_DIR = Path(__file__).resolve().parent

# Load .env file
load_dotenv(BASE_DIR / ".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    # App Information
    APP_NAME: str = "FlavorCraft Bistro AI Ordering System"
    APP_VERSION: str = "1.0.0"
    RESTAURANT_NAME: str = os.getenv("RESTAURANT_NAME", "FlavorCraft Bistro")
    RESTAURANT_PHONE: str = os.getenv("RESTAURANT_PHONE", "+1 (555) 234-5678")
    RESTAURANT_HOURS: str = os.getenv("RESTAURANT_HOURS", "Mon-Sun: 10:00 AM - 11:00 PM")
    RESTAURANT_ADDRESS: str = os.getenv("RESTAURANT_ADDRESS", "742 Evergreen Terrace, Springfield")
    
    # Financial Settings
    TAX_RATE: float = float(os.getenv("TAX_RATE", "0.08"))  # 8%
    DELIVERY_FEE: float = float(os.getenv("DELIVERY_FEE", "3.99"))
    FREE_DELIVERY_THRESHOLD: float = float(os.getenv("FREE_DELIVERY_THRESHOLD", "40.00"))

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_PATH", f"sqlite:///{BASE_DIR / 'restaurant.db'}")

    # Vector Store & RAG
    VECTOR_STORE_DIR: str = str(BASE_DIR / "data" / "chroma_db")
    DOCS_DIR: str = str(BASE_DIR / "src" / "rag" / "documents")

    # LLM Settings (Updated to current active production models)
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai").lower()
    
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL_NAME: str = os.getenv("OPENAI_MODEL_NAME", "gpt-5.4-nano")

    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    GEMINI_MODEL_NAME: str = os.getenv("GEMINI_MODEL_NAME", "gemini-3.5-flash")

    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL_NAME: str = os.getenv("GROQ_MODEL_NAME", "llama-3.3-70b-versatile")

    # Agent Settings
    TEMPERATURE: float = 0.2
    MAX_TOKENS: int = 1500


settings = Settings()
