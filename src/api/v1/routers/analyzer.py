import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks

from src.services.gbp_analyzer import GBPAnalyzer
from src.core.config import config
from src.api.v1.schemas.analyzer_schemas import AnalysisResponse, AnalysisRequest

router = APIRouter()


@router.post(
    "/analyze",
    summary="Analyze a Google Business Profile",
    response_model=AnalysisResponse,
)
def analyze_business(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """
    Performs a full analysis of a Google Business Profile.
    Provide EITHER a `query` or a `place_id`.
    """
    try:

        analyzer = GBPAnalyzer(api_key=config.SERP_API_KEY)
    except ValueError as e:
        raise HTTPException(status_code=503, detail=f"Service Unavailable: {e}")

    logging.info(
        f"Received API request. Query: '{request.business_name}', Place ID: '{request.place_id}'"  # noqa
    )

    job_result = analyzer.create_analysis_job(
        business_name=request.business_name,
        place_id=request.place_id,
        address=request.address,
        star_rating=request.star_rating,
        review_count=request.review_count,
        phone_number=request.phone_number,
    )

    if not job_result.get("success"):
        error_message = job_result.get("error", "Job creation failed.")
        raise HTTPException(status_code=500, detail=error_message)

    job_id = job_result.get("job_id")

    background_tasks.add_task(
        analyzer.run_background_analysis,
        job_id=job_result["job_id"],
        business_name=request.business_name,
        place_id=request.place_id,
        address=request.address,
        star_rating=request.star_rating,
        review_count=request.review_count,
        phone_number=request.phone_number,
    )

    logging.info(f"Started background analysis for job {job_id}")

    return AnalysisResponse(
        status="Pending", message="Analysis in progress", job_id=job_id
    )
