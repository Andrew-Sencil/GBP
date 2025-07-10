from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """
    Application settings, loaded from environment variables and the .env file.
    This class defines the configuration needed for the GMB Analyzer service.

    Args:
        BaseSettings: The base class for settings management from Pydantic.
    """

    SERP_API_KEY: str = Field(..., validation_alias="SERP_API_KEY")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


config = Config()
