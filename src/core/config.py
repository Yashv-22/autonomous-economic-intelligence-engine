"""
Centralized Configuration and Environment Management.
"""

import os
from typing import List, Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load configuration from .env file
load_dotenv(override=True)


class SecurityConfig(BaseModel):
    """Network & Security policy configuration."""
    allowed_schemes: List[str] = Field(default_factory=lambda: ["http", "https"])
    blocked_ip_ranges: List[str] = Field(
        default_factory=lambda: [
            "127.0.0.0/8",      # Loopback
            "10.0.0.0/8",       # Private RFC 1918
            "172.16.0.0/12",    # Private RFC 1918
            "192.168.0.0/16",   # Private RFC 1918
            "169.254.0.0/16",   # Link-local / Cloud metadata
            "::1/128",          # IPv6 loopback
            "fc00::/7",         # IPv6 Unique local
            "fe80::/10",        # IPv6 Link-local
        ]
    )
    max_request_size_bytes: int = 10 * 1024 * 1024  # 10 MB limit
    request_timeout_seconds: float = 15.0
    rate_limit_per_minute: int = 60
    enable_prompt_injection_defense: bool = True
    enforce_strict_ssrf_check: bool = True


class StorageConfig(BaseModel):
    """Storage & Database configuration."""
    sqlite_db_path: str = "output/intelligence_ledger.db"
    artifacts_dir: str = "output"
    vector_dimension: int = 384
    similarity_threshold: float = 0.70


class ResearchBudgetConfig(BaseModel):
    """Budget and stopping criteria for research loops."""
    max_search_depth: int = 3
    max_queries_per_objective: int = 5
    max_sources_per_query: int = 5
    max_total_claims: int = 1000
    evidence_confidence_threshold: float = 0.65


class ModelGatewayConfig(BaseModel):
    """Model provider and routing configuration."""
    default_provider: str = Field(default_factory=lambda: os.environ.get("DEFAULT_LLM_PROVIDER", "omniroute"))
    gemini_api_key: Optional[str] = Field(default_factory=lambda: os.environ.get("GEMINI_API_KEY"))
    gemini_model_name: str = Field(default_factory=lambda: os.environ.get("GEMINI_MODEL_NAME", "gemini-3.7-flash"))
    openai_api_key: Optional[str] = Field(default_factory=lambda: os.environ.get("OPENAI_API_KEY"))
    openai_model_name: str = Field(default_factory=lambda: os.environ.get("OPENAI_MODEL_NAME", "gpt-4o"))
    openai_base_url: str = Field(default_factory=lambda: os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"))
    freellmapi_base_url: str = Field(default_factory=lambda: os.environ.get("FREELLMAPI_BASE_URL", "http://127.0.0.1:3001/v1"))
    freellmapi_api_key: Optional[str] = Field(default_factory=lambda: os.environ.get("FREELLMAPI_API_KEY"))
    freellmapi_default_model: str = Field(default_factory=lambda: os.environ.get("FREELLMAPI_DEFAULT_MODEL", "auto"))
    omniroute_base_url: str = Field(default_factory=lambda: os.environ.get("OMNIROUTE_BASE_URL", "http://127.0.0.1:20128/v1"))
    omniroute_api_key: Optional[str] = Field(default_factory=lambda: os.environ.get("OMNIROUTE_API_KEY"))
    omniroute_default_model: str = Field(default_factory=lambda: os.environ.get("OMNIROUTE_DEFAULT_MODEL", "research-general"))
    max_retries: int = 3
    timeout_seconds: float = 30.0
    enable_cost_accounting: bool = True


class SystemSettings(BaseSettings):
    """Master System Configuration."""
    model_config = SettingsConfigDict(env_prefix="AI_OP_", env_file=".env", extra="ignore")

    app_name: str = "Autonomous AI Operating-Model Intelligence System"
    environment: str = "development"
    debug: bool = False
    log_level: str = "INFO"

    security: SecurityConfig = Field(default_factory=SecurityConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    research: ResearchBudgetConfig = Field(default_factory=ResearchBudgetConfig)
    model: ModelGatewayConfig = Field(default_factory=ModelGatewayConfig)


# Global settings singleton
settings = SystemSettings()
