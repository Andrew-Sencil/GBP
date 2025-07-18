def convert_relative_date_to_days(date_str):
    """
    Converts a relative date string (e.g., "a week ago") into an estimated
    number of days for sorting purposes.
    """
    if not isinstance(date_str, str):
        return float("inf")

    date_str = date_str.lower()
    num = 0

    if "now" in date_str or "moment" in date_str:
        return 0

    parts = date_str.split()
    if parts[0] in ["a", "an"]:
        num = 1
    else:
        try:
            num = int(parts[0])
        except (ValueError, IndexError):
            return float("inf")

    if "day" in date_str:
        return num
    elif "week" in date_str:
        return num * 7
    elif "month" in date_str:
        return num * 30
    elif "year" in date_str:
        return num * 365
    elif "hour" in date_str:
        return num / 24

    return float("inf")


def count_customer_photos(user_reviews):
    """Counts the total number of images found within the user_reviews block."""
    if not user_reviews or "most_relevant" not in user_reviews:
        return 0

    total_customer_photos = 0
    for review in user_reviews["most_relevant"]:
        # Each review can have a list of images. Add the count of that list.
        total_customer_photos += len(review.get("images", []))

    return total_customer_photos


def _convert_relative_date_to_days(date_str: str) -> float:
    """
    Converts a relative date string (e.g., "a week ago") into an estimated
    number of days. Returns infinity for unparseable strings.
    """
    if not isinstance(date_str, str):
        return float("inf")

    date_str = date_str.lower()
    num = 0

    if "now" in date_str or "moment" in date_str:
        return 0

    parts = date_str.split()
    if not parts:
        return float("inf")

    if parts[0] in ["a", "an"]:
        num = 1
    else:
        try:
            num = int(parts[0])
        except ValueError:
            return float("inf")

    if "day" in date_str:
        return num
    elif "week" in date_str:
        return num * 7
    elif "month" in date_str:
        return num * 30
    elif "year" in date_str:
        return num * 365
    elif "hour" in date_str:
        return num / 24

    return float("inf")
