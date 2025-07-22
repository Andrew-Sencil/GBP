import logging
from fastapi import APIRouter, HTTPException

from src.services.gbp_analyzer import GBPAnalyzer
from src.core.config import config
from src.api.v1.schemas.analyzer_schemas import AnalysisResponse, AnalysisRequest
from src.utils.computation import calculate_score
from src.services.llm_detailed_analysis import get_llm_analysis

router = APIRouter()


@router.post(
    "/analyze",
    summary="Analyze a Google Business Profile",
    response_model=AnalysisResponse,
)
def analyze_business(request: AnalysisRequest):
    """
    Performs a full analysis of a Google Business Profile.
    Provide EITHER a `query` or a `place_id`.
    """
    try:

        analyser = GBPAnalyzer(api_key=config.SERP_API_KEY)
    except ValueError as e:
        raise HTTPException(status_code=503, detail=f"Service Unavailable: {e}")

    logging.info(
        f"Received API request. Query: '{request.business_name}', Place ID: '{request.place_id}'"  # noqa
    )
    result = analyser.analyze(
        query=request.business_name,
        place_id=request.place_id,
        user_provided_address=request.address,
        user_provided_rating=request.star_rating,
        user_provided_reviews=request.review_count,
        user_provided_phone=request.phone_number,
    )

    if not result.get("success"):
        error_message = result.get("error", "An unknown error occurred.")
        if "No GBP found" in error_message:
            raise HTTPException(status_code=404, detail=error_message)

        raise HTTPException(status_code=500, detail=f"Analysis Error: {error_message}")

    business_data = result.get("data")
    score = calculate_score(business_data)
    detailed_analysis = get_llm_analysis(business_data, score, request.model_choice)

    return AnalysisResponse(
        score=score, data=business_data, detailed_analysis=detailed_analysis
    )
