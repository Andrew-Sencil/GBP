from supabase import create_client, Client
from supabase.client import ClientOptions
from src.core.config import config
from typing import Optional
from datetime import datetime
import logging


url: str = config.SUPABASE_URL
key: str = config.SUPABASE_KEY

options = ClientOptions(
    schema="public",
    postgrest_client_timeout=10,
    storage_client_timeout=10,
)

supabase: Client = create_client(url, key, options=options)

current_datetime = datetime.now()

timestamp = current_datetime.timestamp()


def insert_data(table: str, data: dict) -> None:
    """Insert data into a Supabase table

    Args:
        table (str): The name of the table to insert into
        data (dict): The data to insert into the table, as a dictionary

    Returns:
        None
    """

    try:
        supabase.table(table).upsert([data], on_conflict="place_id").execute()
        logging.info(f"Successfully upserted data for place_id: {data.get('place_id')}")

    except Exception as e:
        logging.error(
            f"Supabase upsert failed for place_id {data.get('place_id')}: {e}"
        )


def insert_job_and_return_id(table: str, place_id: str, status: str) -> Optional[str]:
    """Insert a job into a Supabase table

    Args:
        table (str): The name of the table to insert into
        place_id (str): The place_id to insert into the table
        status (str): The status of the job (defaults to "Pending")

    Returns:
        Optional[str]: The generated job UUID, or None if insertion failed
    """

    try:
        result = (
            supabase.table(table)
            .insert({"place_id": place_id, "status": status, "created_at": timestamp})
            .execute()
        )
        logging.info(f"Successfully inserted job for place_id: {place_id}")

        if result.data and len(result.data) > 0:
            job_id = result.data[0].get("id")
            logging.info(
                f"Successfully inserted job with ID {job_id} for place_id: {place_id}"
            )
            return job_id

        else:
            logging.error(
                f"No data returned after job insertion for place_id: {place_id}"
            )
            return None

    except Exception as e:
        logging.error(f"Supabase insert job failed for place_id {place_id}: {e}")
