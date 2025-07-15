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
    ENHANCED VERSION: Adds robust error handling, proper timeouts,
    and graceful degradation to prevent the scraper from crashing
    on problematic photos.
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
            "uploader_name": [
                "span.ilzTS",
                "span.fontBodyMedium",
            ],  # Added fallback selector
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

    def _extract_uploader_name(self, uploader_container: Locator) -> str:
        """
        Extract uploader name with multiple fallback strategies.
        Returns 'Owner' if no customer name is found, 'Unknown' if extraction fails.
        """
        # Strategy 1: Try multiple selectors for uploader name
        for selector in self.SELECTORS["uploader_name"]:
            try:
                uploader_element = uploader_container.locator(selector).first
                uploader_name = uploader_element.inner_text(timeout=2000)
                if uploader_name and uploader_name.strip():
                    return uploader_name.strip()
            except PlaywrightTimeoutError:
                continue
            except Exception as e:
                logging.debug(f"Selector '{selector}' failed: {e}")
                continue

        # Strategy 2: Try to find any text content in the container
        try:
            all_text = uploader_container.inner_text(timeout=1000)
            if all_text and all_text.strip():
                # Extract first line or first meaningful text
                lines = [line.strip() for line in all_text.split("\n") if line.strip()]
                if lines:
                    return lines[0]
        except Exception as e:
            logging.debug(f"Text extraction failed: {e}")

        # Strategy 3: Check if this might be an owner photo
        try:
            # Look for owner indicators in the container
            owner_indicators = uploader_container.locator("text=Owner").count()
            if owner_indicators > 0:
                return "Owner"
        except Exception:
            pass

        # If all strategies fail, assume it's an owner photo
        logging.debug("No uploader name found - assuming Owner photo")
        return "Owner"

    def _process_single_photo(
        self, page: Page, thumbnail: Locator, photo_index: int
    ) -> Dict:
        """
        Process a single photo thumbnail with comprehensive error handling.
        Returns a dictionary with uploader info or error status.
        """
        try:
            # Click the thumbnail
            thumbnail.click(timeout=5000)
            page.wait_for_timeout(500)  # Brief pause for UI to update

            # Try to find uploader info container
            uploader_container = self._try_find_element(
                page, "uploader_info_container", timeout=3000
            )

            if uploader_container:
                uploader_name = self._extract_uploader_name(uploader_container)
                logging.info(
                    f"   ---> Photo {photo_index + 1}: Found uploader: {uploader_name}"
                )
                return {"uploader": uploader_name}
            else:
                # No uploader container found - likely an owner photo
                logging.info(
                    f"   ---> Photo {photo_index + 1}: No uploader container - assuming Owner"  # noqa
                )
                return {"uploader": "Owner"}

        except PlaywrightTimeoutError:
            logging.warning(
                f"   ---> Photo {photo_index + 1}: Timeout during processing - assuming Owner"  # noqa
            )
            return {"uploader": "Owner"}
        except Exception as e:
            logging.error(f"   ---> Photo {photo_index + 1}: Processing failed: {e}")
            return {"uploader": "Error"}

    def get_attributions_by_navigation(
        self, search_url: str, business_title: str
    ) -> List[Dict]:
        """
        Enhanced version with comprehensive error handling and graceful degradation.
        """
        logging.info(f"Starting ENHANCED Playwright scraper for: {search_url}")
        attributions = []

        with sync_playwright() as p:
            browser = None
            try:
                browser = p.chromium.launch(
                    headless=True,
                    args=["--disable-blink-features=AutomationControlled"],
                )
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",  # noqa
                    viewport={"width": 1920, "height": 1080},
                    locale="en-US",
                )
                page = context.new_page()
                page.route(
                    "**/*.{png,jpg,jpeg,gif,svg,woff,woff2}",
                    lambda route: route.abort(),
                )

                # Navigate to the page
                page.goto(search_url, wait_until="domcontentloaded", timeout=30000)

                # Handle consent dialog
                try:
                    page.locator('button:has-text("Reject all")').first.click(
                        timeout=5000
                    )
                    logging.info("Consent dialog handled.")
                except PlaywrightTimeoutError:
                    logging.info("No consent dialog found.")

                # Handle search results if present
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

                # Wait for business profile page
                page.wait_for_selector(
                    'div[role="main"]', state="visible", timeout=15000
                )
                logging.info("Successfully on the business profile page.")

                # Click "See photos" button
                logging.info(
                    "Step 1: Clicking the 'See photos' button to enter the gallery..."
                )
                see_photos_button = self._try_find_element(page, "see_photos_button")
                if not see_photos_button:
                    raise Exception("Could not find 'See photos' button.")
                see_photos_button.click()

                # Wait for gallery to load
                logging.info(
                    "Step 2: Waiting for the first photo thumbnail to appear..."
                )
                if not self._try_find_element(page, "gallery_anchor"):
                    raise Exception("The photo gallery grid did not load.")

                # Collect thumbnails with scrolling
                logging.info(
                    "SUCCESS! Photo gallery is loaded. Collecting thumbnails with mouse-wheel scrolling..."  # noqa
                )
                thumbnails = []
                previous_count = 0
                scroll_attempts = 0

                while len(thumbnails) < self.PHOTO_CHECK_LIMIT and scroll_attempts < 20:
                    try:
                        current_thumbnails = page.locator(
                            self.SELECTORS["gallery_anchor"][0]
                        ).all()
                        thumbnails = current_thumbnails

                        if len(thumbnails) == previous_count and scroll_attempts > 0:
                            logging.info(
                                "No new thumbnails loaded after scroll. Collection complete."  # noqa
                            )
                            break

                        previous_count = len(thumbnails)
                        logging.info(
                            f"Collected {len(thumbnails)} unique thumbnails. Scrolling down..."  # noqa
                        )

                        page.mouse.wheel(0, 10000)
                        page.wait_for_timeout(2500)
                        scroll_attempts += 1
                    except Exception as e:
                        logging.error(f"Error during thumbnail collection: {e}")
                        break

                # Process thumbnails
                thumbnails = thumbnails[: self.PHOTO_CHECK_LIMIT]
                logging.info(
                    f"Found a total of {len(thumbnails)} photo thumbnails to process."
                )

                for i, thumbnail in enumerate(thumbnails):
                    try:
                        result = self._process_single_photo(page, thumbnail, i)
                        attributions.append(result)
                    except Exception as e:
                        logging.error(f"Unexpected error processing photo {i+1}: {e}")
                        attributions.append({"uploader": "Error"})

                logging.info(
                    f"Photo scraping completed successfully. Processed {len(attributions)} photos."  # noqa
                )

            except Exception as e:
                logging.error(f"Critical error during scraping process: {e}")
                try:
                    screenshot_path = (
                        f"error_screenshot_{business_title.replace(' ', '_')}.png"
                    )
                    page.screenshot(path=screenshot_path)
                    logging.error(f"Screenshot saved to {screenshot_path}")
                except Exception as screenshot_error:
                    logging.error(f"Could not save screenshot: {screenshot_error}")

                # Return whatever we managed to collect
                if not attributions:
                    attributions = [{"uploader": "Error"}]

            finally:
                if browser:
                    try:
                        browser.close()
                    except Exception as e:
                        logging.error(f"Error closing browser: {e}")

        return attributions
