import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BACKEND_DIR / ".env")


class Settings:
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/cs_exam_coach",
    )
    OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
    CHROMA_HOST: str = os.getenv("CHROMA_HOST", "chroma")
    CHROMA_PORT: int = int(os.getenv("CHROMA_PORT", "8000"))
    OPENAI_CHAT_MODEL: str = os.getenv("OPENAI_CHAT_MODEL", "gpt-4.1-mini")
    OPENAI_EMBEDDING_MODEL: str = os.getenv(
        "OPENAI_EMBEDDING_MODEL",
        "text-embedding-3-small",
    )
    
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "Paa943Lg4vXXMy74SL97DhX7qzkYun3T97lnjMoKRxS")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "1440")
    )
    
    
settings = Settings()
