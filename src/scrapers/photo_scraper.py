# src/scrapers/photo_scraper.py

import logging
from typing import List, Dict, Optional
from playwright.sync_api import (
    sync_playwright,
    TimeoutError as PlaywrightTimeoutError,
    Locator,
    Page,
)
import re


class PhotoScraper:
    """
    THE FINAL, WORKING VERSION: Restores the successful 'Anchor Wait' strategy and
    enhances it with a robust mouse-wheel scrolling loop to handle lazy loading.
    """

    def __init__(self, check_limit: int = 100):
        self.PHOTO_CHECK_LIMIT = check_limit
        self.SELECTORS = {
            "see_photos_button": [
                'button:has-text("See photos")',
                'button:has-text("All photos")',
            ],
            "gallery_anchor": [
                "a[aria-label]"
            ],  # Our reliable anchor for all thumbnails
            "uploader_info_container": ["div.JHngof", "div.UXc6zc"],
        }

    def _try_find_element(
        self, page_or_locator: "Page|Locator", selector_key: str, timeout: int = 15000
    ) -> Optional[Locator]:
        for selector in self.SELECTORS[selector_key]:
            try:
                element = page_or_locator.locator(selector).first
                element.wait_for(state="visible", timeout=timeout)
                logging.info(
                    f"   -> Successfully found element with selector: '{selector}'"
                )
                return element
            except PlaywrightTimeoutError:
                logging.warning(
                    f"   -> Selector timed out: '{selector}'. Trying next..."
                )
        logging.error(f"   -> All selectors failed for key: '{selector_key}'")
        return None

    def get_attributions_by_navigation(
        self, search_url: str, business_title: str
    ) -> List[Dict]:
        logging.info(f"Starting FINAL Playwright scraper for: {search_url}")
        attributions = []

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True, args=["--disable-blink-features=AutomationControlled"]
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
                locale="en-US",
            )
            page = context.new_page()
            page.route(
                "**/*.{png,jpg,jpeg,gif,svg,woff,woff2}", lambda route: route.abort()
            )

            try:
                page.goto(search_url, wait_until="domcontentloaded", timeout=30000)

                try:
                    page.locator('button:has-text("Reject all")').first.click(
                        timeout=5000
                    )
                    logging.info("Consent dialog handled.")
                except PlaywrightTimeoutError:
                    logging.info("No consent dialog found.")

                try:
                    page.locator('div[role="feed"]').wait_for(
                        state="visible", timeout=5000
                    )
                    logging.info(
                        "Detected search results list. Clicking business link..."
                    )
                    page.get_by_role(
                        "link", name=re.compile(business_title, re.IGNORECASE)
                    ).first.click()
                except PlaywrightTimeoutError:
                    logging.info(
                        "Search results list not found, assuming direct navigation."
                    )

                page.wait_for_selector(
                    'div[role="main"]', state="visible", timeout=15000
                )
                logging.info("Successfully on the business profile page.")

                logging.info(
                    "Step 1: Clicking the 'See photos' button to enter the gallery..."
                )
                see_photos_button = self._try_find_element(page, "see_photos_button")
                if not see_photos_button:
                    raise Exception("Could not find 'See photos' button.")
                see_photos_button.click()

                logging.info(
                    "Step 2: Waiting for the first photo thumbnail to appear (our anchor)..."
                )
                if not self._try_find_element(page, "gallery_anchor"):
                    raise Exception("The photo gallery grid did not load.")

                # --- THE CORRECT SCROLLING LOGIC ---
                logging.info(
                    "SUCCESS! Photo gallery is loaded. Collecting thumbnails with mouse-wheel scrolling..."
                )
                thumbnails = []
                previous_count = 0
                scroll_attempts = 0

                # Loop until we hit our goal or the page stops giving us new photos.
                while (
                    len(thumbnails) < self.PHOTO_CHECK_LIMIT and scroll_attempts < 20
                ):  # Safety break
                    # Re-query all thumbnails visible on the page
                    current_thumbnails = page.locator(
                        self.SELECTORS["gallery_anchor"][0]
                    ).all()
                    thumbnails = current_thumbnails

                    # If the number of photos hasn't changed after scrolling, we're done.
                    if len(thumbnails) == previous_count and scroll_attempts > 0:
                        logging.info(
                            "No new thumbnails loaded after scroll. Collection complete."
                        )
                        break

                    previous_count = len(thumbnails)
                    logging.info(
                        f"Collected {len(thumbnails)} unique thumbnails. Scrolling down..."
                    )

                    # Simulate a user scrolling the mouse wheel down by a large amount.
                    page.mouse.wheel(0, 10000)
                    page.wait_for_timeout(2500)  # Wait for the new content to load
                    scroll_attempts += 1

                # --- EXTRACTION PHASE ---
                thumbnails = thumbnails[: self.PHOTO_CHECK_LIMIT]  # Trim to our limit
                logging.info(
                    f"Found a total of {len(thumbnails)} photo thumbnails to process."
                )

                for i, thumbnail in enumerate(thumbnails):
                    # logging.info(
                    #     f"Processing photo thumbnail {i+1}/{len(thumbnails)}..."
                    # )
                    try:
                        thumbnail.click()
                        page.wait_for_timeout(500)

                        uploader_container = self._try_find_element(
                            page, "uploader_info_container", timeout=3000
                        )
                        if uploader_container:
                            uploader_name = uploader_container.locator(
                                "span.ilzTS"
                            ).inner_text()
                            attributions.append({"uploader": uploader_name})
                            logging.info(f"   ---> Found uploader: {uploader_name}")
                        else:
                            attributions.append({"uploader": "Unknown"})
                            logging.warning(
                                "   -> Could not find uploader info for this photo."
                            )
                    except Exception as e:
                        logging.error(f"Could not process photo {i+1}. Error: {e}")
                        attributions.append({"uploader": "Error"})
            except Exception as e:
                logging.error(f"An error occurred during the scraping process: {e}")
                screenshot_path = "error_screenshot.png"
                page.screenshot(path=screenshot_path)
                logging.error(
                    f"Screenshot saved to {screenshot_path}. Please review this image for clues."
                )
            finally:
                browser.close()

        return attributions
