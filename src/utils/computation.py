from src.utils.scoring import (
    _star_rating_scoring,
    _fields_filled_scoring,
    _review_count_scoring,
    _review_recency_scoring,
    _NAPW_completeness_scoring,
    _google_post_scoring,
    _owner_images_scoring,
    _customer_images_scoring,
)


def calculate_score(business_data: dict) -> float:

    photo_count = business_data.get("photo_counts_by_uploader", {})

    owner_photos = photo_count.get("owner_photo_count", 0)
    customer_photos = photo_count.get("customer_photo_count", 0)

    star_rating = _star_rating_scoring(business_data.get("rating", 0))
    review_count = _review_count_scoring(business_data.get("reviews_count", 0))
    attributes = business_data.get("attributes_count", 0)
    description = business_data.get("description")
    name = business_data.get("title")
    address = business_data.get("address")
    phone = business_data.get("phone")
    website = business_data.get("website")
    google_post = business_data.get("posts_count")
    review_recency = business_data.get("recent_reviews_in_last_month_count")

    completeness_score = _fields_filled_scoring(attributes, description)
    NAPW_score = _NAPW_completeness_scoring(name, address, phone, website)
    google_post_score = _google_post_scoring(google_post)
    owner_score = _owner_images_scoring(owner_photos)
    customer_score = _customer_images_scoring(customer_photos)
    review_recency_score = _review_recency_scoring(review_recency)
    total_image_score = (owner_score + customer_score) / 2

    print("completeness_score: ", completeness_score)
    print("NAPW_score: ", NAPW_score)
    print("google_post_score: ", google_post_score)
    print("owner_score: ", owner_score)
    print("customer_score: ", customer_score)
    print("review_recency_score: ", review_recency_score)
    print("total_image_score: ", total_image_score)

    # Your weighting logic remains the same
    weighted_google_score = google_post_score * 0.20
    weighted_image_score = total_image_score * 0.20
    weighted_review_recency_score = review_recency_score * 0.20
    weighted_star_score = star_rating * 0.15
    weighted_review_score = review_count * 0.15
    weighted_fields_score = completeness_score * 0.05
    weighted_napw_score = NAPW_score * 0.05

    print("weighted_google_score: ", weighted_google_score)
    print("weighted_image_score: ", weighted_image_score)
    print("weighted_review_recency_score: ", weighted_review_recency_score)
    print("weighted_star_score: ", weighted_star_score)
    print("weighted_review_score: ", weighted_review_score)
    print("weighted_fields_score: ", weighted_fields_score)
    print("weighted_napw_score: ", weighted_napw_score)

    business_score = (
        weighted_google_score
        + weighted_image_score
        + weighted_review_recency_score
        + weighted_star_score
        + weighted_review_score
        + weighted_fields_score
        + weighted_napw_score
    )

    safe_score = round(business_score, 1)

    print("safe_score: ", safe_score)

    return safe_score
