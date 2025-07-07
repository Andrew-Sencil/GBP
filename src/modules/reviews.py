# import csv
# import json
from serpapi import GoogleSearch
from src.core.config import SERP_API_KEY
from src.utils.scoring import _star_rating_scoring, _fields_filled_scoring


def _fetch_all_posts(data_id: str):
    """
    Private helper to fetch all the post for a given data_id.
    """
    all_posts = []
    if not data_id:
        return all_posts

    posts_params = {
        "engine": "google_maps",
        "data_id": data_id,
        "api_key": SERP_API_KEY,
    }

    while True:
        posts_results = GoogleSearch(posts_params).get_dict()
        posts = posts_results.get("posts", [])
        if not posts:
            break
        all_posts.extend(posts)

        if "next" not in posts_results.get("serpapi_pagination", {}):
            break
        posts_params["next_page_token"] = posts_results["serpapi_pagination"][
            "next_page_token"
        ]

    return all_posts


def _fetch_all_photos(data_id: str) -> list:
    """
    Private helper to fetch all the photo URLs for a given data_id.
    """

    all_photos = []
    if not data_id:
        return all_photos

    photos_params = {
        "engine": "google_maps_photos",
        "data_id": data_id,
        "api_key": SERP_API_KEY,
    }

    for _ in range(5):
        photos_results = GoogleSearch(photos_params).get_dict()
        photos = photos_results.get("photos", [])
        if not photos:
            break
        all_photos.extend(photos)

        if (
            "next" not in photos_results.get("serpapi_pagination", {})
            or len(all_photos) == 100
        ):
            break
        photos_params["next_page_token"] = photos_results["serpapi_pagination"][
            "next_page_token"
        ]

        return all_photos


def _fetch_knowledge_graph_socials(query: str) -> list:
    """
    Performs a regular Google search to find the social profiles in the Knowledge Graph.
    """

    print("[Info] Checking Google Knowledge Panel for social links...")
    params = {
        "engine": "google",
        "q": query,
        "api_key": SERP_API_KEY,
    }
    search = GoogleSearch(params)
    results = search.get_dict()

    knowledge_graph = results.get("knowledge_graph", {})
    profiles = knowledge_graph.get("profiles", [])

    standardized_profiles = []
    for profile in profiles:
        standardized_profiles.append(
            {
                "name": profile.get("name"),
                "link": profile.get("link"),
            }
        )

    return standardized_profiles


def _fetch_all_reviews(place_id: str) -> list:
    """
    Fetches all reviews for a given place_id by paginating.
    """
    all_reviews = []
    if not place_id:
        return all_reviews

    reviews_params = {
        "engine": "google_maps_reviews",
        "place_id": place_id,
        "api_key": SERP_API_KEY,
    }

    print("[Info] Fetching all reviews to count every customer photo...")
    for _ in range(5):
        reviews_results = GoogleSearch(reviews_params).get_dict()
        reviews = reviews_results.get("reviews", [])
        if not reviews:
            break
        all_reviews.extend(reviews)

        if (
            "next" not in reviews_results.get("serpapi_pagination", {})
            or len(all_reviews) == 100
        ):
            break
        reviews_params["next_page_token"] = reviews_results["serpapi_pagination"][
            "next_page_token"
        ]

    return all_reviews


def _get_photo_counts(place_data: dict, all_reviews: list, business_title: str) -> dict:
    """
    Performs a continuous count of all identifiable owner and customer photos.
    """

    owner_photo_count = 0
    customer_photo_count = 0

    if place_data.get("thumbnail"):
        owner_photo_count += 1

    main_photos = place_data.get("photos", [])
    for photo in main_photos:
        if (
            photo.get("title", "").lower() == "by owner"
            or photo.get("user", {}).get("name") == business_title
            or photo.get("user", {}).get("name") == "foodpanda"
        ):
            owner_photo_count += 1

    for review in all_reviews:
        customer_photo_count += len(review.get("images", []))

    return {
        "owner_photo_count": owner_photo_count,
        "customer_photo_count": customer_photo_count,
    }


def analyze_profile(query: str) -> dict:
    """
    Fetches and analyzes a Google Business Profile, returning a
    dictionary of the findings.
    This function does not print. It returns structured data.
    """

    analysis_result = {
        "query": query,
        "success": False,
        "error": None,
        "data": {},
    }

    search_params = {
        "engine": "google_maps",
        "q": query,
        "type": "search",
        "api_key": SERP_API_KEY,
    }
    initial_results = GoogleSearch(search_params).get_dict()

    first_result = None
    if initial_results.get("error"):
        analysis_result["error"] = initial_results["error"]
        return analysis_result

    if "place_results" in initial_results:
        first_result = initial_results["place_results"]
    elif "local_results" in initial_results and initial_results["local_results"]:
        first_result = initial_results["local_results"][0]
    else:
        analysis_result["error"] = "No GBP found for this query."
        return analysis_result

    place_id = first_result.get("place_id")
    data_id = first_result.get("data_id")
    business_title = first_result.get("title")

    details_params = {
        "engine": "google_maps",
        "data_id": data_id,
        "api_key": SERP_API_KEY,
    }
    details_results = GoogleSearch(details_params).get_dict()
    place_data = details_results.get("place_results", {})

    details_params = {
        "engine": "google_maps",
        "place_id": place_id,
        "api_key": SERP_API_KEY,
    }
    details_results = GoogleSearch(details_params).get_dict()
    place_data = details_results.get("place_results", {})

    analysis_result["success"] = True
    result_data = analysis_result["data"]

    result_data["title"] = business_title
    result_data["place_id"] = place_id
    result_data["data_id"] = data_id
    result_data["address"] = place_data.get("address")
    result_data["phone"] = place_data.get("phone")
    result_data["website"] = place_data.get("website")
    result_data["rating"] = place_data.get("rating")
    print("Star Rating Score: ", _star_rating_scoring(result_data["rating"]))
    result_data["reviews_count"] = place_data.get("reviews")
    result_data["description"] = place_data.get("description")

    social_links = place_data.get("links", [])
    if not social_links:
        print("[Info] No GBP links found. Falling back to Google Knowledge Panel.")
        social_links = _fetch_knowledge_graph_socials(query)
    result_data["social_links"] = social_links

    attributes_list = []
    extensions_data = place_data.get("extensions", [])
    if isinstance(extensions_data, list):
        for item in extensions_data:
            for attribute_group in item.values():
                if isinstance(attribute_group, list):
                    attributes_list.extend(attribute_group)

    result_data["attributes"] = attributes_list

    if result_data["description"] is not None:
        print("All fields score: ", _fields_filled_scoring(len(result_data["attributes"])))

    all_posts = _fetch_all_posts(data_id)
    result_data["posts_count"] = len(all_posts)
    result_data["most_recent_post_date"] = (
        all_posts[0].get("date") if all_posts else None
    )

    all_photos = _fetch_all_photos(data_id)
    result_data["photos"] = len(all_photos)

    all_reviews = _fetch_all_reviews(place_id)

    result_data["photo_counts_by_uploader"] = _get_photo_counts(
        place_data, all_reviews, business_title
    )

    return analysis_result
