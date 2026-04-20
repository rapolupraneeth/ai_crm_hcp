from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI CRM HCP Backend"
    app_env: str = "development"
    api_prefix: str = "/api/v1"

    database_url: str = "postgresql+psycopg2://postgres:Praneeth@localhost:5432/ai_crm_hcp"

    groq_api_key: str = Field(..., description="GROQ_API_KEY")
    groq_model: str = Field(default="llama-3.3-70b-versatile", description="Groq model name")


    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")



@lru_cache
def get_settings() -> Settings:
    return Settings()
