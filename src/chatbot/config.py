"""
Configuration management using Pydantic Settings.

This module provides type-safe configuration loaded from environment variables.
All settings are automatically validated and converted to the correct types.

Usage:
    from chatbot.config import get_settings

    settings = get_settings()
    print(settings.anthropic_api_key)  # Type-safe access
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    All settings are type-checked and validated automatically.
    Required settings will raise an error if not provided.
    Optional settings have sensible defaults.
    """

    # ============================================================================
    # API Server Configuration
    # ============================================================================

    api_host: str = Field(
        default="0.0.0.0",
        description="API server host address"
    )

    api_port: int = Field(
        default=8000,
        description="API server port",
        ge=1024,  # Greater than or equal to 1024 (avoid privileged ports)
        le=65535  # Less than or equal to 65535
    )

    api_reload: bool = Field(
        default=False,
        description="Enable auto-reload for development"
    )

    # ============================================================================
    # AI Provider Configuration
    # ============================================================================

    provider_type: Literal["anthropic", "openai", "ollama"] = Field(
        default="anthropic",
        description="AI provider to use"
    )

    anthropic_api_key: str = Field(
        default="",
        description="Anthropic API key (required when provider_type=anthropic)"
    )

    # Future provider keys (Phase 5)
    openai_api_key: str = Field(
        default="",
        description="OpenAI API key (required when provider_type=openai)"
    )

    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Ollama server URL (used when provider_type=ollama)"
    )

    # ============================================================================
    # Model Configuration
    # ============================================================================

    default_model: str = Field(
        default="claude-3-5-sonnet-20241022",
        description="Default AI model to use"
    )

    default_temperature: float = Field(
        default=0.7,
        description="Default response randomness (0.0-1.0)",
        ge=0.0,
        le=1.0
    )

    default_max_tokens: int = Field(
        default=1000,
        description="Default maximum tokens in response",
        ge=1,
        le=100000
    )

    # ============================================================================
    # Database Configuration (Phase 3+)
    # ============================================================================

    database_url: str = Field(
        default="sqlite+aiosqlite:///./chatbot.db",
        description="Database connection URL"
    )

    # ============================================================================
    # Vector Database Configuration (Phase 4+)
    # ============================================================================

    chroma_persist_directory: str = Field(
        default="./chroma_data",
        description="ChromaDB persistence directory"
    )

    # ============================================================================
    # Memory Configuration (Phase 2+)
    # ============================================================================

    short_term_max_messages: int = Field(
        default=50,
        description="Maximum messages to keep in short-term memory",
        ge=1
    )

    short_term_max_tokens: int = Field(
        default=8000,
        description="Maximum tokens in short-term memory context",
        ge=100
    )

    semantic_top_k: int = Field(
        default=5,
        description="Number of semantic memory results to retrieve",
        ge=1,
        le=20
    )

    # ============================================================================
    # Pydantic Settings Configuration
    # ============================================================================

    model_config = SettingsConfigDict(
        env_file=".env",  # Load from .env file
        env_file_encoding="utf-8",
        case_sensitive=False,  # API_PORT and api_port both work
        extra="ignore",  # Ignore extra env vars not defined here
    )

    def validate_provider_config(self) -> None:
        """
        Validate that required API keys are present for the selected provider.

        Raises:
            ValueError: If provider-specific configuration is missing
        """
        if self.provider_type == "anthropic" and not self.anthropic_api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY must be set when provider_type is 'anthropic'"
            )

        if self.provider_type == "openai" and not self.openai_api_key:
            raise ValueError(
                "OPENAI_API_KEY must be set when provider_type is 'openai'"
            )


@lru_cache()
def get_settings() -> Settings:
    """
    Get the application settings.

    Uses @lru_cache to ensure we only load settings once and reuse the same
    instance throughout the application. This is more efficient and ensures
    consistency.

    Returns:
        Settings: The application settings instance

    Example:
        >>> settings = get_settings()
        >>> print(settings.api_port)
        8000
        >>> print(settings.default_temperature)
        0.7
    """
    settings = Settings()
    settings.validate_provider_config()
    return settings
