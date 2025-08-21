from src.scrapers.photo_scraper import PhotoScraper


# The first parameter is now place_id
def run_photo_scraper_process(place_id: str, business_title: str):
    """
    A target function for multiprocessing. It instantiates the scraper
    and runs the analysis, returning the result.
    """

    scraper = PhotoScraper()

    # Pass the place_id to the scraper method
    return scraper.get_attributions_by_navigation(place_id, business_title)
