from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    # Telegram
    bot_token: str = Field(..., env="BOT_TOKEN")

    # Database
    database_url: str = Field(..., env="DATABASE_URL")

    # AI
    ai_provider: str = Field("openrouter", env="AI_PROVIDER")

    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    openai_model: str = Field("gpt-4.1-mini", env="OPENAI_MODEL")

    openrouter_api_key: Optional[str] = Field(None, env="OPENROUTER_API_KEY")
    openrouter_model: str = Field(
        "meta-llama/llama-3.1-8b-instruct", env="OPENROUTER_MODEL"
    )

    class Config:
        env_file = ".env"
        extra = "allow"
