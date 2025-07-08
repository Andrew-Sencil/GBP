import logging
from dataclasses import dataclass, field
from serpapi import GoogleSearch

# --- Configuration ---
# In a real app, this would come from a config file or environment variables
SERP_API_KEY = "YOUR_SERP_API_KEY"

# Configure logging
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


@dataclass
class GmbProfileData:
    """A container for all data fetched for a single GMB profile."""

    business_title: str
    place_data: dict = field(default_factory=dict)
    all_photos: list = field(default_factory=list)
    all_reviews: list = field(default_factory=list)
    owner_photos_from_posts: list = field(default_factory=list)


class GmbAnalyzer:
    """
    A class to encapsulate the logic for fetching and analyzing a Google Business Profile.
    """

    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("SERP_API_KEY is required.")
        self.api_key = api_key
        # Safety limits to prevent excessive API usage
        self.pagination_page_limit = 5
        self.pagination_item_limit = 100

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
        self,
        profile_data: GmbProfileData,
    ) -> dict:
        """
        Streamlined and efficient photo counting.
        - Source of Truth for Customer Photos: Images attached to reviews.
        - Source of Truth for Owner Photos: High-confidence signals in the main photos list.
        """
        logging.info("Starting advanced photo classification using Google Posts. . .")

        distinct_owner_photo_urls = set()
        distinct_customer_photo_urls = set()

        if profile_data.place_data.get("thumbnail"):
            distinct_owner_photo_urls.add(profile_data.place_data["thumbnail"])
        for url in profile_data.owner_photos_from_posts:
            if url:
                distinct_owner_photo_urls.add(url)

        logging.info(
            f"Found {len(distinct_owner_photo_urls)} owner photos from high-confidence sources."
        )

        for photo in profile_data.all_photos:
            photo_url = photo.get("image")
            if not photo_url or photo_url in distinct_owner_photo_urls:
                continue

            photo_title = photo.get("title", "").lower()
            photo_user_name = photo.get("user", {}).get("name", "")

            is_owner_photo = (
                photo_title == "by owner"
                or photo_user_name == profile_data.business_title
                or "owner" in photo_title
            )

            if is_owner_photo:
                distinct_owner_photo_urls.add(photo_url)
            else:
                distinct_customer_photo_urls.add(photo_url)

            for review in profile_data.all_reviews:
                for img in review.get("images", []):
                    if img and img not in distinct_owner_photo_urls:
                        distinct_customer_photo_urls.add(img)

            owner_count = len(distinct_owner_photo_urls)
            customer_count = len(distinct_customer_photo_urls)

            logging.info(
                f"Classification complete. Final distinct counts -> Owner: {owner_count}, Customer: {customer_count}"
            )
            return {
                "distinct_owner_photo_count": owner_count,
                "distinct_customer_photo_count": customer_count,
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
        logging.info(f"Found business: '{business_title}' (Place ID: {place_id})")

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

        # Step 3: Fetch all supplementary data
        all_posts = self.fetch_all_posts(data_id, business_title)
        all_photos = self.fetch_all_photos(data_id)
        all_reviews = self.fetch_all_reviews(place_id)
        owner_photos_from_posts = [post["image_url"] for post in all_posts if post.get("image_url")]

        profile_data = GmbProfileData(
            business_title=business_title,
            place_data=place_data,
            all_photos=all_photos,
            all_reviews=all_reviews,
            owner_photos_from_posts=owner_photos_from_posts,
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
        result_data["total_photo_count"] = len(all_photos)
        result_data["photo_counts_by_uploader"] = self._get_photo_counts(profile_data)
        analysis_result["success"] = True
        return analysis_result
