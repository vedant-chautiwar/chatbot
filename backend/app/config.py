import logging
from pathlib import Path
from typing import Any, List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

# Resolve candidate paths to the .env file.
# config.py lives at: <project_root>/backend/app/config.py
# parents[0] = backend/app, parents[1] = backend, parents[2] = <project_root>
_ROOT_ENV = Path(__file__).resolve().parents[2] / ".env"
_BACKEND_ENV = Path(__file__).resolve().parents[1] / ".env"
_CWD_ENV = Path.cwd() / ".env"
_ENV_FILES = (str(_ROOT_ENV), str(_BACKEND_ENV), str(_CWD_ENV))


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILES,
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @field_validator("GROQ_API_KEY", "TAVILY_API_KEY", mode="before")
    @classmethod
    def clean_api_keys(cls, v: Any) -> str:
        """Strip surrounding whitespace and quotation marks from API keys."""
        if isinstance(v, str):
            return v.strip().strip('"\'').strip()
        return "" if v is None else str(v)

    # Environment
    ENVIRONMENT: str = Field(default="development", description="Current running environment")

    # Groq LLM
    GROQ_API_KEY: str = Field(default="", description="Groq API key")
    GROQ_MODEL: str = Field(
        default="openai/gpt-oss-120b",
        description="Groq model ID supporting reliable tool calling",
    )

    # Tavily Web Search
    TAVILY_API_KEY: str = Field(default="", description="Tavily Search API key")
    TAVILY_MAX_RESULTS: int = Field(default=5, description="Max search results per query")
    TAVILY_SEARCH_DEPTH: str = Field(default="basic", description="Search depth: 'basic' or 'advanced'")

    # MongoDB Atlas
    MONGODB_URI: str = Field(
        default="mongodb://localhost:27017",
        description="MongoDB connection URI (Atlas or local)",
    )
    MONGODB_DATABASE: str = Field(default="chatbot_db", description="Database name")

    # FastAPI Authentication & JWT
    JWT_SECRET: str = Field(
        default="dev-super-secure-jwt-secret-key-32-chars-long!!",
        description="JWT signing secret key for FastAPI authentication",
    )
    JWT_ALGORITHM: str = Field(
        default="HS256",
        description="JWT signing algorithm",
    )
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=1440,
        description="Access token expiration in minutes (default 24h)",
    )

    # Application Settings
    FRONTEND_ORIGIN: str = Field(
        default="http://localhost:3000,http://localhost:5173",
        description="Allowed frontend origin(s), comma-separated",
    )
    MAX_HISTORY_MESSAGES: int = Field(
        default=10,
        description="Bounded conversation history messages to pass to the agent",
    )

    @property
    def cors_origins(self) -> List[str]:
        """Parse comma-separated origins into a list of cleaned strings."""
        if not self.FRONTEND_ORIGIN:
            return ["*"]
        return [origin.strip() for origin in self.FRONTEND_ORIGIN.split(",") if origin.strip()]

    @property
    def effective_jwt_secret(self) -> str:
        """Resolve the active JWT signing secret."""
        return self.JWT_SECRET or "dev-super-secure-jwt-secret-key-32-chars-long!!"

    def validate_runtime_keys(self) -> None:
        """Log helpful warnings if critical keys are missing for live operation."""
        missing = []
        if not self.GROQ_API_KEY:
            missing.append("GROQ_API_KEY")
        if not self.TAVILY_API_KEY:
            missing.append("TAVILY_API_KEY")
        if missing and self.ENVIRONMENT != "testing":
            logger.warning(
                "Missing environment variables for live integrations: %s. "
                "Backend will run with degraded capabilities until provided in .env.",
                ", ".join(missing),
            )


settings = Settings()
