import os
from pydantic_settings import BaseSettings
from pydantic import Field, HttpUrl, SecretStr, PositiveInt
from dotenv import load_dotenv
from typing import Optional

# Load .env file explicitly before BaseSettings reads it
# This ensures variables are available if BaseSettings is imported early
load_dotenv()

class Settings(BaseSettings):
    """Application Configuration"""

    # --- AI Keys & URLs ---
    gemini_api_key: Optional[SecretStr] = Field(None, description="API Key for Google Gemini")
    ollama_url: HttpUrl = Field(HttpUrl("http://localhost:11434"), description="URL for the Ollama API server")
    lmstudio_url: HttpUrl = Field(HttpUrl("http://localhost:1234/v1"), description="URL for the LMStudio OpenAI-compatible API endpoint")

    # --- AI Model Selection ---
    # Provide defaults, but allow override via .env
    ollama_model: str = Field("phi4", description="Default model name for Ollama")
    lmstudio_model: Optional[str] = Field("gemma-3-1b-it-GGUF/gemma-3-1b-it-Q4_K_M.gguf", description="Model identifier for LMStudio")
    gemini_model: str = Field("models/gemini-1.5-flash-latest", description="Model identifier for Gemini")

    # --- Redis ---
    # Note: Redis is currently unused in main.py, but keeping config here
    redis_host: str = Field("localhost", description="Hostname for Redis server")
    redis_port: PositiveInt = Field(6379, description="Port for Redis server")
    redis_db: int = Field(0, description="Redis database number")

    # --- Web App ---
    app_host: str = Field("localhost", description="Host for the FastAPI application")
    app_port: PositiveInt = Field(5001, description="Port for the FastAPI application")
    app_base_url: HttpUrl = Field(HttpUrl("http://localhost:5001"), description="Base URL of the application (used for OAuth redirect)")
    # Secret key for session middleware - MUST be set in production
    session_secret_key: SecretStr = Field(SecretStr("default-insecure-secret-key-replace-me"), description="Secret key for session management")

    # --- Google OAuth ---
    google_client_id: Optional[str] = Field(None, description="Google OAuth Client ID")
    google_client_secret: Optional[SecretStr] = Field(None, description="Google OAuth Client Secret")
    # These are generally static for Google, but configurable just in case
    google_auth_uri: HttpUrl = Field(HttpUrl("https://accounts.google.com/o/oauth2/v2/auth"), description="Google OAuth Authorization URI")
    google_token_uri: HttpUrl = Field(HttpUrl("https://oauth2.googleapis.com/token"), description="Google OAuth Token URI")
    google_userinfo_uri: HttpUrl = Field(HttpUrl("https://www.googleapis.com/oauth2/v3/userinfo"), description="Google OAuth UserInfo URI")

    # --- Pydantic Settings Configuration ---
    model_config = {
        # Load from .env file if it exists
        "env_file": '.env',
        "env_file_encoding": 'utf-8',
        # Allow extra fields (though we aim to define all)
        "extra": 'ignore',
        # Make SecretStr fields case-insensitive loading from env
        "case_sensitive": False # Primarily for environment variables
    }

# Create a single instance of the settings to be imported by other modules
settings = Settings()  # type: ignore

# --- Perform some basic validation checks ---
if settings.google_client_id is None or settings.google_client_secret is None:
     print("WARNING: GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET not found in environment/config. Google OAuth will not work.")

if settings.session_secret_key.get_secret_value() == "default-insecure-secret-key-replace-me":
    print("WARNING: Using default SESSION_SECRET_KEY. Please set a strong secret in your .env file for security.")