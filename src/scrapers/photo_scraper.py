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
            "see_photos_button": [
                'button:has-text("See photos")',
                'button:has-text("All photos")',
            ],
            # This is only used to click the very first photo to enter the viewer
            "first_photo_in_gallery": ['a[aria-label*="Photo"]'],
            # This is the uploader's name, which is always a link
            "uploader_link": ['a[href*="/contrib/"]'],
            # The "Next" button inside the photo viewer
            "next_button": ['button[aria-label="Next"]'],
        }

    def _get_current_uploader_type(self, page: Page, business_title: str) -> str:
        """
        Analyzes the currently visible photo in the viewer and determines if the
        uploader is the Owner or a Customer.
        """
        try:
            # Wait for the uploader link to be present. Use a short timeout.
            # We use .last because sometimes the business name appears twice.
            uploader_link = page.locator(self.SELECTORS["uploader_link"][0]).last
            uploader_link.wait_for(state="visible", timeout=2500)
            uploader_name = uploader_link.inner_text()

            # The core logic: if the uploader's name matches the business,
            # it's the Owner.
            if business_title.strip().lower() in uploader_name.strip().lower():
                return "Owner"
            else:
                return "Customer"
        except PlaywrightTimeoutError:
            # If no link is found, it's likely a video or other media.
            # We safely classify these as "Owner".
            logging.warning(
                "   -> No uploader link found. Defaulting to Owner (likely a video/360 view)."  # noqa
            )
            return "Owner"

    def get_attributions_by_navigation(
        self, search_url: str, business_title: str
    ) -> List[Dict]:
        """
        Main function using the robust "click Next" strategy.
        """
        logging.info(f"Starting FINAL ROBUST scraper for: {search_url}")
        attributions = []
        with sync_playwright() as p:
            browser = None
            try:
                browser = p.chromium.launch(
                    headless=True,
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
                page.goto(search_url, wait_until="domcontentloaded", timeout=30000)

                # Standard navigation to get to the photo gallery
                try:
                    page.locator('button:has-text("Reject all")').first.click(
                        timeout=5000
                    )
                except Exception:
                    pass
                try:
                    page.locator('div[role="feed"]').wait_for(
                        state="visible", timeout=5000
                    )
                    page.get_by_role(
                        "link", name=re.compile(business_title, re.IGNORECASE)
                    ).first.click()
                except Exception:
                    pass
                page.wait_for_selector(
                    'div[role="main"]', state="visible", timeout=15000
                )

                # --- The New, Simplified Process ---

                # 1. Enter the photo gallery
                page.locator(self.SELECTORS["see_photos_button"][0]).first.click()

                # 2. Click the VERY FIRST photo to open the viewer modal
                page.locator(self.SELECTORS["first_photo_in_gallery"][0]).first.click(
                    timeout=10000
                )

                logging.info("Photo viewer opened. Starting 'Next' loop...")

                # 3. Loop by clicking the "Next" button, never returning to the gallery
                for i in range(self.PHOTO_CHECK_LIMIT):
                    # A hard pause is the most reliable way to wait for content to load
                    page.wait_for_timeout(750)

                    logging.info(f"---> Analyzing photo {i+1}...")

                    # Get the uploader of the CURRENTLY visible photo
                    uploader_type = self._get_current_uploader_type(
                        page, business_title
                    )
                    attributions.append({"uploader": uploader_type})
                    logging.info(f"   -> Classified as: {uploader_type}")

                    # Check if we are on the last photo
                    if i >= self.PHOTO_CHECK_LIMIT - 1:
                        logging.info("Reached photo check limit.")
                        break

                    # Find and click the "Next" button to proceed
                    next_button = page.locator(self.SELECTORS["next_button"][0])

                    # If the "Next" button is disabled, we're at the end of the gallery
                    if not next_button.is_enabled(timeout=2000):
                        logging.info(
                            "'Next' button is disabled. End of gallery reached."
                        )
                        break

                    next_button.click()

            except Exception as e:
                logging.error(f"Critical error during scraping process: {e}")
                if "page" in locals():
                    page.screenshot(path="fatal_error_screenshot.png")
            finally:
                if browser:
                    browser.close()
        logging.info("Photo scraping finished.")
        return attributions
