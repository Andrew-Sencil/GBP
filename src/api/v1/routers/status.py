import logging
from fastapi import APIRouter, HTTPException

from src.api.v1.schemas.analyzer_schemas import (
    JobStatusUpdateRequest,
    JobstatusResponse,
)
from src.services.job_status import check_job_status, update_job_status

router = APIRouter()


@router.get(
    "/check-status/{job_id}",
    summary="Checks the status of a job",
    response_model=JobstatusResponse,
)
def get_job_status(job_id: str):
    """
    Check the status of an analysis job.
    Returns: Pending, Analysis Started, Analyzing, Writing the Analysis,
    Analysis Finished, or Analysis Failed
    """

    logging.info(f"Checking status for the job: {job_id}")

    try:
        result = check_job_status(job_id)

        status_message = {
            "Analysis Finished": "Analysis completed successfully",
            "Analyzing": "Analysis is currently in progress",
            "Analysis Started": "Analysis has been started",
            "Writing the Analysis": "Analysis is being finalized",
            "Pending": "Analysis is pending to start",
            "Analysis Failed": "Analysis failed due to an error",
            "not_found": "Job not found",
        }

        status = result.get("status", "Analysis Failed")
        message = status_message.get(status, "Unknown status")

        if status == "not_found":
            raise HTTPException(status_code=404, detail="Job not found")

        if status == "Analysis Finished" and result.get("data"):
            business_data = result.get("data", {})
            business_name = business_data.get("title", "Unknown Business Name")
            score = business_data.get("score", "N/A")
            message = f"Analysis completed for {business_name}. Overall score: {score}"

        return JobstatusResponse(
            status=status,
            job_id=result.get("job_id", job_id),
            message=message,
            place_id=result.get("place_id", ""),
            data=result.get("data"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error checking job status: {e}")

        raise HTTPException(status_code=500, detail="Failed to check job status")


@router.put(
    "/update-status/{job_id}",
    summary="Updates the status of a job",
    response_model=JobstatusResponse,
)
def update_status(job_id: str, request: JobStatusUpdateRequest):
    """
    Update the status of an analysis job.
    Allowed statuses: Pending, Analysis Started, Analyzing, Writing the Analysis,
                      Analysis Finished, Analysis Failed
    """

    logging.info(f"Updating status for job {job_id} to: {request.status}")

    allowed_statuses = [
        "Pending",
        "Analysis Started",
        "Analyzing",
        "Writing the Analysis",
        "Analysis Finished",
        "Analysis Failed",
    ]

    if request.status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Allowed statuses: {', '.join(allowed_statuses)}",
        )

    try:
        success = update_job_status(job_id, request.status)

        if not success:
            raise HTTPException(
                status_code=404, detail="Job not found or update failed"
            )

        return get_job_status(job_id)

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error updating job status: {e}")
        raise HTTPException(status_code=500, detail="Failed to update job status")
