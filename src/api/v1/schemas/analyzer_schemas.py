from pydantic import BaseModel, Field, model_validator, HttpUrl
from typing import Dict, Any, Optional, List
from enum import Enum


class ModelChoice(str, Enum):
    FLASH = "flash"
    PRO = "pro"


class AnalysisRequest(BaseModel):
    """
    Defines the request body for the /analyze endpoint.
    A user must provide EITHER a query OR a place_id.
    """

    business_name: Optional[str] = Field(
        None,
        min_length=3,
        description="Fuzzy search query (e.g., 'Pilsen Yards, Chicago'). Use this if you don't know the place_id.",  # noqa
        example="Pilsen Yards, Chicago",
    )
    place_id: Optional[str] = Field(
        None,
        min_length=10,
        description="The specific Google Place ID (e.g., 'ChIJJW8vOWAtDogRA0JukJqeJeI'). This is faster and more accurate.",  # noqa
        example="ChIJJW8vOWAtDogRA0JukJqeJeI",
    )
    address: Optional[str] = Field(
        None,
        description="The expected address of the business (e.g., '123 Main St, Anytown, USA').",  # noqa
        example="1163 W 18th St, Chicago, IL 60608",
    )
    star_rating: Optional[float] = Field(
        None,
        description="The expected star rating of the business (e.g., 4.2).",
        example=4.4,
    )
    review_count: Optional[int] = Field(
        None,
        description="The expected review count of the business (e.g., 100).",
        example=774,
    )
    phone_number: Optional[str] = Field(
        None,
        description="The expected phone number of the business (e.g., '+1-555-555-5555').",  # noqa
        example="+1 312-243-2410",
    )
    model_choice: ModelChoice = Field(
        default=ModelChoice.FLASH,
        description="Choose the LLM to use for the detailed analysis.",
    )

    @model_validator(mode="before")
    def check_exactly_one_field_is_provided(cls, values):
        """Ensures that either 'query' or 'place_id' is provided, but not both."""
        if not values.get("business_name") and not values.get("place_id"):
            raise ValueError(
                "You must provide at least one of 'business_name' or 'place_id'."
            )

        return values


class AnalysisResponse(BaseModel):
    """
    The successful response model for the /analyze endpoint.
    It contains the final score and the detailed raw data.
    """

    score: float
    data: Dict[str, Any]
    detailed_analysis: str


class WebsiteSocialsData(BaseModel):
    website: Optional[HttpUrl] = None
    social_links: List[Dict[str, str]] = []


class WebsiteSocialsResponse(BaseModel):
    success: bool
    data: WebsiteSocialsData


class DetailedAnalysisRequest(BaseModel):
    """The request body for the new /detailed-analysis endpoint."""

    score: float = Field(description="The numerical score from the initial analysis.")
    data: Dict[str, Any] = Field(
        description="The data object from the initial analysis."
    )


class DetailedAnalysisResponse(BaseModel):
    """The response body for the new /detailed-analysis endpoint."""

    detailed_analysis: str
