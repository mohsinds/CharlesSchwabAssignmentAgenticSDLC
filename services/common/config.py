"""Application settings — all LLM traffic routes through LiteLLM."""

import os
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LiteLLM
    litellm_base_url: str = "http://localhost:4000"
    litellm_api_key: str = "sk-agentic-sdlc-local"
    litellm_model_default: str = "gpt-4o-mini"
    litellm_model_judge: str = "gpt-4o-mini"
    litellm_model_embedding: str = "text-embedding-3-small"

    # LangSmith
    langsmith_api_key: str = ""
    langsmith_endpoint: str = "https://api.smith.langchain.com"
    langsmith_tracing: bool = False
    langsmith_project: str = "agentic-sdlc"

    # Temporal
    temporal_host: str = "localhost:7233"
    temporal_namespace: str = "default"
    temporal_task_queue_workflows: str = "sdlc-workflows"
    temporal_task_queue_agents: str = "agent-activities"
    temporal_task_queue_policy: str = "policy-activities"
    temporal_task_queue_audit: str = "audit-activities"

    # Data
    database_url: str = "postgresql+asyncpg://sdlc:sdlc@localhost:5432/sdlc"
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "sdlc-audit"
    minio_secure: bool = False
    audit_fs_fallback_dir: str = "./data/audit"
    artifacts_dir: str = "./artifacts"

    # Policy / judge
    opa_url: str = "http://localhost:8181"
    judge_pass_threshold: float = 0.7
    coverage_min: float = 0.6
    replan_max: int = 3

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    demo_mode_default: bool = False

    dag_path: Path = Field(default_factory=lambda: ROOT_DIR / "dag" / "sdlc.yaml")
    dag_schema_path: Path = Field(default_factory=lambda: ROOT_DIR / "dag" / "schema.json")
    prompts_dir: Path = Field(default_factory=lambda: ROOT_DIR / "prompts")
    policies_dir: Path = Field(default_factory=lambda: ROOT_DIR / "policies")
    scenarios_dir: Path = Field(default_factory=lambda: ROOT_DIR / "scenarios")

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


def configure_langsmith() -> bool:
    """Set the standard LangChain tracing env vars from our settings.

    LangChain's SDK auto-instruments ChatOpenAI/embeddings calls when
    LANGCHAIN_TRACING_V2 + LANGCHAIN_API_KEY are present in the environment.
    Call once at process startup (API + worker). Returns True if tracing
    was enabled.
    """
    settings = get_settings()
    if not (settings.langsmith_tracing and settings.langsmith_api_key):
        os.environ["LANGCHAIN_TRACING_V2"] = "false"
        return False
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = settings.langsmith_api_key
    os.environ["LANGCHAIN_ENDPOINT"] = settings.langsmith_endpoint
    os.environ["LANGCHAIN_PROJECT"] = settings.langsmith_project
    return True


def get_chat_model(model: str | None = None):
    """OpenAI-compatible chat client pointed at LiteLLM proxy."""
    from langchain_openai import ChatOpenAI

    settings = get_settings()
    return ChatOpenAI(
        base_url=f"{settings.litellm_base_url.rstrip('/')}/v1",
        api_key=settings.litellm_api_key,
        model=model or settings.litellm_model_default,
        temperature=0.2,
    )


def get_embeddings(model: str | None = None):
    """OpenAI-compatible embeddings client pointed at LiteLLM proxy."""
    from langchain_openai import OpenAIEmbeddings

    settings = get_settings()
    return OpenAIEmbeddings(
        base_url=f"{settings.litellm_base_url.rstrip('/')}/v1",
        api_key=settings.litellm_api_key,
        model=model or settings.litellm_model_embedding,
    )
