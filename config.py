import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Brevo API
    brevo_api_key: str = Field(default="", validation_alias="BREVO_API_KEY")
    
    # FastAPI Server Configuration
    host: str = Field(default="0.0.0.0", validation_alias="HOST")
    port: int = Field(default=8000, validation_alias="PORT")
    
    # LLM Configuration
    llm_provider: str = Field(default="gemini", validation_alias="LLM_PROVIDER")
    ollama_base_url: str = Field(default="http://20.20.20.186:11434", validation_alias="OLLAMA_BASE_URL")
    ollama_model: str = Field(default="llama3.2:3b", validation_alias="OLLAMA_MODEL")
    gemini_api_key: str = Field(default="", validation_alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-2.0-flash-exp", validation_alias="GEMINI_MODEL")
    
    # Microsoft Graph API Configuration
    use_graph_api: bool = Field(default=False, validation_alias="USE_GRAPH_API")
    graph_tenant_id: str = Field(default="", validation_alias="GRAPH_TENANT_ID")
    graph_client_id: str = Field(default="", validation_alias="GRAPH_CLIENT_ID")
    graph_client_secret: str = Field(default="", validation_alias="GRAPH_CLIENT_SECRET")
    graph_user_email: str = Field(default="", validation_alias="GRAPH_USER_EMAIL")
    
    # IMAP Configuration
    imap_enabled: bool = Field(default=False, validation_alias="IMAP_ENABLED")
    imap_provider: str = Field(default="outlook", validation_alias="IMAP_PROVIDER")
    imap_host: str = Field(default="outlook.office365.com", validation_alias="IMAP_HOST")
    imap_port: int = Field(default=993, validation_alias="IMAP_PORT")
    imap_email: str = Field(default="", validation_alias="IMAP_EMAIL")
    imap_password: str = Field(default="", validation_alias="IMAP_PASSWORD")
    imap_folder: str = Field(default="INBOX", validation_alias="IMAP_FOLDER")
    imap_check_interval: int = Field(default=3600, validation_alias="IMAP_CHECK_INTERVAL")

    # Confirmation email behavior
    # If true, send a confirmation email to the sender after a successful Brevo unsubscribe
    send_confirmation_email: bool = Field(default=False, validation_alias="SEND_CONFIRMATION_EMAIL")
    
    # Database
    database_url: str = Field(default="sqlite:///./unsubscribe_logs.db", validation_alias="DATABASE_URL")

    # Auth / JWT
    jwt_secret_key: str = Field(default="change-me-in-production-use-openssl-rand-hex-32", validation_alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", validation_alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=60, validation_alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    login_rate_limit_per_minute: int = Field(default=5, validation_alias="LOGIN_RATE_LIMIT_PER_MINUTE")
    # Optional: initial admin seed (set ADMIN_EMAIL and ADMIN_PASSWORD to create first user)
    admin_seed_email: str = Field(default="", validation_alias="ADMIN_SEED_EMAIL")
    admin_seed_password: str = Field(default="", validation_alias="ADMIN_SEED_PASSWORD")


# Create settings instance
settings = Settings()
