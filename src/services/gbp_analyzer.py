import logging

from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from serpapi import GoogleSearch
from src.scrapers.uploader_scraper_process import run_photo_scraper_process
from typing import List, Dict, Optional

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


class GBPAnalyzer:
    """
    A class to encapsulate the logic for fetching
    and analyzing a Google Business Profile.
    """

    def __init__(self, api_key: str):

        if not api_key:
            raise ValueError("An API key is required to initialize the GmbAnalyzer.")

        self.api_key = api_key
        self.pagination_page_limit = 10
        self.pagination_item_limit = 200

    def _paginate_results(self, params: dict, results_key: str) -> list:

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
                f"Retrieved {len(page_items)} items from page {page_count} for {params.get('engine')}"
            )

            pagination = results.get("serpapi_pagination", {})

            if "next_page_token" in pagination:
                params["next_page_token"] = pagination["next_page_token"]
            else:
                break

        return all_results

    def _filter_reviews_by_recency(self, all_reviews: List[Dict]) -> List[Dict]:

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
            date_string = review.get("date", "").lower()
            if not date_string:
                continue
            if date_string in VALID_MONTH_STRINGS or "day" in date_string:
                recent_reviews.append(review)

        logging.info(f"Found {len(recent_reviews)} recent reviews.")

        return recent_reviews

    def _fetch_all_posts(self, data_id: str, business_title: str) -> list:

        if not data_id:
            return []

        params = {
            "engine": "google_maps_posts",
            "q": business_title,
            "data_id": data_id,
            "api_key": self.api_key,
        }

        return self._paginate_results(params, "posts")

    def _fetch_knowledge_graph_socials(self, query: str) -> list:

        params = {
            "engine": "google",
            "q": query,
            "api_key": self.api_key,
        }

        results = GoogleSearch(params).get_dict()
        knowledge_graph = results.get("knowledge_graph", {})
        profiles = knowledge_graph.get("profiles", [])

        return [{"name": p.get("name"), "link": p.get("link")} for p in profiles]

    def _fetch_all_reviews(self, place_id: str) -> list:

        if not place_id:
            return []

        params = {
            "engine": "google_maps_reviews",
            "place_id": place_id,
            "api_key": self.api_key,
            "sort_by": "newestFirst",
        }

        return self._paginate_results(params, "reviews")

    def _get_photo_counts(
        self, business_title: str, photo_attributions: List[Dict]
    ) -> dict:

        if not photo_attributions:
            return {"owner_photo_count": 0, "customer_photo_count": 0}

        owner_count, customer_count = 0, 0
        clean_business_title = business_title.lower().strip()
        for photo in photo_attributions:
            uploader_name = photo.get("uploader", "Unknown").lower().strip()
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

    def _fetch_details_by_place_id(self, place_id: str) -> dict:

        if not place_id:
            return {}

        details_params = {
            "engine": "google_maps",
            "place_id": place_id,
            "api_key": self.api_key,
        }

        return details_params.get("place_results", {})

    def _get_social_links(self, place_data: dict, query: str) -> list:

        links = place_data.get("links", [])

        if not links and query:
            links = self._fetch_knowledge_graph_socials(query)

        return links

    def _run_photo_scraper(self, search_url: str, business_title: str) -> list:
        with ProcessPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                run_photo_scraper_process, search_url, business_title
            )
            try:
                return future.result(timeout=300)
            except Exception as e:
                logging.error(f"Photo scraping process failed: {e}")
                return []

    def analyze(
        self, query: Optional[str] = None, place_id: Optional[str] = None
    ) -> dict:

        current_place_id = place_id
        initial_search_result = None

        if not current_place_id:
            if not query:
                return {
                    "success": False,
                    "error": "Internal Error: Either query or place_id must be provided.",
                }

            search_params = {
                "engine": "google_maps",
                "q": query,
                "type": "search",
                "api_key": self.api_key,
            }

            initial_results = GoogleSearch(search_params).get_dict()
            if initial_results.get("error"):
                return {"success": False, "error": initial_results["error"]}

            initial_search_result = (
                initial_results.get("place_results")
                or (initial_results.get("local_results", [])[0:1] or [None])[0]
            )

            if not initial_search_result:
                return {"success": False, "error": f"No GBP found for query: '{query}'"}

            current_place_id = initial_search_result.get("place_id")
            if not current_place_id:
                return {
                    "success": False,
                    "error": "Could not extract place_id from search results.",
                }

        else:
            logging.info(
                f"Analyzing directly with provided place_id: '{current_place_id}'"
            )

        details_params = {
            "engine": "google_maps",
            "place_id": current_place_id,
            "api_key": self.api_key,
        }
        details_results = GoogleSearch(details_params).get_dict()
        place_data = details_results.get("place_results", {})

        if not place_data:
            return {
                "success": False,
                "error": f"Could not fetch detailed data for place_id: {current_place_id}",
            }

        data_id = place_data.get("data_id") or (
            initial_search_result.get("data_id") if initial_search_result else None
        )
        business_title = place_data.get("title")

        all_reviews = self._fetch_all_reviews(place_id)
        recent_reviews_filtered = self._filter_reviews_by_recency(all_reviews)

        all_posts = []
        photo_attributions = []
        all_reviews = []
        social_links = []

        # updates_from_details = place_data.get("updates", {})
        # if updates_from_details:
        #     all_posts = updates_from_details.get("posts", [])

        # if not all_posts and initial_search_result:
        #     updates_from_initial = initial_search_result.get("updates", {})
        #     if updates_from_initial:
        #         all_posts = updates_from_initial.get("posts", [])

        # if not all_posts and data_id:
        #     all_posts = self._fetch_all_posts(data_id, business_title)

        search_url = f"https://www.google.com/maps/search/{business_title.replace(' ', '+')}"  # noqa

        with (
            ThreadPoolExecutor(max_workers=2) as api_executor,
            ProcessPoolExecutor(max_workers=1) as scraper_executor,
        ):

            review_future = api_executor.submit(self._fetch_all_reviews, place_id)
            social_future = api_executor.submit(
                self._get_social_links, place_data, business_title
            )
            photo_future = scraper_executor.submit(
                self._run_photo_scraper, search_url, business_title
            )

            all_reviews = review_future.result()
            social_links = social_future.result()

            updates = place_data.get("updates", {})
            if updates:
                all_posts = updates.get("posts", [])

            if not all_posts and initial_search_result:
                updates_from_initial = initial_search_result.get("updates", {})
                if updates_from_initial:
                    all_posts = updates_from_initial.get("posts", [])
            if not all_posts and data_id:
                all_posts = self._fetch_all_posts(data_id, business_title)

            photo_attributions = photo_future.result()

        # social_links = place_data.get("links", [])
        # if not social_links and business_title:
        #     social_links = self._fetch_knowledge_graph_socials(business_title)

        result_data = {
            "title": business_title,
            "place_id": current_place_id,
            "address": place_data.get("address"),
            "phone": place_data.get("phone"),
            "website": place_data.get("website"),
            "rating": place_data.get("rating"),
            "reviews_count": place_data.get("reviews"),
            "social_links": social_links,
            "recent_reviews_in_last_month_count": len(recent_reviews_filtered),
            "posts_count": len(all_posts),
            "photo_counts_by_uploader": self._get_photo_counts(
                business_title, photo_attributions
            ),
            "total_photos_analyzed": len(photo_attributions),
        }

        return {
            "success": True,
            "data": result_data,
        }
