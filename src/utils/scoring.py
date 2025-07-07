def _star_rating_scoring(star_rating: float):
    """
    Assigns a score based on the star rating from 1 to 5.0.

    Args:
        star_rating (float): The star rating from 1 to 5.0.

    Returns:
        int: The score from 10 to 0.
    """
    if star_rating == 5:
        return 10
    elif star_rating <= 4.9 and star_rating >= 4.0:
        return 8
    elif star_rating <= 3.9 and star_rating >= 3.0:
        return 6
    elif star_rating <= 2.9 and star_rating >= 2.0:
        return 3
    elif star_rating <= 1.9 and star_rating >= 1.0:
        return 1
    else:
        return 0


def _owner_images_scoring(owner_photo_count: int):
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


def _customer_images_scoring(customer_photo_count: int):
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


def _fields_filled_scoring(fields_filled: int):
    """
    Assigns a score based on the number of fields filled from 0 to 10.

    Args:
        fields_filled (int): The number of fields filled.

    Returns:
        int: The score from 10 to 0.
    """
    if fields_filled >= 15:
        return 10
    elif fields_filled <= 14 and fields_filled >= 10:
        return 8
    elif fields_filled <= 9 and fields_filled >= 5:
        return 5
    elif fields_filled <= 4 and fields_filled >= 1:
        return 1
    else:
        return 0
