import logging
import traceback
from concurrent.futures import (
    ProcessPoolExecutor,
    ThreadPoolExecutor,
)
from typing import Optional

from src.utils.analyzer_helper import (
    _safe_get_nested_value,
    _fetch_all_posts,
    _fetch_all_reviews,
    _get_social_links,
    _run_photo_scraper,
    _filter_reviews_by_recency,
    _filter_posts_by_recency,
    _get_photo_counts,
    _safe_api_call,
)
from src.utils.computation import calculate_score
from src.services.supabase import supabase, insert_data
from src.services.job_status import update_job_status
from src.services.llm_detailed_analysis import get_llm_analysis
from src.core.config import config

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


class GBPAnalyzer:
    """
    Enhanced version with comprehensive error handling and graceful degradation
    to prevent crashes when businesses have incomplete information.
    """

    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("An API key is required to initialize the GmbAnalyzer.")

        self.api_key = api_key

    def create_analysis_job(
        self,
        business_name: Optional[str] = None,
        place_id: Optional[str] = None,
        address: Optional[str] = None,
        star_rating: Optional[float] = None,
        review_count: Optional[int] = None,
        phone_number: Optional[str] = None,
    ) -> dict:
        """
        Create a new analysis job with real place_id.
        This method resolves the place_id first, then creates the job.

        Returns:
            dict: {"success": bool,
            "job_id": str,
            "status": str,
            "message": str,
            "place_id": str}
        """

        try:
            resolved_place_id = place_id

            if not resolved_place_id:
                if not business_name:
                    return {
                        "success": False,
                        "error": "Either business_name or place_id must be provided.",
                    }

                search_params = {
                    "engine": "google_maps",
                    "q": business_name,
                    "type": "search",
                    "api_key": self.api_key,
                }

                initial_results = _safe_api_call(search_params, "initial search")

                if not initial_results:
                    return {
                        "success": False,
                        "error": f"No results for business_name: '{business_name}'",
                    }

                initial_search_result = (
                    initial_results.get("place_results")
                    or (initial_results.get("local_results", [])[0:1] or [None])[0]
                )

                if not initial_search_result:
                    return {
                        "success": False,
                        "error": f"No GBP found for business_name: '{business_name}'",
                    }

                resolved_place_id = initial_search_result.get("place_id")

                if not resolved_place_id:
                    return {
                        "success": False,
                        "error": "Could not extract place_id from search results.",
                    }

            placeholder_data = {
                "place_id": resolved_place_id,
                "title": business_name or "Analysis in progress...",
                "address": address or "",
                "phone": phone_number or "",
                "rating": star_rating or 0.0,
                "reviews_count": review_count or 0,
                "score": 0,
                "website": "",
                "description": "Analysis in progress...",
                "social_links": [],
                "recent_reviews": 0,
                "posts_count": 0,
                "photo_counts_by_uploader": {},
                "total_photos_analyzed": 0,
                "attributes_count": 0,
            }

            supabase.table("GBP-results").upsert(
                [placeholder_data], on_conflict="place_id"
            ).execute()

            status = "Pending"
            job_data = {"place_id": resolved_place_id, "status": status}
            result = supabase.table("jobs").insert(job_data).execute()

            if result.data and len(result.data) > 0:
                job_id = result.data[0].get("id")
                logging.info(
                    f"Created analysis job {job_id} for place_id: {resolved_place_id}"
                )

                return {
                    "success": True,
                    "job_id": str(job_id),
                    "status": status,
                    "message": "Analysis job created successfully",
                    "place_id": resolved_place_id,
                }
            else:
                return {"success": False, "error": "Failed to create job record"}

        except Exception as e:
            logging.error(f"Failed to create analysis job: {e}")
            return {"success": False, "error": f"Job creation failed: {str(e)}"}

    def run_background_analysis(
        self,
        job_id: str,
        business_name: Optional[str] = None,
        place_id: Optional[str] = None,
        address: Optional[str] = None,
        star_rating: Optional[float] = None,
        review_count: Optional[int] = None,
        phone_number: Optional[str] = None,
    ) -> None:
        """
        Run the complete analysis in the background and update job status.
        This method is designed to be called as a background task.
        """

        try:
            update_job_status(job_id, "Analysis Started")

            update_job_status(job_id, "Analyzing")

            result = self.analyze(
                query=business_name,
                place_id=place_id,
                user_provided_address=address,
                user_provided_rating=star_rating,
                user_provided_reviews=review_count,
                user_provided_phone=phone_number,
            )

            if not result or not result.get("success"):
                error_message = (
                    result.get("error", "Analysis failed.")
                    if result
                    else "Analysis returned no result"
                )
                logging.error(f"Analysis failed for job {job_id}: {error_message}")
                update_job_status(job_id, "Analysis Failed")

                return

            business_data = result.get("data")
            if not business_data:
                logging.error(f"No business data returned for job {job_id}")
                update_job_status(job_id, "Analysis Failed")
                return

            real_place_id = business_data.get("place_id")
            if real_place_id:
                try:
                    supabase.table("jobs").update({"place_id": real_place_id}).eq(
                        "id", job_id
                    ).execute()
                    logging.info(f"Updated job {job_id} place_id to {real_place_id}")

                except Exception as e:
                    logging.warning(f"Failed to update job place_id: {e}")

            update_job_status(job_id, "Writing the Analysis")

            try:
                insert_data("GBP-results", business_data)
                logging.info(f"Successfully saved business data for job {job_id}")

                update_job_status(job_id, "Analysis Finished")

            except Exception as e:
                logging.error(f"Failed to save business data for job {job_id}: {e}")
                update_job_status(job_id, "Analysis Failed")

        except Exception as e:
            logging.error(f"Background analysis failed for job {job_id}: {e}")
            update_job_status(job_id, "Analysis Failed")

    def analyze(
        self,
        query: Optional[str] = None,
        place_id: Optional[str] = None,
        user_provided_address: Optional[str] = None,
        user_provided_rating: Optional[float] = None,
        user_provided_reviews: Optional[int] = None,
        user_provided_phone: Optional[str] = None,
    ) -> dict:
        try:
            # --- Initial Search and Data Fetching (remains the same) ---
            if not place_id:
                if not query:
                    return {
                        "success": False,
                        "error": "Query or place_id must be provided.",
                    }
                search_params = {
                    "engine": "google_maps",
                    "q": query,
                    "type": "search",
                    "api_key": self.api_key,
                }
                initial_results = _safe_api_call(search_params, "initial search")
                if not initial_results:
                    return {
                        "success": False,
                        "error": f"No results for query: '{query}'",
                    }
                initial_search_result = (
                    initial_results.get("place_results")
                    or (initial_results.get("local_results", [])[0:1] or [None])[0]
                )
                if not initial_search_result:
                    return {
                        "success": False,
                        "error": f"No GBP found for query: '{query}'",
                    }
                place_id = initial_search_result.get("place_id")
                if not place_id:
                    return {"success": False, "error": "Could not extract place_id."}
            else:
                initial_search_result = None

            details_params = {
                "engine": "google_maps",
                "place_id": place_id,
                "api_key": self.api_key,
            }
            details_results = _safe_api_call(details_params, "place details")
            place_data = details_results.get("place_results", {})
            if not place_data:
                return {
                    "success": False,
                    "error": f"Could not fetch data for place_id: {place_id}",
                }

            # --- Safe Data Extraction (calls are now to standalone functions) ---
            business_title = _safe_get_nested_value(
                place_data, "title", "Unknown Business"
            )
            address = user_provided_address or _safe_get_nested_value(
                place_data, "address", "Unknown Address"
            )

            # --- Concurrent Operations ---
            with (
                ThreadPoolExecutor(max_workers=2) as api_executor,
                ProcessPoolExecutor(max_workers=1) as scraper_executor,
            ):
                # Calls are updated to pass self.api_key where needed
                review_future = api_executor.submit(
                    _fetch_all_reviews, place_id, self.api_key
                )
                social_future = api_executor.submit(
                    _get_social_links, place_data, business_title, address, self.api_key
                )
                photo_future = scraper_executor.submit(
                    _run_photo_scraper, place_id, business_title
                )

                all_reviews = review_future.result(timeout=60)
                social_links = social_future.result(timeout=30)
                photo_attributions = photo_future.result(timeout=320)

            # --- Post Extraction ---
            data_id = _safe_get_nested_value(place_data, "data_id")
            all_posts = _fetch_all_posts(data_id, business_title, self.api_key)
            recent_posts_count = _filter_posts_by_recency(all_posts)
            extensions_data = _safe_get_nested_value(place_data, "extensions", [])

            attributes_list = []
            if extensions_data and isinstance(extensions_data, list):
                for item in extensions_data:
                    if isinstance(item, dict):
                        for attribute_group in item.values():
                            if isinstance(attribute_group, list):
                                attributes_list.extend(attribute_group)

            result_data = {
                "title": business_title,
                "place_id": place_id,
                "address": address,
                "phone": user_provided_phone
                or _safe_get_nested_value(place_data, "phone"),
                "website": _safe_get_nested_value(place_data, "website"),
                "description": _safe_get_nested_value(place_data, "description"),
                "attributes_count": len(attributes_list),
                "rating": user_provided_rating
                or _safe_get_nested_value(place_data, "rating", 0.0),
                "reviews_count": user_provided_reviews
                or _safe_get_nested_value(place_data, "reviews", 0),
                "social_links": social_links,
                "recent_reviews_in_last_month_count": len(
                    _filter_reviews_by_recency(all_reviews)
                ),
                "posts_count": recent_posts_count,
                "photo_counts_by_uploader": _get_photo_counts(
                    business_title, photo_attributions
                ),
                "total_photos_analyzed": len(photo_attributions),
            }

            score = calculate_score(result_data)

            # --- Final Assembly ---
            output = {
                "title": business_title,
                "place_id": place_id,
                "address": address,
                "phone": user_provided_phone
                or _safe_get_nested_value(place_data, "phone"),
                "website": _safe_get_nested_value(place_data, "website"),
                "description": _safe_get_nested_value(place_data, "description"),
                "attributes_count": len(attributes_list),
                "rating": user_provided_rating
                or _safe_get_nested_value(place_data, "rating", 0.0),
                "reviews_count": user_provided_reviews
                or _safe_get_nested_value(place_data, "reviews", 0),
                "social_links": social_links,
                "recent_reviews": len(_filter_reviews_by_recency(all_reviews)),
                "posts_count": recent_posts_count,
                "photo_counts_by_uploader": _get_photo_counts(
                    business_title, photo_attributions
                ),
                "total_photos_analyzed": len(photo_attributions),
                "score": score,
            }

            llm_analysis = get_llm_analysis(
                business_data=output, model_choice=config.GEMINI_MODEL_FLASH
            )

            final_output = {
                "title": business_title,
                "place_id": place_id,
                "address": address,
                "phone": user_provided_phone
                or _safe_get_nested_value(place_data, "phone"),
                "website": _safe_get_nested_value(place_data, "website"),
                "description": _safe_get_nested_value(place_data, "description"),
                "attributes_count": len(attributes_list),
                "rating": user_provided_rating
                or _safe_get_nested_value(place_data, "rating", 0.0),
                "reviews_count": user_provided_reviews
                or _safe_get_nested_value(place_data, "reviews", 0),
                "social_links": social_links,
                "recent_reviews": len(_filter_reviews_by_recency(all_reviews)),
                "posts_count": recent_posts_count,
                "photo_counts_by_uploader": _get_photo_counts(
                    business_title, photo_attributions
                ),
                "total_photos_analyzed": len(photo_attributions),
                "score": score,
                "llm_analysis": llm_analysis,
            }

            return {"success": True, "data": final_output}

        except Exception as e:
            logging.error(
                f"Critical error in analyze method: {e}\n{traceback.format_exc()}"
            )
            return {"success": False, "error": f"Analysis failed: {str(e)}"}

    def website_socials(
        self, query: Optional[str] = None, place_id: Optional[str] = None
    ) -> dict:
        """
        Enhanced analysis with comprehensive error handling and safe defaults.
        """
        default_result = {
            "success": False,
            "data": {"website": None, "social_links": []},
        }

        try:
            # --- Initial Search and Data Fetching (This part is correct) ---
            current_place_id = place_id
            initial_search_result = None

            if not current_place_id:
                if not query:
                    return {
                        "success": False,
                        "error": "Internal Error: Either query or place_id must be provided.",  # noqa
                    }

                search_params = {
                    "engine": "google_maps",
                    "q": query,
                    "type": "search",
                    "api_key": self.api_key,
                }
                initial_results = _safe_api_call(search_params, "initial search")
                if not initial_results:
                    return {
                        "success": False,
                        "error": f"No results found for query: '{query}'",
                    }

                initial_search_result = (
                    initial_results.get("place_results")
                    or (initial_results.get("local_results", [])[0:1] or [None])[0]
                )
                if not initial_search_result:
                    return {
                        "success": False,
                        "error": f"No GBP found for query: '{query}'",
                    }

                current_place_id = initial_search_result.get("place_id")
                if not current_place_id:
                    return {
                        "success": False,
                        "error": "Could not extract place_id from search results.",
                    }

            details_params = {
                "engine": "google_maps",
                "place_id": current_place_id,
                "api_key": self.api_key,
            }
            details_results = _safe_api_call(details_params, "place details")
            place_data = details_results.get("place_results", {})
            if not place_data:
                return {
                    "success": False,
                    "error": f"Could not fetch detailed data for place_id: {current_place_id}",  # noqa
                }

            business_title = _safe_get_nested_value(
                place_data, "title", "Unknown Business"
            )

            result_data = {
                "website": _safe_get_nested_value(place_data, "website"),
                "social_links": [],
            }
            address = _safe_get_nested_value(place_data, "address")

            # --- Concurrent Operations ---
            social_links = []
            try:
                with ThreadPoolExecutor(max_workers=1) as api_executor:
                    futures = {}
                    try:
                        # --- THE FIX IS HERE ---
                        # We must pass the api_key to the helper function,
                        # as it now requires it.
                        futures["social"] = api_executor.submit(
                            _get_social_links,
                            place_data,
                            business_title,
                            address,
                            self.api_key,
                        )
                    except Exception as e:
                        logging.error(f"Error submitting social links task: {e}")

                    if "social" in futures:
                        try:
                            social_links = futures["social"].result(timeout=30)
                        except Exception as e:
                            logging.error(f"Social links collection failed: {e}")
                            social_links = []
            except Exception as e:
                logging.error(f"Error during concurrent operations: {e}")

            result_data["social_links"] = social_links if social_links else []

            return {"success": True, "data": result_data}

        except Exception as e:
            logging.error(f"Critical error in website_socials method: {e}")
            logging.error(f"Traceback: {traceback.format_exc()}")
            return {
                "success": False,
                "error": f"Analysis failed: {str(e)}",
                "data": default_result["data"],
            }
