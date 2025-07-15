import logging
from fastapi import APIRouter, HTTPException, Query

from src.services.gbp_analyzer import GBPAnalyzer
from src.core.config import config
from src.api.v1.schemas.analyzer_schemas import WebsiteSocialsResponse, AnalysisRequest

router = APIRouter()


@router.post(
    "/website_socials",
    summary="Analyze a Google Business Profile",
    response_model=WebsiteSocialsResponse,
)
def web_socials(request: AnalysisRequest):
    """
    Performs a full analysis of a Google Business Profile.
    Provide EITHER a `query` or a `place_id`.
    """
    try:

        analyser = GBPAnalyzer(api_key=config.SERP_API_KEY)
    except ValueError as e:
        raise HTTPException(status_code=503, detail=f"Service Unavailable: {e}")

    logging.info(
        f"Received API request. Query: '{request.query}', Place ID: '{request.place_id}'"
    )

    result = analyser.website_socials(query=request.query, place_id=request.place_id)

    if not result.get("success"):
        error_message = result.get("error", "An unknown error occurred.")
        if "No links found" in error_message:
            raise HTTPException(status_code=404, detail=error_message)

        raise HTTPException(status_code=500, detail=f"Scrapping Error: {error_message}")

    return result
