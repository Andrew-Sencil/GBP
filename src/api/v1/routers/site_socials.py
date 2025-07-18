# src/api/v1/routers/site_socials.py

import logging
from fastapi import APIRouter, HTTPException

from src.services.gbp_analyzer import GBPAnalyzer
from src.core.config import config
from src.api.v1.schemas.analyzer_schemas import WebsiteSocialsResponse, AnalysisRequest

router = APIRouter()


@router.post(
    "/website_socials",
    summary="Retrieve Website and Social Links for a GBP",
    response_model=WebsiteSocialsResponse,
)
def web_socials(request: AnalysisRequest):
    """
    Retrieves the website and social links for a Google Business Profile.
    Provide EITHER a `business_name` or a `place_id`.
    """
    try:
        analyser = GBPAnalyzer(api_key=config.SERP_API_KEY)
    except ValueError as e:
        raise HTTPException(status_code=503, detail=f"Service Unavailable: {e}")

    # --- THE FIX IS HERE ---
    # Changed 'request.query' to 'request.business_name' to match the schema.
    logging.info(
        f"Received API request for socials. Query: '{request.business_name}', Place ID: '{request.place_id}'" # noqa
    )

    # And also fixed it here when calling the service.
    result = analyser.website_socials(
        query=request.business_name, place_id=request.place_id
    )

    if not result.get("success"):
        error_message = result.get("error", "An unknown error occurred.")
        if "No links found" in error_message:
            raise HTTPException(status_code=404, detail=error_message)
        raise HTTPException(
            status_code=500, detail=f"Analysis Error: {error_message}"
        )  # Changed from "Scrapping" to "Analysis" for consistency

    return result
