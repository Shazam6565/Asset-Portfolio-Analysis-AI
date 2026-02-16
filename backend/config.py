from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # LLM
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"

    # Market Data APIs
    finnhub_api_key: str = ""
    fmp_api_key: str = ""
    newsapi_api_key: str = ""
    massive_api_key: str = ""


    # App
    cors_origins: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # V3 Feature Flags (Migration)
    # V3 Feature Flags (Migration)
    ENABLE_STRUCTURED_OUTPUTS: bool = True
    ENABLE_ENTITY_RESOLUTION: bool = True
    ENABLE_STREAMING: bool = True
    DEBUG_TIMINGS: bool = True
    ENABLE_NEWS_LLM_SUMMARY: bool = True

    class Config:
        env_file = ".env"

    def validate_required(self):
        """Call on startup to warn about missing keys. Does not hard-fail for optional APIs."""
        import warnings
        if not self.openai_api_key:
            # We warn but don't crash yet, allowing the app to start even if some features fail later
            warnings.warn("OPENAI_API_KEY is not set. AI features will not work.")
        if not self.finnhub_api_key:
            warnings.warn("FINNHUB_API_KEY not set — news and sentiment data will be unavailable.")
        if not self.fmp_api_key:
            warnings.warn("FMP_API_KEY not set — enriched fundamental data will be unavailable.")
        if not self.newsapi_api_key:
            warnings.warn("NEWSAPI_API_KEY not set — NewsAPI news source will be unavailable.")
        if not self.massive_api_key:
            warnings.warn("MASSIVE_API_KEY not set - Deep metrics will use limited yfinance fallback.")


settings = Settings()
