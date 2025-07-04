# import csv
import json
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


def analyze_photo_data(photos, business_title):
    """Categorizes photos into owner-uploaded and customer-uploaded."""
    owner_photo_count = 0
    customer_photo_count = 0
    for photo in photos:
        user_data = photo.get("user")
        if not user_data or user_data.get("name") == business_title:
            owner_photo_count += 1
        else:
            customer_photo_count += 1
    return owner_photo_count, customer_photo_count


def count_customer_photos(user_reviews):
    """Counts the total number of images found within the user_reviews block."""
    if not user_reviews or "most_relevant" not in user_reviews:
        return 0

    total_customer_photos = 0
    for review in user_reviews["most_relevant"]:
        # Each review can have a list of images. Add the count of that list.
        total_customer_photos += len(review.get("images", []))

    return total_customer_photos


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

    search = GoogleSearch(search_params)
    search_results = search.get_dict()

    target_place_id = None
    target_data_id = None
    business_title = ""

    if "place_results" in search_results:
        print("--- Found a specific 'place_results' object. ---")
        first_result = search_results["place_results"]
        target_place_id = first_result.get("place_id")
        target_data_id = first_result.get("data_id")
        business_title = first_result.get("title")
        business_address = first_result.get("address")
        business_phone = first_result.get("phone")
        business_site = first_result.get("website")
        print("Found business: ", business_title)
        print("Located at: ", business_address)
        print("Contact: ", business_phone)
        print("Website: ", business_site)
        print("With a rating of: ", first_result.get("rating"))
        print("A total reviews of: ", first_result.get("reviews"))
        print("Successfully extracted its place_id: ", target_place_id)
        print("Successfully extracted its place_id: ", target_data_id)

        details_params = {
            "engine": "google_maps",
            "place_id": target_place_id,
            "api_key": API_KEY,
        }

        details_search = GoogleSearch(details_params)
        details_results = details_search.get_dict()
        place_data = details_results.get("place_results", {})

        print("\n" + "="*20 + " DEBUGGING " + "="*20)
        print("--- FULL 'place_data' OBJECT STRUCTURE ---")
        # This will "pretty-print" the entire dictionary so we can inspect it.
        print(json.dumps(place_data, indent=2))
        print("--- END OF DEBUGGING ---")
        print("="*53 + "\n")

        print("--- Analyzing for Social Media Links... ---")
        social_links = place_data.get("links", []) # Use .get() for safety

        if social_links:
            print(f"--- Success! Found {len(social_links)} social media profiles. ---")
            for profile in social_links:
                name = profile.get("name")
                link = profile.get("link")
                print(f"  - {name}: {link}")
        else:
            print("--- No social media links found for this business. ---")

        print("--- Analyzing photos from user reviews... ---")

        # Get the rich user reviews block from the details call
        user_reviews_data = place_data.get("user_reviews", {})

        # Count customer photos from within the reviews
        customer_photo_count = count_customer_photos(user_reviews_data)

        print("Total customer photo count:", customer_photo_count)

        print("--- Step 1.6: Extracting Attributes from 'extensions' ---")
        attributes_list = []

        # Get the 'extensions' list from the place_data
        extensions_data = place_data.get("extensions")

        # Check if extensions_data exists and is a list
        if extensions_data and isinstance(extensions_data, list):
            # Loop through each dictionary in the 'extensions' list (e.g., {"service_options": [...]})
            for item in extensions_data:
                # Loop through the values of that dictionary (which will be the list of actual attributes)
                for attribute_group in item.values():
                    if isinstance(attribute_group, list):
                        # Add the attributes from the group to our main list
                        attributes_list.extend(attribute_group)

        # Now, we print the results based on the 'attributes_list' we just built
        if attributes_list:
            print(
                f"--- Success! Found {len(attributes_list)} attributes for this business ---"
            )
            for attr in attributes_list:
                print(f"  - {attr}")
        else:
            print("--- No attributes found under the 'extensions' key. ---")

        print("--- Fetching all posts for analysis... ---")
        all_posts = []
        if target_data_id:
            posts_params = {
                "engine": "google_maps_posts",
                "data_id": target_data_id,  # Use data_id for posts
                "api_key": API_KEY,
            }
            while True:
                posts_search = GoogleSearch(posts_params)
                posts_results = posts_search.get_dict()
                if "posts" in posts_results:
                    all_posts.extend(posts_results["posts"])
                else:
                    break
                if "next" not in posts_results.get("serpapi_pagination", {}):
                    break
                posts_params["next_page_token"] = posts_results["serpapi_pagination"][
                    "next_page_token"
                ]

        if all_posts:
            # --- 2. ADD THIS DEBUGGING BLOCK ---
            print(f"--- Success! Found a total of {len(all_posts)} posts. ---")

            # This is the original code that is currently failing
            most_recent_post = all_posts[0]
            date_of_recent_post = most_recent_post.get("posted_at_text", "Date not available")

            print(f"Date of most recent post: {date_of_recent_post}")
        else:
            print("--- No posts found for this business. ---")

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
                photos_params["next_page_token"] = photos_results["serpapi_pagination"][
                    "next_page_token"
                ]

                if len(all_photos) == 100:
                    break

            photo_count = len(all_photos)
            print(f"And a total of {photo_count} photos.")

            owner_count, customer_count = analyze_photo_data(all_photos, business_title)
            print(f"--- Found {len(all_photos)} total photos. ---")
            print(f"    - Owner-uploaded: {owner_count}")
            print(f"    - Customer-uploaded: {customer_count}")
            print("-" * 28)

    elif "local_results" in search_results and len(search_results["local_results"]) > 0:
        first_result = search_results["local_results"][0]
        target_place_id = first_result.get("place_id")
        target_data_id = first_result.get("data_id")
        business_title = first_result.get("title")
        business_address = first_result.get("address")
        business_phone = first_result.get("phone")
        business_site = first_result.get("website")
        print("Found business: ", business_title)
        print("Located at: ", business_address)
        print("Contact: ", business_phone)
        print("Website: ", business_site)
        print("With a rating of: ", first_result.get("rating"))
        print("A total reviews of: ", first_result.get("reviews"))
        print("Successfully extracted its place_id: ", target_place_id)
        print("Successfully extracted its place_id: ", target_data_id)

        details_params = {
            "engine": "google_maps",
            "place_id": target_place_id,
            "api_key": API_KEY,
        }

        details_search = GoogleSearch(details_params)
        details_results = details_search.get_dict()
        place_data = details_results.get("place_results", {})

        photo_sample = place_data.get("user_photos", [])

        if photo_sample:
            print("--- Analyzing photo sample for Owner vs. Customer uploads... ---")

            # Now, analyze and score the photos using the rich sample data
            owner_count, customer_count = analyze_photo_data(photo_sample, business_title)

            print(f"--- Analysis based on a sample of {len(photo_sample)} photos ---")
            print(f"    - Owner-uploaded in sample: {owner_count}")
            print(f"    - Customer-uploaded in sample: {customer_count}")
        else:
            print("--- No photo sample available in the details API response. ---")

        print("--- Step 1.6: Extracting Attributes from 'extensions' ---")
        attributes_list = []

        # Get the 'extensions' list from the place_data
        extensions_data = place_data.get("extensions")

        # Check if extensions_data exists and is a list
        if extensions_data and isinstance(extensions_data, list):
            # Loop through each dictionary in the 'extensions' list (e.g., {"service_options": [...]})
            for item in extensions_data:
                # Loop through the values of that dictionary (which will be the list of actual attributes)
                for attribute_group in item.values():
                    if isinstance(attribute_group, list):
                        # Add the attributes from the group to our main list
                        attributes_list.extend(attribute_group)

        # Now, we print the results based on the 'attributes_list' we just built
        if attributes_list:
            print(
                f"--- Success! Found {len(attributes_list)} attributes for this business ---"
            )
            for attr in attributes_list:
                print(f"  - {attr}")
        else:
            print("--- No attributes found under the 'extensions' key. ---")

        print("--- Fetching all posts for analysis... ---")
        all_posts = []
        if target_data_id:
            posts_params = {
                "engine": "google_maps_posts",
                "data_id": target_data_id,  # Use data_id for posts
                "api_key": API_KEY,
            }
            while True:
                posts_search = GoogleSearch(posts_params)
                posts_results = posts_search.get_dict()
                if "posts" in posts_results:
                    all_posts.extend(posts_results["posts"])
                else:
                    break
                if "next" not in posts_results.get("serpapi_pagination", {}):
                    break
                posts_params["next_page_token"] = posts_results["serpapi_pagination"][
                    "next_page_token"
                ]

        if all_posts:
            # --- 2. ADD THIS DEBUGGING BLOCK ---
            print(f"--- Success! Found a total of {len(all_posts)} posts. ---")

            # This is the original code that is currently failing
            most_recent_post = all_posts[0]
            date_of_recent_post = most_recent_post.get("posted_at_text", "Date not available")

            print(f"Date of most recent post: {date_of_recent_post}")
        else:
            print("--- No posts found for this business. ---")

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
                photos_params["next_page_token"] = photos_results["serpapi_pagination"][
                    "next_page_token"
                ]

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

    # Example 1: Mimicking a Zipcode and Radius search from your form
    print("\n--- EXAMPLE 1: SEARCHING BY ZIPCODE ---")
    get_reviews(query="Pilsen Yards, 60608, USA", location_name=None)

    print("\n" + "=" * 50 + "\n")

    # Example 2: Mimicking a Latitude/Longitude and Radius search
    print("--- EXAMPLE 2: SEARCHING BY COORDINATES & RADIUS ---")
    get_reviews(query="Restaurant", latitude=10.317, longitude=123.905, radius_miles=5)

    print("\n" + "=" * 50 + "\n")
