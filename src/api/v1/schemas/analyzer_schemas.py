from pydantic import BaseModel, Field, model_validator, HttpUrl
from typing import Dict, Any, Optional, List


class AnalysisRequest(BaseModel):
    """
    Defines the request body for the /analyze endpoint.
    A user must provide EITHER a query OR a place_id.
    """

    query: Optional[str] = Field(
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

    @model_validator(mode="before")
    def check_exactly_one_field_is_provided(cls, values):
        """Ensures that either 'query' or 'place_id' is provided, but not both."""
        query, place_id = values.get("query"), values.get("place_id")
        if (query and place_id) or (not query and not place_id):
            raise ValueError("You must provide exactly one of 'query' or 'place_id'.")

        return values


class WebsiteSocialsData(BaseModel):
    website: Optional[HttpUrl] = None
    social_links: List[Dict[str, str]] = []


class WebsiteSocialsResponse(BaseModel):
    success: bool
    data: WebsiteSocialsData


class AnalysisResponse(BaseModel):
    """
    The successful response model for the /analyze endpoint.
    It contains the final score and the detailed raw data.
    """

    score: str
    data: Dict[str, Any]
