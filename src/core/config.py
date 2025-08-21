import os
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
    GEMINI_API_KEY: str = Field(..., validation_alias="GEMINI_API_KEY")
    GEMINI_MODEL_FLASH: str = Field(
        "gemini-2.5-flash", validate_alias="GEMINI_MODEL_FLASH"
    )
    GEMINI_MODEL_PRO: str = Field("gemini-2.5-pro", validate_alias="GEMINI_MODEL_PRO")

    GBP_ANALYSIS_PROMPT_PATH: str = Field(
        os.path.join("assets", "pre-prompt.txt"),
        validate_alias="GBP_ANALYSIS_PROMPT_PATH",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    APP_HOST: str = Field("0.0.0.0", validation_alias="APP_HOST")

    APP_PORT: int = Field(8000, validation_alias="APP_PORT")


config = Config()
