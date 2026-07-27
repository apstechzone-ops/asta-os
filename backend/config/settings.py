from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "Asta OS"
    ENV: str = "development"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "asta"
    POSTGRES_USER: str = "asta"
    POSTGRES_PASSWORD: str = "changeme"

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # Vector DB
    CHROMA_HOST: str = "chroma.railway.internal"
    CHROMA_PORT: int = 8000

    # AI
    # AI Providers — config-driven, no code changes needed to reorder/add/remove
    AI_PROVIDER_PRIORITY: str = "ollama,openrouter,cloudflare"

    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen3:8b"
    OLLAMA_TIMEOUT: float = 60.0
    OLLAMA_MAX_TOKENS: int = 1024
    OLLAMA_TEMPERATURE: float = 0.7
    OLLAMA_RETRY_COUNT: int = 1
    OLLAMA_CONTEXT_WINDOW: int = 8192  # depends entirely on which model you've pulled — edit to match
    OLLAMA_GOOD_FOR: str = "general,coding"  # comma list of task-type tags; user-editable, not a benchmark claim
    OLLAMA_COST_PER_1K_INPUT: float = 0.0  # local inference — genuinely free
    OLLAMA_COST_PER_1K_OUTPUT: float = 0.0

    OPENROUTER_API_KEY: str = "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"
    OPENROUTER_MODEL: str = "meta-llama/llama-3.1-8b-instruct:free"
    OPENROUTER_TIMEOUT: float = 60.0
    OPENROUTER_MAX_TOKENS: int = 1024
    OPENROUTER_TEMPERATURE: float = 0.7
    OPENROUTER_RETRY_COUNT: int = 1
    OPENROUTER_CONTEXT_WINDOW: int = 8192
    OPENROUTER_GOOD_FOR: str = "general"
    OPENROUTER_COST_PER_1K_INPUT: float = 0.0  # 0.0 while using a :free model; set real rates if you switch models
    OPENROUTER_COST_PER_1K_OUTPUT: float = 0.0

    CLOUDFLARE_ACCOUNT_ID: str = ""
    CLOUDFLARE_API_TOKEN: str = ""
    CLOUDFLARE_MODEL: str = "@cf/meta/llama-3.1-8b-instruct"
    CLOUDFLARE_TIMEOUT: float = 60.0
    CLOUDFLARE_MAX_TOKENS: int = 1024
    CLOUDFLARE_TEMPERATURE: float = 0.7
    CLOUDFLARE_RETRY_COUNT: int = 1
    CLOUDFLARE_CONTEXT_WINDOW: int = 4096
    CLOUDFLARE_GOOD_FOR: str = "general"
    CLOUDFLARE_COST_PER_1K_INPUT: float = 0.0  # 0.0 within the 10k free Neurons/day quota
    CLOUDFLARE_COST_PER_1K_OUTPUT: float = 0.0

    # Voice
    WHISPER_MODEL_SIZE: str = "small"
    WHISPER_DEVICE: str = "cuda"
    WHISPER_COMPUTE_TYPE: str = "int8_float16"
    PIPER_BINARY_PATH: str = "piper"
    PIPER_MODEL_PATH: str = "models/piper/en_US-lessac-medium.onnx"

    # Google Workspace
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/google/callback"
    GOOGLE_SCOPES: list[str] = [
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/drive.readonly",
        "https://www.googleapis.com/auth/calendar.readonly",
        "https://www.googleapis.com/auth/documents",
    ]

    # Auth
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # CORS
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:5173",
        "https://fabulous-truth-production-a69c.up.railway.app",
    ]

    LOG_LEVEL: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
