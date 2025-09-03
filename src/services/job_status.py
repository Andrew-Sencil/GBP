import logging
from typing import Dict, Any
from supabase import create_client, Client
from supabase.client import ClientOptions
from src.core.config import config

url: str = config.SUPABASE_URL
key: str = config.SUPABASE_KEY

options = ClientOptions(
    schema="public",
    postgrest_client_timeout=10,
    storage_client_timeout=10,
)

supabase: Client = create_client(url, key, options=options)


def check_job_status(job_id: str) -> Dict[str, Any]:
    """
    Check the status of a job by its UUID

    Args:
        job_id (str): The job UUID to check

    Returns:
        Dict[str, str]: Dictionary containing status, job_id, and place_id
    """

    logging.info(f"Checking status for job: {job_id}")

    try:
        job_result = supabase.table("jobs").select("*").eq("id", job_id).execute()

        if not job_result.data or len(job_result.data) == 0:
            logging.warning(f"Job {job_id} not found")

            return {"status": "not_found", "job_id": job_id, "place_id": ""}

        job = job_result.data[0]
        place_id = job.get("place_id")
        current_status = job.get("status", "Pending")

        business_data = None
        if current_status == "Analysis Finished" and place_id:
            try:
                data_result = (
                    supabase.table("GBP-results")
                    .select("*")
                    .eq("place_id", place_id)
                    .execute()
                )

                if data_result.data and len(data_result.data) > 0:
                    business_data = data_result.data[0]
                    logging.info(f"Retrieved business data for job {job_id}")
                else:
                    logging.warning(f"No business data found for job {job_id}")

            except Exception as e:
                logging.error(f"Failed to retrieve business data for job {job_id}: {e}")

        return {
            "status": current_status,
            "job_id": job_id,
            "place_id": place_id,
            "data": business_data,
        }

    except Exception as e:
        logging.error(f"Failed to check job status for {job_id}: {e}")

        return {"status": "Analysis Failed", "job_id": job_id, "place_id": ""}


def update_job_status(job_id: str, status: str) -> bool:
    """
    Update the status of a job

    Args:
        job_id (str): The job UUID to update
        status (str): The new status

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        result = (
            supabase.table("jobs").update({"status": status}).eq("id", job_id).execute()
        )

        if result.data and len(result.data) > 0:
            logging.info(f"Update job {job_id} status to {status}")

            return True
        else:
            logging.warning(f"No job found with ID {job_id} to update")

            return False

    except Exception as e:
        logging.error(f"Failed to update job status for {job_id} status: {e}")
