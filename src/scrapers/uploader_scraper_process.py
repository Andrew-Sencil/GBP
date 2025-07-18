from src.scrapers.photo_scraper import PhotoScraper


def run_photo_scraper_process(search_url: str, business_title: str):
    """
    A target function for multiprocessing. It instantiates the scraper
    and runs the analysis, returning the result.
    """

    scraper = PhotoScraper()

    return scraper.get_attributions_by_navigation(search_url, business_title)
