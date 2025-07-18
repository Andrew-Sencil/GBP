def _star_rating_scoring(star_rating: float):
    """
    Assigns a score based on the star rating from 1 to 5.0.

    Args:
        star_rating (float): The star rating from 1 to 5.0.

    Returns:
        int: The score from 10 to 0.
    """
    return (star_rating / 5) * 10


def _owner_images_scoring(owner_photo_count: float):
    """
    Assigns a score based on the number of owner images from 0 to 10.

    Args:
        owner_photo_count (int): The number of owner images.

    Returns:
        int: The score from 10 to 0.
    """
    if owner_photo_count >= 20:
        return 10
    elif owner_photo_count <= 19 and owner_photo_count >= 10:
        return 8
    elif owner_photo_count <= 9 and owner_photo_count >= 5:
        return 5
    elif owner_photo_count <= 4 and owner_photo_count >= 1:
        return 2
    else:
        return 0


def _customer_images_scoring(customer_photo_count: float):
    """
    Assigns a score based on the number of customer images from 0 to 10.

    Args:
        customer_photo_count (int): The number of customer images.

    Returns:
        int: The score from 10 to 0.
    """
    if customer_photo_count >= 75:
        return 10
    elif customer_photo_count <= 74 and customer_photo_count >= 50:
        return 8
    elif customer_photo_count <= 49 and customer_photo_count >= 30:
        return 6
    elif customer_photo_count <= 29 and customer_photo_count >= 15:
        return 4
    elif customer_photo_count <= 14 and customer_photo_count >= 5:
        return 3
    elif customer_photo_count <= 4 and customer_photo_count >= 1:
        return 1
    else:
        return 0


def _fields_filled_scoring(attributes: list, description: str):
    """
    Assigns a score based on the number of fields filled from 0 to 10.

    Args:
        fields_filled (int): The number of fields filled.

    Returns:
        int: The score from 10 to 0.
    """

    description_score = 2 if description else 0

    attribute_score = 0
    fields_filled = attributes

    if fields_filled >= 15:
        attribute_score = 8
    elif fields_filled <= 14 and fields_filled >= 10:
        attribute_score = 6
    elif fields_filled <= 9 and fields_filled >= 5:
        attribute_score = 4
    elif fields_filled <= 4 and fields_filled >= 1:
        attribute_score = 1
    else:
        attribute_score = 0

    return description_score + attribute_score


def _review_recency_scoring(total_review: int):
    """
    Assigns a score based on the review recency from 0 to 10 within the span of 1 month.

    Args:
        date_reviewed (str): The date of the review in '%Y-%m-%d' format.

    Returns:
        int: The score from 10 to 0.
    """

    if total_review >= 5:
        return 10
    elif total_review == 4:
        return 8
    elif total_review == 3:
        return 4
    elif total_review == 2:
        return 2
    elif total_review == 1:
        return 1
    else:
        return 0


def _review_count_scoring(review_count: float):
    """
    Assigns a score based on the review count from 0 to 10.

    Args:
        review_count (int): The review count.

    Returns:
        int: The score from 10 to 0.
    """
    if review_count >= 250:
        return 10
    elif review_count <= 249 and review_count >= 100:
        return 8
    elif review_count <= 99 and review_count >= 50:
        return 6
    elif review_count <= 49 and review_count >= 10:
        return 3
    elif review_count <= 9 and review_count >= 1:
        return 1
    else:
        return 0


def _NAPW_completeness_scoring(name: str, address: str, phone: str, website: str):
    """
    Assigns a score based on the completeness of the NAPW from 0 to 10.

    Args:
        name (str): The name of the business.
        address (str): The address of the business.
        phone (str): The phone number of the business.
        website (str): The website of the business.

    Returns:
        int: The score from 10 to 0.
    """

    items_to_check = [name, address, phone, website]
    existing_items = [item for item in items_to_check if item]
    special_sites = [".business.site", "facebook.com", "instagram.com", "linkedin.com"]

    if len(existing_items) == 4:
        return 10
    elif website and any(site in website for site in special_sites):
        return 8
    elif len(existing_items) == 3:
        return 6
    elif len(existing_items) == 2:
        return 3
    elif len(existing_items) == 1:
        return 1
    else:
        return 0


def _google_post_scoring(update_count: int):
    """
    Assigns a score based on the post recency from 0 to 10.

    Args:
        date (str): The date of the post in '%Y-%m-%d' format.

    Returns:
        int: The score from 10 to 0.
    """
    if update_count >= 4:
        return 10
    elif update_count == 3:
        return 7
    elif update_count == 2:
        return 5
    elif update_count == 1:
        return 2
    else:
        return 0
