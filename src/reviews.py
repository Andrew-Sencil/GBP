# import csv
import os
from dotenv import load_dotenv
from serpapi import GoogleSearch


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


def get_reviews(
    query, location_name=None, latitude=None, longitude=None, radius_miles=None
):
    """
    Fetches, sorts, and saves reviews for a given business found based on
    search criteria.

    Args:
        query (str): The type of business or place name (e.g., "Starbucks").
        location_name (str, optional): A location name like "Cebu, Philippines"
          or a zipcode.
        latitude (float, optional): The latitude of the searched location.
        longitude (float, optional): The longitude of the searched location.
        radius_miles (float, optional): The search radius in miles
         (only used with lat/lon).
    """

    load_dotenv()

    API_KEY = os.getenv("SERP_API_KEY")

    if not API_KEY:
        print("Error: SERP_API_KEY not foun. Make sure it's set in your .env file.")
        exit()

    print(f"--- Step 1: Searching for {query} ---")

    search_params = {
        "engine": "google_maps",
        "q": query,
        "type": "search",
        "api_key": API_KEY,
    }

    if latitude and longitude:
        search_params["ll"] = f"@{latitude},{longitude},15z"
        print(f"Searching by coordinates: {latitude}, {longitude}")
        if radius_miles:
            radius_meters = int(radius_miles * 1609.34)
            search_params["radius"] = radius_meters
            print(f"Using a radius of {radius_meters} miles ({radius_meters} meters)")
    elif location_name:
        search_params["location"] = location_name
        print(f"Searching by location: {location_name}")
    else:
        print("Error: You must provide either a location_name or latitude/longitude.")
        return

    search = GoogleSearch(search_params)
    search_results = search.get_dict()

    target_place_id = None
    target_data_id = None
    business_title = ""

    if "local_results" in search_results and len(search_results["local_results"]) > 0:
        first_result = search_results["local_results"][0]
        target_place_id = first_result.get("place_id")
        target_data_id = first_result.get("data_id")
        business_title = first_result.get("title")
        print("Found business: ", first_result.get("title"))
        print("With a rating of: ", first_result.get("rating"))
        print("And a total reviews of: ", first_result.get("reviews"))
        print("Successfully extracted its place_id: ", target_data_id)

        if target_data_id:
            print("--- Fetching place details for photo count... ---")

            all_photos = []
            photos_params = {
                "engine": "google_maps_photos",
                "data_id": target_data_id,  # Use data_id for photos engine
                "api_key": API_KEY,
            }

            while True:
                photos_search = GoogleSearch(photos_params)
                photos_results = photos_search.get_dict()

                if "photos" in photos_results:
                    all_photos.extend(photos_results["photos"])
                else:
                    break  # Exit if no photos on the page

                if "next" not in photos_results.get("serpapi_pagination", {}):
                    break  # Exit if it's the last page

                # Get the token for the next page of photos
                photos_params["next_page_token"] = photos_results["serpapi_pagination"]["next_page_token"]

                if len(all_photos) == 100:
                    break

            photo_count = len(all_photos)
            print(f"And a total of {photo_count} photos.")

    else:
        print("Could not find any local results for the search query.")
        if "error" in search_results:
            print(f"API Error: {search_results['error']}")
        exit()

    if target_data_id:
        print("--- Step 2: Fetching reviews using engine 'google_maps_reviews' ---")

        # all_reviews = []

        # reviews_params = {
        #     "engine": "google_maps_reviews",
        #     "place_id": target_data_id,
        #     "api_key": API_KEY,
        # }

        # page_num = 1
        # while page_num <= 3:
        #     reviews_search = GoogleSearch(reviews_params)
        #     reviews_results = reviews_search.get_dict()

        #     if "reviews" in reviews_results:
        #         all_reviews.extend(reviews_results["reviews"])
        #     else:
        #         print("No reviews found on this page.")
        #         break

        #     if "next" not in reviews_results.get("serpapi_pagination", {}):
        #         print("--- No more review pages. All reviews collected. ---")
        #         break

        #     reviews_params["next_page_token"] = reviews_results["serpapi_pagination"][
        #         "next_page_token"
        #     ]
        #     page_num += 1

        # if all_reviews:

        #     sorted_reviews = sorted(
        #         all_reviews,
        #         key=lambda review: convert_relative_date_to_days(review.get("date")),
        #     )

            # for review in sorted_reviews[:10]:
                # print(f"User:   {review.get('user', {}).get('name', 'N/A')}")
                # print(f"Rating: {review.get('rating')} ★")
                # print(f"Date:   {review.get('date')}")
                # print("-" * 25)

            # if sorted_reviews:
            #     safe_filename = "".join(
            #         c for c in business_title if c.isalnum() or c in (" ", "_")
            #     ).rstrip()
            #     output_filename = f"{safe_filename}_reviews_sorted.csv"

            #     print(
            #         f"--- Writing {len(sorted_reviews)} sorted reviews to {output_filename} ---"
            #     )
            #     with open(
            #         output_filename, "w", newline="", encoding="utf-8"
            #     ) as csvfile:
            #         csv_writer = csv.writer(csvfile)
            #         csv_writer.writerow(
            #             ["User Name", "Rating", "Date", "Review Snippet"]
            #         )

            #         # We now loop through the NEW 'sorted_reviews' list
            #         for review in sorted_reviews:
            #             csv_writer.writerow(
            #                 [
            #                     review.get("user", {}).get("name", "N/A"),
            #                     review.get("rating", "N/A"),
            #                     review.get("date", "N/A"),
            #                     review.get("snippet", "No snippet available"),
            #                 ]
            #             )
            #     print(f"--- Success! Data saved to {output_filename} ---")
            # else:
            #     print("\n--- No reviews were found to save. ---")


if __name__ == "__main__":

    SEARCH_QUERY = "Palazzo Cafe"
    LOCATION_QUERY = "Springfield, MA, USA"  # <-- Tell the API to look in the correct city and country

    print("\n--- Searching for the business from the screenshot ---")
    get_reviews(query=SEARCH_QUERY, location_name=LOCATION_QUERY)

    # Example 1: Mimicking a Zipcode and Radius search from your form
    print("\n--- EXAMPLE 1: SEARCHING BY ZIPCODE ---")
    get_reviews(query="Coffee Shop", location_name="90210, USA")

    print("\n" + "=" * 50 + "\n")

    # Example 2: Mimicking a Latitude/Longitude and Radius search
    print("--- EXAMPLE 2: SEARCHING BY COORDINATES & RADIUS ---")
    get_reviews(query="Restaurant", latitude=10.317, longitude=123.905, radius_miles=5)

    print("\n" + "=" * 50 + "\n")

    # Example 3: Your original search for reference
    print("--- EXAMPLE 3: YOUR ORIGINAL CEBU SEARCH ---")
    get_reviews(query="Stalls", location_name="Cebu, Philippines")

    print("\n" + "=" * 50 + "\n")
