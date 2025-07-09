# GMB_analysis.py

import logging
from serpapi import GoogleSearch
from src.scrapers.photo_scraper import PhotoScraper
from typing import List, Dict

# --- Configuration ---
# In a real app, this would come from a config file or environment variables
# IMPORTANT: Remember to replace "YOUR_SERP_API_KEY" with your actual key.
SERP_API_KEY = "YOUR_SERP_API_KEY"

# Configure logging
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


class GmbAnalyzer:
    """
    A class to encapsulate the logic for fetching and analyzing a Google Business Profile.
    """

    def __init__(self, api_key: str):
        if not api_key or api_key == "YOUR_SERP_API_KEY":
            raise ValueError(
                "SERP_API_KEY is required. Please replace the placeholder value."
            )
        self.api_key = api_key
        # Safety limits to prevent excessive API usage
        self.pagination_page_limit = 5
        self.pagination_item_limit = 100
        self.photo_scraper = PhotoScraper()

    def _paginate_results(self, params: dict, results_key: str) -> list:
        """
        Generic private helper to paginate through SerpApi results.
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

            search = GoogleSearch(params)
            results = search.get_dict()

            if "error" in results:
                logging.error(
                    f"API Error for {params.get('engine')}: {results['error']}"
                )
                break

            page_items = results.get(results_key, [])
            if not page_items:
                break

            all_results.extend(page_items)
            logging.info(
                f"Fetched page {page_count}: {len(page_items)} {results_key}. Total: {len(all_results)}"
            )

            pagination = results.get("serpapi_pagination", {})
            if (
                "next" not in pagination
                or len(all_results) >= self.pagination_item_limit
            ):
                break

            params["next_page_token"] = pagination["next_page_token"]

        return all_results

    def fetch_all_posts(self, data_id: str, business_title: str) -> list:
        if not data_id:
            return []
        params = {
            "engine": "google_maps_posts",
            "q": business_title,
            "data_id": data_id,
            "api_key": self.api_key,
        }
        return self._paginate_results(params, "posts")

    def fetch_all_photos(self, data_id: str) -> list:
        if not data_id:
            return []
        params = {
            "engine": "google_maps_photos",
            "data_id": data_id,
            "api_key": self.api_key,
        }
        return self._paginate_results(params, "photos")

    def fetch_all_reviews(self, place_id: str) -> list:
        if not place_id:
            return []
        params = {
            "engine": "google_maps_reviews",
            "place_id": place_id,
            "api_key": self.api_key,
        }
        return self._paginate_results(params, "reviews")

    def _fetch_knowledge_graph_socials(self, query: str) -> list:
        logging.info("Falling back to Google Knowledge Panel for social links...")
        params = {
            "engine": "google",
            "q": query,
            "api_key": self.api_key,
        }
        results = GoogleSearch(params).get_dict()
        knowledge_graph = results.get("knowledge_graph", {})
        profiles = knowledge_graph.get("profiles", [])
        return [{"name": p.get("name"), "link": p.get("link")} for p in profiles]

    def _get_photo_counts(
        self, business_title: str, photo_attributions: List[Dict]
    ) -> dict:
        """
        Analyzes the high-quality attribution data provided by the Playwright scraper.
        """
        if not photo_attributions:
            return {"owner_photo_count": 0, "customer_photo_count": 0}
        owner_count, customer_count = 0, 0
        clean_business_title = business_title.lower().strip()
        for photo in photo_attributions:
            uploader_name = photo.get("uploader", "Unknown").lower().strip()
            # The uploader name in the gallery is often just "By [Business Name]"
            # This makes the comparison more robust
            if clean_business_title in uploader_name:
                owner_count += 1
            else:
                customer_count += 1
        logging.info(
            f"Final Tally (from Playwright): Owner: {owner_count}, Customer: {customer_count}"
        )
        return {
            "owner_photo_count": owner_count,
            "customer_photo_count": customer_count,
        }

    def analyze(self, query: str) -> dict:
        """
        Main analysis function. Returns structured data without printing.
        """
        logging.info(f"Starting analysis for query: '{query}'")
        analysis_result = {"query": query, "success": False, "error": None, "data": {}}

        # Step 1: Initial search to get IDs
        search_params = {
            "engine": "google_maps",
            "q": query,
            "type": "search",
            "api_key": self.api_key,
        }
        initial_results = GoogleSearch(search_params).get_dict()

        if initial_results.get("error"):
            analysis_result["error"] = initial_results["error"]
            return analysis_result

        first_result = (
            initial_results.get("place_results")
            or (initial_results.get("local_results", [])[0:1] or [None])[0]
        )
        if not first_result:
            analysis_result["error"] = "No GBP found for this query."
            return analysis_result

        place_id = first_result.get("place_id")
        data_id = first_result.get("data_id")
        business_title = first_result.get("title")

        # Step 2: Get rich details using place_id for reliability
        details_params = {
            "engine": "google_maps",
            "place_id": place_id,
            "api_key": self.api_key,
        }
        details_results = GoogleSearch(details_params).get_dict()
        place_data = details_results.get("place_results", {})

        if not place_data:
            analysis_result["error"] = "Could not fetch detailed place data."
            return analysis_result

        business_title = place_data.get("title", business_title)
        logging.info(f"Using official business title for analysis: '{business_title}'")

        all_posts = self.fetch_all_posts(data_id, business_title)

        search_url = f"https://www.google.com/maps/search/{query.replace(' ', '+')}"
        photo_attributions = self.photo_scraper.get_attributions_by_navigation(
            search_url, business_title
        )

        # Step 4: Assemble the final data structure
        result_data = analysis_result["data"]
        result_data["title"] = business_title
        result_data["place_id"] = place_id
        result_data["address"] = place_data.get("address")
        result_data["phone"] = place_data.get("phone")
        result_data["website"] = place_data.get("website")
        result_data["rating"] = place_data.get("rating")
        result_data["reviews_count"] = place_data.get("reviews")

        # Social links with fallback
        social_links = place_data.get("links", [])
        if not social_links:
            social_links = self._fetch_knowledge_graph_socials(query)
        result_data["social_links"] = social_links

        # Posts
        result_data["posts_count"] = len(all_posts)
        result_data["most_recent_post_date"] = (
            all_posts[0].get("date") if all_posts else None
        )

        # Photos (Total and Classified)
        result_data["photo_counts_by_uploader"] = self._get_photo_counts(
            business_title, photo_attributions
        )
        result_data["total_photos_analyzed"] = len(photo_attributions)

        analysis_result["success"] = True
        return analysis_result
