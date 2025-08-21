import logging
from typing import List, Dict
from playwright.sync_api import (
    sync_playwright,
    TimeoutError as PlaywrightTimeoutError,
    Page,
)
import re


class PhotoScraper:
    """
    FINAL WORKING VERSION: This scraper abandons the flawed looping methods
    and mimics human behavior by repeatedly clicking the 'Next' button inside
    the photo viewer. This is the most robust and stable strategy to prevent

    stale element errors and handle different media types.
    """

    def __init__(self, check_limit: int = 100):
        self.PHOTO_CHECK_LIMIT = check_limit
        self.SELECTORS = {
            "first_photo_in_gallery": 'a[aria-label*="Photo"]',
            "uploader_link": 'a[href*="/contrib/"]',
            "next_button": 'button[aria-label="Next"]',
        }

    def _get_current_uploader_type(self, page: Page, business_title: str) -> str:
        """
        Analyzes the currently visible photo in the viewer and determines if the
        uploader is the Owner or a Customer.
        """
        try:
            uploader_link = page.locator(self.SELECTORS["uploader_link"]).last
            uploader_link.wait_for(state="visible", timeout=2500)
            uploader_name = uploader_link.inner_text()
            if business_title.strip().lower() in uploader_name.strip().lower():
                return "Owner"
            else:
                return "Customer"
        except PlaywrightTimeoutError:
            logging.warning(
                "   -> No uploader link found. Defaulting to Owner (likely a video/360 view)."  # noqa
            )
            return "Owner"

    def get_attributions_by_navigation(
        self, place_id: str, business_title: str
    ) -> List[Dict]:
        """
        Main function using the robust "click Next" strategy.
        Now constructs a direct URL using the Place ID.
        """
        direct_url = f"https://www.google.com/maps/place/?q=place_id:{place_id}"
        logging.info(f"Starting FINAL ROBUST scraper for Place ID: {place_id}")
        logging.info(f"Using direct URL: {direct_url}")

        attributions = []
        with sync_playwright() as p:
            browser = None
            try:
                browser = p.chromium.launch(
                    headless=True,  # Set to False for debugging
                    args=["--disable-blink-features=AutomationControlled"],
                )
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",  # noqa
                    viewport={"width": 1280, "height": 720},
                    locale="en-US",
                )
                page = context.new_page()
                page.route(
                    "**/*.{png,jpg,jpeg,gif,svg,woff,woff2}",
                    lambda route: route.abort(),
                )
                page.goto(direct_url, wait_until="domcontentloaded", timeout=45000)

                try:
                    logging.info("Attempting to dismiss cookie/consent banners...")
                    page.get_by_role(
                        "button",
                        name=re.compile(r"Reject all|Decline all", re.IGNORECASE),
                    ).first.click(timeout=5000)
                    logging.info("Dismissed a consent banner.")
                except PlaywrightTimeoutError:
                    logging.warning("No cookie/consent banner found to dismiss.")
                    pass

                logging.info("Waiting for the main business profile content to load...")
                page.locator('div[role="main"]').first.wait_for(
                    state="visible", timeout=20000
                )
                logging.info("Main content loaded.")

                viewer_opened_directly = False
                try:
                    logging.info("Attempt 1: Finding 'See all photos' button...")
                    page.get_by_role(
                        "button",
                        name=re.compile(
                            r"See all photos|All photos|See photos", re.IGNORECASE
                        ),
                    ).first.click(timeout=7000)
                    logging.info("'See all photos' button found and clicked.")

                except PlaywrightTimeoutError:
                    logging.warning("'See all photos' button not found.")
                    try:
                        logging.info("Attempt 2: Finding 'Photos' tab...")
                        page.get_by_role("tab", name="Photos").first.click(timeout=7000)
                        logging.info("'Photos' tab found and clicked.")
                    except PlaywrightTimeoutError:
                        logging.warning("'Photos' tab not found.")
                        logging.info("Attempt 3: Clicking the main hero image...")
                        page.locator(
                            'button[jsaction*="pane.heroHeaderImage.click"]'
                        ).first.click(timeout=10000)
                        logging.info("Main hero image found and clicked.")
                        viewer_opened_directly = True

                if not viewer_opened_directly:
                    logging.info("Entering photo viewer from gallery grid...")
                    page.locator(self.SELECTORS["first_photo_in_gallery"]).first.click(
                        timeout=10000
                    )
                else:
                    logging.info("Photo viewer was opened directly by the main image.")

                logging.info("Photo viewer is open. Starting 'Next' loop...")

                # --- IMPROVED AND MORE STABLE LOOP LOGIC ---
                for i in range(self.PHOTO_CHECK_LIMIT):
                    page.wait_for_timeout(500)  # Short pause for content to settle

                    logging.info(f"---> Analyzing photo {i+1}...")
                    uploader_type = self._get_current_uploader_type(
                        page, business_title
                    )
                    attributions.append({"uploader": uploader_type})
                    logging.info(f"   -> Classified as: {uploader_type}")

                    if i >= self.PHOTO_CHECK_LIMIT - 1:
                        logging.info("Reached photo check limit.")
                        break

                    try:
                        # First, wait for the 'Next' button to be visible.
                        next_button = page.locator(self.SELECTORS["next_button"])
                        next_button.wait_for(
                            state="visible", timeout=2500
                        )  # Wait up to 2.5s for it to appear

                        # If it is visible, check if it's enabled.
                        # If not, we're at the end.
                        if not next_button.is_enabled():
                            logging.info(
                                "'Next' button is disabled. End of gallery reached."
                            )
                            break

                        # If it's visible and enabled, click it.
                        next_button.click()

                    except PlaywrightTimeoutError:
                        # If the button never becomes visible, we've reached the end.
                        logging.info(
                            "Could not find a visible 'Next' button. Assuming end of gallery."  # noqa
                        )
                        break

            except Exception as e:
                logging.error(f"Critical error during scraping process: {e}")
                if "page" in locals() and not page.is_closed():
                    page.screenshot(path="fatal_error_screenshot.png")
            finally:
                if browser:
                    browser.close()
        logging.info("Photo scraping finished.")
        return attributions
