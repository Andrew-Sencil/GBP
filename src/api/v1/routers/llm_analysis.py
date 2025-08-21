import logging
from fastapi import APIRouter

from src.api.v1.schemas.analyzer_schemas import (
    DetailedAnalysisRequest,
    DetailedAnalysisResponse,
)
from src.services.llm_detailed_analysis import get_llm_analysis

router = APIRouter()


@router.post(
    "/detailed_analysis",
    summary="Generate a detailed LLM analysis from business data",
    response_model=DetailedAnalysisResponse,
)
def generate_detailed_analysis(request: DetailedAnalysisRequest):
    """
    Takes the score and data from the primary `/analyze` endpoint and
    generates a detailed, human-readable analysis using a generative AI model.
    """

    logging.info(
        f"Received request for detailed analysis for business: {request.data.get('title')}"  # noqa
    )

    analysis_text = get_llm_analysis(
        business_data=request.data,
        score=request.score,
        model_choice=request.model_choice,
    )

    return DetailedAnalysisResponse(detailed_analysis=analysis_text)
