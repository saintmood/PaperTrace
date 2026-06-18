from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ApplicationConfig(BaseSettings):
    """
    Centralized Application Configuration.
    Validates environment variables on startup. If a required variable
    is missing, the app will fail fast before any execution begins.
    """

    llm_model_name: str = Field(
        default="ollama/qwen2.5-coder-7b-instruct-q6_k-00001-of-00002.gguf",
        description="The specific LLM version to use for extraction.",
    )

    # 2. File System and Database Paths
    database_path: str = Field(
        default="db/archive.db", description="Relative or absolute path to the SQLite database."
    )
    storage_path: str = Field(
        default="storage/archives",
        description="Directory where approved PDFs will be permanently stored.",
    )

    # 3. Protective Shields (The "Sarcophagus" Limits)
    max_execution_loops: int = Field(
        default=3, description="Maximum allowed iterations for the Refinement (Critic) loop."
    )
    max_token_budget: int = Field(
        default=10000, description="Maximum tokens allowed per processing pipeline run."
    )
    # Tell Pydantic to read from the local .env file
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # Ignore any extra variables in the .env file
    )

    ollama_base_url: str = Field(
        default="http://127.0.0.1:8080",
    )

    ollama_api_key: str = Field(
        default="sk-no-key-required",
    )

    worker_max_retries: int = Field(
        default=3, description="Maximum retries for worker tasks before giving up."
    )


settings = ApplicationConfig()
