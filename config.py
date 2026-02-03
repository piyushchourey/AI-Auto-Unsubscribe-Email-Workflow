from pydantic_settings import BaseSettings
from typing import Literal, Dict


# Predefined email provider configurations
EMAIL_PROVIDERS: Dict[str, Dict[str, any]] = {
    "outlook": {
        "host": "outlook.office365.com",
        "port": 993,
        "ssl": True,
        "description": "Microsoft Outlook / Office 365"
    },
    "gmail": {
        "host": "imap.gmail.com",
        "port": 993,
        "ssl": True,
        "description": "Google Gmail"
    },
    "rediff": {
        "host": "imap.rediffmailpro.com",
        "port": 993,
        "ssl": True,
        "description": "Rediff Mail Pro"
    },
    "yahoo": {
        "host": "imap.mail.yahoo.com",
        "port": 993,
        "ssl": True,
        "description": "Yahoo Mail"
    },
    "custom": {
        "host": "",
        "port": 993,
        "ssl": True,
        "description": "Custom IMAP Server"
    }
}


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # LLM Configuration
    llm_provider: Literal["ollama", "gemini"] = "ollama"
    ollama_model: str = "llama2"
    ollama_base_url: str = "http://localhost:11434"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-pro"
    
    # Brevo Configuration
    brevo_api_key: str = ""
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    
    # IMAP Configuration
    imap_enabled: bool = False
    imap_provider: Literal["outlook", "gmail", "rediff", "yahoo", "custom"] = "outlook"
    imap_host: str = ""  # Will be set from provider if empty
    imap_port: int = 993
    imap_email: str = ""
    imap_password: str = ""
    imap_check_interval: int = 3600  # 1 hour in seconds
    imap_folder: str = "INBOX"
    
    def get_imap_host(self) -> str:
        """Get IMAP host based on provider or custom host"""
        if self.imap_host:
            return self.imap_host
        return EMAIL_PROVIDERS.get(self.imap_provider, {}).get("host", "")
    
    def get_imap_port(self) -> int:
        """Get IMAP port based on provider or custom port"""
        if self.imap_port != 993:  # If user set custom port
            return self.imap_port
        return EMAIL_PROVIDERS.get(self.imap_provider, {}).get("port", 993)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
