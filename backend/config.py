from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')
    qdrant_path: str = 'data/qdrant'
    qdrant_url: str = ''
    qdrant_api_key: str = ''
    embedding_backend: str = 'fastembed'
    embedding_model: str = 'BAAI/bge-small-en-v1.5'
    generation_mode: str = 'extractive'
    gemini_api_key: str = ''
    gemini_model: str = 'gemini-2.5-flash'
    admin_api_key: str = ''
    cors_origins: list[str] = ['http://localhost:3000']
    min_score: float = Field(default=0.35, ge=0, le=1)


@lru_cache
def settings():
    return Settings()
