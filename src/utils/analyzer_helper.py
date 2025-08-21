import logging
from typing import List, Dict
from concurrent.futures import (
    ProcessPoolExecutor,
    TimeoutError as FutureTimeoutError,
)
from serpapi import GoogleSearch

from src.scrapers.uploader_scraper_process import run_photo_scraper_process
from src.utils.parsing import convert_relative_date_to_days

pagination_page_limit = 1
# pagination_item_limit = 200


def _safe_api_call(params: dict, description: str) -> dict:
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


def _paginate_results(params: dict, results_key: str) -> list:
    """
    Enhanced pagination with better error handling.
    """
    all_results = []
    page_count = 0

    while True:
        page_count += 1
        if page_count > pagination_page_limit:
            logging.warning(
                f"Reached page limit of {pagination_page_limit} for {params.get('engine')}"  # noqa
            )
            break

            # Use safe API call
        results = _safe_api_call(params, f"{params.get('engine')} page {page_count}")
        if not results:
            break

        page_items = results.get(results_key, [])
        if not page_items:
            break

        all_results.extend(page_items)
        logging.info(
            f"Retrieved {len(page_items)} items from page {page_count} for {params.get('engine')}"  # noqa
        )

        pagination = results.get("serpapi_pagination", {})
        if "next_page_token" in pagination:
            params["next_page_token"] = pagination["next_page_token"]
        else:
            break

    return all_results


def _filter_reviews_by_recency(all_reviews: List[Dict]) -> List[Dict]:
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


def _fetch_all_posts(data_id: str, business_title: str, api_key: str) -> list:
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
            "api_key": api_key,
        }

        return _paginate_results(params, "posts")
    except Exception as e:
        logging.error(f"Error fetching posts: {e}")
        return []


def _filter_posts_by_recency(all_posts: List[Dict]) -> int:
    """
    Filters a list of posts and returns the count of those
    posted within the last month (approximated as 31 days).
    """
    if not all_posts:
        return 0

    recent_post_count = 0
    for post in all_posts:
        date_str = post.get("posted_at_text")
        if not date_str:
            continue

        days_ago = convert_relative_date_to_days(date_str)
        if days_ago <= 31:
            recent_post_count += 1

    logging.info(f"Found {recent_post_count} posts from the last month.")
    return recent_post_count


def _fetch_knowledge_graph_socials(
    business_title: str, address: str, api_key: str
) -> list:
    """
    Enhanced social media fetching with better error handling.
    """
    if not business_title or not address:
        logging.warning("No query provided for social media fetching")
        return []

    query = f"{business_title}, {address}"
    logging.info(f"Fetching social links with specific query: '{query}'")

    try:
        params = {
            "engine": "google",
            "q": query,
            "api_key": api_key,
        }

        results = _safe_api_call(params, "knowledge graph social links")
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


def _fetch_all_reviews(place_id: str, api_key: str) -> list:
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
            "api_key": api_key,
            "sort_by": "newestFirst",
        }

        return _paginate_results(params, "reviews")
    except Exception as e:
        logging.error(f"Error fetching reviews: {e}")
        return []


def _get_photo_counts(business_title: str, photo_attributions: List[Dict]) -> dict:
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
                if uploader_name == "owner" or clean_business_title in uploader_name:
                    owner_count += 1
                else:
                    customer_count += 1
            except Exception as e:
                logging.warning(f"Error processing photo attribution: {e}")
                customer_count += 1  # Default to customer if unclear

        logging.info(
            f"Final Tally (from Playwright): Owner: {owner_count}, Customer: {customer_count}"  # noqa
        )

        return {
            "owner_photo_count": owner_count,
            "customer_photo_count": customer_count,
        }
    except Exception as e:
        logging.error(f"Error calculating photo counts: {e}")
        return default_counts


def _run_photo_scraper(place_id: str, business_title: str) -> list:
    """
    Enhanced photo scraper with better error handling and timeout management.
    """
    if not place_id or not business_title:
        logging.warning("Missing search_url or business_title for photo scraping")
        return []

    try:
        with ProcessPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                run_photo_scraper_process, place_id, business_title
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


def _get_social_links(
    place_data: dict, business_title: str, address: str, api_key: str
) -> list:

    links = place_data.get("links", []) if place_data else []
    if not links and business_title and address:
        links = _fetch_knowledge_graph_socials(business_title, address, api_key)
    return links


def _safe_get_nested_value(data: dict, key: str, default=None):

    return data.get(key, default) if data else default
