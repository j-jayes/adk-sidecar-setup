"""
Settings for the lease reviewer agent.

Loads configuration from a .env file (or environment variables).
Sets up LiteLLM to use Google Gemini 2.5 Flash via the GOOGLE_API_KEY.
"""

import os

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load .env from the current working directory or any parent directory.
load_dotenv()


class Settings(BaseSettings):
    """Agent and service configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- LLM ---
    google_api_key: str = Field(default="", validation_alias="GOOGLE_API_KEY")
    agent_model: str = Field(
        default="gemini/gemini-2.5-flash",
        validation_alias="AGENT_MODEL",
    )

    # --- Docling sidecar ---
    docling_url: str = Field(
        default="http://docling:5001",
        validation_alias="DOCLING_URL",
    )
    docling_timeout: int = Field(
        default=300,
        validation_alias="DOCLING_TIMEOUT",
    )

    # --- Uploads ---
    upload_dir: str = Field(
        default="/uploads",
        validation_alias="UPLOAD_DIR",
    )


# Singleton settings instance
settings = Settings()

# LiteLLM uses GEMINI_API_KEY for the "gemini/" provider prefix.
# We expose our key under both names for maximum compatibility.
if settings.google_api_key:
    os.environ.setdefault("GEMINI_API_KEY", settings.google_api_key)
    os.environ.setdefault("GOOGLE_API_KEY", settings.google_api_key)

# Suppress the ADK warning that recommends switching away from LiteLLM for
# Gemini – we are intentionally using LiteLLM to keep the model layer
# swappable (e.g. for testing with other providers).
os.environ.setdefault("ADK_SUPPRESS_GEMINI_LITELLM_WARNINGS", "true")
