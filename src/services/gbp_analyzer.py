import logging
import traceback
from concurrent.futures import (
    ProcessPoolExecutor,
    ThreadPoolExecutor,
    TimeoutError as FutureTimeoutError,
)
from serpapi import GoogleSearch
from src.scrapers.uploader_scraper_process import run_photo_scraper_process
from typing import List, Dict, Optional, Union

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
        self.pagination_page_limit = 10
        self.pagination_item_limit = 200

    def _safe_api_call(self, params: dict, description: str) -> dict:
        """
        Safely make API calls with error handling and logging.
        """
        try:
            search = GoogleSearch(params)
            results = search.get_dict()

            if "error" in results:
                logging.error(f"API Error for {description}: {results['error']}")
                return {}

            return results
        except Exception as e:
            logging.error(f"Exception during {description}: {e}")
            return {}

    def _paginate_results(self, params: dict, results_key: str) -> list:
        """
        Enhanced pagination with better error handling.
        """
        all_results = []
        page_count = 0

        while True:
            page_count += 1
            if page_count > self.pagination_page_limit:
                logging.warning(
                    f"Reached page limit of {self.pagination_page_limit} for {params.get('engine')}"
                )
                break

            # Use safe API call
            results = self._safe_api_call(
                params, f"{params.get('engine')} page {page_count}"
            )
            if not results:
                break

            page_items = results.get(results_key, [])
            if not page_items:
                break

            all_results.extend(page_items)
            logging.info(
                f"Retrieved {len(page_items)} items from page {page_count} for {params.get('engine')}"
            )

            pagination = results.get("serpapi_pagination", {})
            if "next_page_token" in pagination:
                params["next_page_token"] = pagination["next_page_token"]
            else:
                break

        return all_results

    def _filter_reviews_by_recency(self, all_reviews: List[Dict]) -> List[Dict]:
        """
        Enhanced review filtering with better error handling.
        """
        if not all_reviews:
            logging.info("No reviews to filter")
            return []

        logging.info(
            f"Filtering {len(all_reviews)} reviews to find those from the last month..."
        )
        recent_reviews = []

        VALID_MONTH_STRINGS = {
            "now",
            "today",
            "a week ago",
            "2 weeks ago",
            "3 weeks ago",
            "4 weeks ago",
            "a month ago",
        }

        for review in all_reviews:
            try:
                date_string = review.get("date", "").lower()
                if not date_string:
                    continue
                if date_string in VALID_MONTH_STRINGS or "day" in date_string:
                    recent_reviews.append(review)
            except Exception as e:
                logging.warning(f"Error processing review date: {e}")
                continue

        logging.info(f"Found {len(recent_reviews)} recent reviews.")
        return recent_reviews

    def _fetch_all_posts(self, data_id: str, business_title: str) -> list:
        """
        Enhanced posts fetching with better error handling.
        """
        if not data_id:
            logging.warning("No data_id provided for posts fetching")
            return []

        if not business_title:
            logging.warning("No business_title provided for posts fetching")
            return []

        try:
            params = {
                "engine": "google_maps_posts",
                "q": business_title,
                "data_id": data_id,
                "api_key": self.api_key,
            }

            return self._paginate_results(params, "posts")
        except Exception as e:
            logging.error(f"Error fetching posts: {e}")
            return []

    def _fetch_knowledge_graph_socials(self, query: str) -> list:
        """
        Enhanced social media fetching with better error handling.
        """
        if not query:
            logging.warning("No query provided for social media fetching")
            return []

        try:
            params = {
                "engine": "google",
                "q": query,
                "api_key": self.api_key,
            }

            results = self._safe_api_call(params, "knowledge graph social links")
            if not results:
                return []

            knowledge_graph = results.get("knowledge_graph", {})
            profiles = knowledge_graph.get("profiles", [])

            social_links = []
            for profile in profiles:
                try:
                    name = profile.get("name")
                    link = profile.get("link")
                    if name and link:
                        social_links.append({"name": name, "link": link})
                except Exception as e:
                    logging.warning(f"Error processing social profile: {e}")
                    continue

            return social_links
        except Exception as e:
            logging.error(f"Error fetching social links: {e}")
            return []

    def _fetch_all_reviews(self, place_id: str) -> list:
        """
        Enhanced review fetching with better error handling.
        """
        if not place_id:
            logging.warning("No place_id provided for reviews fetching")
            return []

        try:
            params = {
                "engine": "google_maps_reviews",
                "place_id": place_id,
                "api_key": self.api_key,
                "sort_by": "newestFirst",
            }

            return self._paginate_results(params, "reviews")
        except Exception as e:
            logging.error(f"Error fetching reviews: {e}")
            return []

    def _get_photo_counts(
        self, business_title: str, photo_attributions: List[Dict]
    ) -> dict:
        """
        Enhanced photo counting with better error handling.
        """
        default_counts = {"owner_photo_count": 0, "customer_photo_count": 0}

        if not photo_attributions:
            logging.info("No photo attributions provided")
            return default_counts

        if not business_title:
            logging.warning("No business title provided for photo counting")
            return default_counts

        try:
            owner_count, customer_count = 0, 0
            clean_business_title = business_title.lower().strip()

            for photo in photo_attributions:
                try:
                    uploader_name = photo.get("uploader", "Unknown").lower().strip()
                    if (
                        uploader_name == "owner"
                        or clean_business_title in uploader_name
                    ):
                        owner_count += 1
                    else:
                        customer_count += 1
                except Exception as e:
                    logging.warning(f"Error processing photo attribution: {e}")
                    customer_count += 1  # Default to customer if unclear

            logging.info(
                f"Final Tally (from Playwright): Owner: {owner_count}, Customer: {customer_count}"
            )

            return {
                "owner_photo_count": owner_count,
                "customer_photo_count": customer_count,
            }
        except Exception as e:
            logging.error(f"Error calculating photo counts: {e}")
            return default_counts

    def _get_social_links(self, place_data: dict, query: str) -> list:
        """
        Enhanced social links extraction with better error handling.
        """
        try:
            # Try to get links from place data first
            links = place_data.get("links", []) if place_data else []

            # Validate and clean existing links
            valid_links = []
            for link in links:
                try:
                    if isinstance(link, dict) and link.get("name") and link.get("link"):
                        valid_links.append(link)
                except Exception as e:
                    logging.warning(f"Invalid link format: {e}")
                    continue

            # If no valid links and we have a query, try knowledge graph
            if not valid_links and query:
                try:
                    kg_links = self._fetch_knowledge_graph_socials(query)
                    valid_links.extend(kg_links)
                except Exception as e:
                    logging.error(f"Error fetching knowledge graph socials: {e}")

            return valid_links
        except Exception as e:
            logging.error(f"Error getting social links: {e}")
            return []

    def _run_photo_scraper(self, search_url: str, business_title: str) -> list:
        """
        Enhanced photo scraper with better error handling and timeout management.
        """
        if not search_url or not business_title:
            logging.warning("Missing search_url or business_title for photo scraping")
            return []

        try:
            with ProcessPoolExecutor(max_workers=1) as executor:
                future = executor.submit(
                    run_photo_scraper_process, search_url, business_title
                )
                try:
                    result = future.result(timeout=300)  # 5 minute timeout
                    return result if result else []
                except FutureTimeoutError:
                    logging.error("Photo scraping process timed out after 5 minutes")
                    return []
                except Exception as e:
                    logging.error(f"Photo scraping process failed: {e}")
                    return []
        except Exception as e:
            logging.error(f"Error setting up photo scraper: {e}")
            return []

    def _safe_get_nested_value(self, data: dict, key: str, default=None):
        """
        Safely get nested values from dictionary with fallback.
        """
        try:
            return data.get(key, default) if data else default
        except Exception as e:
            logging.warning(f"Error accessing key '{key}': {e}")
            return default

    def analyze(
        self, query: Optional[str] = None, place_id: Optional[str] = None
    ) -> dict:
        """
        Enhanced analysis with comprehensive error handling and safe defaults.
        """
        # Initialize default result structure
        default_result = {
            "success": False,
            "data": {
                "title": "Unknown Business",
                "place_id": place_id or "unknown",
                "address": None,
                "phone": None,
                "website": None,
                "rating": 0.0,
                "reviews_count": 0,
                "social_links": [],
                "recent_reviews_in_last_month_count": 0,
                "posts_count": 0,
                "photo_counts_by_uploader": {
                    "owner_photo_count": 0,
                    "customer_photo_count": 0,
                },
                "total_photos_analyzed": 0,
            },
        }

        try:
            current_place_id = place_id
            initial_search_result = None

            # Handle place_id resolution
            if not current_place_id:
                if not query:
                    return {
                        "success": False,
                        "error": "Internal Error: Either query or place_id must be provided.",
                    }

                try:
                    search_params = {
                        "engine": "google_maps",
                        "q": query,
                        "type": "search",
                        "api_key": self.api_key,
                    }

                    initial_results = self._safe_api_call(
                        search_params, "initial search"
                    )
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
                except Exception as e:
                    logging.error(f"Error during initial search: {e}")
                    return {"success": False, "error": f"Search failed: {str(e)}"}

            else:
                logging.info(
                    f"Analyzing directly with provided place_id: '{current_place_id}'"
                )

            # Fetch detailed place data
            try:
                details_params = {
                    "engine": "google_maps",
                    "place_id": current_place_id,
                    "api_key": self.api_key,
                }
                details_results = self._safe_api_call(details_params, "place details")
                place_data = details_results.get("place_results", {})

                if not place_data:
                    return {
                        "success": False,
                        "error": f"Could not fetch detailed data for place_id: {current_place_id}",
                    }
            except Exception as e:
                logging.error(f"Error fetching place details: {e}")
                return {
                    "success": False,
                    "error": f"Failed to fetch place details: {str(e)}",
                }

            # Extract basic info with safe defaults
            data_id = self._safe_get_nested_value(place_data, "data_id") or (
                self._safe_get_nested_value(initial_search_result, "data_id")
                if initial_search_result
                else None
            )
            business_title = self._safe_get_nested_value(
                place_data, "title", "Unknown Business"
            )

            # Initialize result data with safe values
            result_data = {
                "title": business_title,
                "place_id": current_place_id,
                "address": self._safe_get_nested_value(place_data, "address"),
                "phone": self._safe_get_nested_value(place_data, "phone"),
                "website": self._safe_get_nested_value(place_data, "website"),
                "rating": self._safe_get_nested_value(place_data, "rating", 0.0),
                "reviews_count": self._safe_get_nested_value(place_data, "reviews", 0),
                "social_links": [],
                "recent_reviews_in_last_month_count": 0,
                "posts_count": 0,
                "photo_counts_by_uploader": {
                    "owner_photo_count": 0,
                    "customer_photo_count": 0,
                },
                "total_photos_analyzed": 0,
            }

            # Build search URL for photo scraping
            search_url = (
                f"https://www.google.com/maps/search/{business_title.replace(' ', '+')}"
            )

            # Execute concurrent operations with error handling
            all_reviews = []
            social_links = []
            all_posts = []
            photo_attributions = []

            try:
                with (
                    ThreadPoolExecutor(max_workers=2) as api_executor,
                    ProcessPoolExecutor(max_workers=1) as scraper_executor,
                ):
                    # Submit all futures
                    futures = {}

                    try:
                        futures["reviews"] = api_executor.submit(
                            self._fetch_all_reviews, current_place_id
                        )
                    except Exception as e:
                        logging.error(f"Error submitting reviews task: {e}")

                    try:
                        futures["social"] = api_executor.submit(
                            self._get_social_links, place_data, business_title
                        )
                    except Exception as e:
                        logging.error(f"Error submitting social links task: {e}")

                    try:
                        futures["photos"] = scraper_executor.submit(
                            self._run_photo_scraper, search_url, business_title
                        )
                    except Exception as e:
                        logging.error(f"Error submitting photo scraper task: {e}")

                    # Collect results with individual error handling
                    if "reviews" in futures:
                        try:
                            all_reviews = futures["reviews"].result(timeout=60)
                        except Exception as e:
                            logging.error(f"Reviews collection failed: {e}")
                            all_reviews = []

                    if "social" in futures:
                        try:
                            social_links = futures["social"].result(timeout=30)
                        except Exception as e:
                            logging.error(f"Social links collection failed: {e}")
                            social_links = []

                    if "photos" in futures:
                        try:
                            photo_attributions = futures["photos"].result(timeout=320)
                        except Exception as e:
                            logging.error(f"Photo attribution collection failed: {e}")
                            photo_attributions = []

            except Exception as e:
                logging.error(f"Error during concurrent operations: {e}")

            # Handle posts extraction
            try:
                updates = self._safe_get_nested_value(place_data, "updates", {})
                if updates:
                    all_posts = self._safe_get_nested_value(updates, "posts", [])

                if not all_posts and initial_search_result:
                    updates_from_initial = self._safe_get_nested_value(
                        initial_search_result, "updates", {}
                    )
                    if updates_from_initial:
                        all_posts = self._safe_get_nested_value(
                            updates_from_initial, "posts", []
                        )

                if not all_posts and data_id:
                    all_posts = self._fetch_all_posts(data_id, business_title)
            except Exception as e:
                logging.error(f"Error extracting posts: {e}")
                all_posts = []

            # Process results safely
            try:
                recent_reviews_filtered = self._filter_reviews_by_recency(all_reviews)
                result_data["recent_reviews_in_last_month_count"] = len(
                    recent_reviews_filtered
                )
            except Exception as e:
                logging.error(f"Error filtering recent reviews: {e}")

            try:
                result_data["social_links"] = social_links if social_links else []
            except Exception as e:
                logging.error(f"Error setting social links: {e}")

            try:
                result_data["posts_count"] = len(all_posts) if all_posts else 0
            except Exception as e:
                logging.error(f"Error counting posts: {e}")

            try:
                photo_counts = self._get_photo_counts(
                    business_title, photo_attributions
                )
                result_data["photo_counts_by_uploader"] = photo_counts
                result_data["total_photos_analyzed"] = (
                    len(photo_attributions) if photo_attributions else 0
                )
            except Exception as e:
                logging.error(f"Error processing photo counts: {e}")

            return {
                "success": True,
                "data": result_data,
            }

        except Exception as e:
            logging.error(f"Critical error in analyze method: {e}")
            logging.error(f"Traceback: {traceback.format_exc()}")
            return {
                "success": False,
                "error": f"Analysis failed: {str(e)}",
                "data": default_result["data"],
            }
