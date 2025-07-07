# import csv
import json
from src.core.config import SERP_API_KEY
from src.utils.parsing import analyze_photo_data, count_customer_photos
from serpapi import GoogleSearch


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

    API_KEY = SERP_API_KEY

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


if __name__ == "__main__":

    # Example 1: Mimicking a Zipcode and Radius search from your form
    print("\n--- EXAMPLE 1: SEARCHING BY ZIPCODE ---")
    get_reviews(query="Pilsen Yards, 60608, USA", location_name=None)

    print("\n" + "=" * 50 + "\n")

    # Example 2: Mimicking a Latitude/Longitude and Radius search
    print("--- EXAMPLE 2: SEARCHING BY COORDINATES & RADIUS ---")
    get_reviews(query="Restaurant", latitude=10.317, longitude=123.905, radius_miles=5)

    print("\n" + "=" * 50 + "\n")
