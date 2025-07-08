from src.utils.scoring import (
    _star_rating_scoring,
    _fields_filled_scoring,
    _review_count_scoring,
    _NAPW_completeness_scoring,
    _google_post_scoring,
)


def calculate_score(business_data: dict) -> float:

    star_rating = _star_rating_scoring(business_data.get("rating", 0))
    review_count = _review_count_scoring(business_data.get("reviews_count", 0))
    attributes = business_data.get("attributes", [])
    description = business_data.get("description")
    name = business_data.get("title")
    address = business_data.get("address")
    phone = business_data.get("phone")
    website = business_data.get("website")
    google_post = business_data.get("most_recent_post_date")

    completeness_score = _fields_filled_scoring(attributes, description)
    NAPW_score = _NAPW_completeness_scoring(name, address, phone, website)
    google_post_score = _google_post_scoring(google_post)

    # Your weighting logic remains the same
    weighted_star_score = star_rating * 0.25
    weighted_fields_score = completeness_score * 0.15
    weighted_review_score = review_count * 0.10
    weighted_napw_score = NAPW_score * 0.15
    weighted_google_score = google_post_score * 0.10

    business_score = (
        weighted_star_score
        + weighted_fields_score
        + weighted_review_score
        + weighted_napw_score
        + weighted_google_score
    )

    safe_score = round(business_score, 4)

    return f"{safe_score:.1f}"
