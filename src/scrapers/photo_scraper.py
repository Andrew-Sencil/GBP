import logging
import os
from typing import List, Dict
from playwright.sync_api import (
    sync_playwright,
    TimeoutError as PlaywrightTimeoutError,
    Page,
)
import re

# --- Set up basic logging ---
# It's good practice to get the logger by name for better control in larger apps
logger = logging.getLogger(__name__)


class PhotoScraper:
    """
    Optimized for Docker: This scraper mimics human behavior by repeatedly
    clicking the 'Next' button inside the photo viewer. It's designed to be
    robust for headless execution in a containerized environment.
    """

    def __init__(self, check_limit: int = 100):
        self.PHOTO_CHECK_LIMIT = check_limit
        self.SELECTORS = {
            "first_photo_in_gallery": 'a[aria-label*="Photo"]',
            "uploader_link": 'a[href*="/contrib/"]',
            "next_button": 'button[aria-label="Next"]',
        }
        # Define an output directory for screenshots, useful within Docker
        self.output_dir = os.getenv("OUTPUT_DIR", "/app/output")
        os.makedirs(self.output_dir, exist_ok=True)

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
            logger.warning(
                "   -> No uploader link found. Defaulting to Owner (likely a video/360 view)."  # noqa
            )
            return "Owner"

    def get_attributions_by_navigation(
        self, place_id: str, business_title: str
    ) -> List[Dict]:
        """
        Main function using the robust "click Next" strategy.
        Constructs a direct URL using the Place ID for stability.
        """
        direct_url = f"https://www.google.com/maps/place/?q=place_id:{place_id}"
        logger.info(f"Starting scraper for Place ID: {place_id}")
        logger.info(f"Using direct URL: {direct_url}")

        attributions = []
        with sync_playwright() as p:
            browser = None
            try:
                # Using --no-sandbox is often necessary in Docker environments
                browser = p.chromium.launch(
                    headless=True,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--disable-dev-shm-usage",  # Recommended for Docker to prevent
                        # shared memory issues
                    ],
                )
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",  # noqa
                    viewport={"width": 1280, "height": 720},
                    locale="en-US",
                )
                page = context.new_page()

                # Aborting image/font requests is a key optimization for speed
                # and resource use
                page.route(
                    "**/*.{png,jpg,jpeg,gif,svg,woff,woff2}",
                    lambda route: route.abort(),
                )
                page.goto(direct_url, wait_until="domcontentloaded", timeout=45000)

                try:
                    logger.info("Attempting to dismiss cookie/consent banners...")
                    page.get_by_role(
                        "button",
                        name=re.compile(r"Reject all|Decline all", re.IGNORECASE),
                    ).first.click(timeout=5000)
                    logger.info("Dismissed a consent banner.")
                except PlaywrightTimeoutError:
                    logger.warning("No cookie/consent banner found to dismiss.")
                    pass

                logger.info("Waiting for the main business profile content to load...")
                page.locator('div[role="main"]').first.wait_for(
                    state="visible", timeout=20000
                )
                logger.info("Main content loaded.")

                viewer_opened_directly = False
                try:
                    page.get_by_role(
                        "button",
                        name=re.compile(
                            r"See all photos|All photos|See photos", re.IGNORECASE
                        ),
                    ).first.click(timeout=7000)
                    logger.info("'See all photos' button found and clicked.")

                except PlaywrightTimeoutError:
                    logger.warning("'See all photos' button not found.")
                    try:
                        page.get_by_role("tab", name="Photos").first.click(timeout=7000)
                        logger.info("'Photos' tab found and clicked.")
                    except PlaywrightTimeoutError:
                        logger.warning("'Photos' tab not found.")
                        page.locator(
                            'button[jsaction*="pane.heroHeaderImage.click"]'
                        ).first.click(timeout=10000)
                        logger.info("Main hero image found and clicked.")
                        viewer_opened_directly = True

                if not viewer_opened_directly:
                    logger.info("Entering photo viewer from gallery grid...")
                    page.locator(self.SELECTORS["first_photo_in_gallery"]).first.click(
                        timeout=10000
                    )
                else:
                    logger.info("Photo viewer was opened directly by the main image.")

                logger.info("Photo viewer is open. Starting 'Next' loop...")

                for i in range(self.PHOTO_CHECK_LIMIT):
                    page.wait_for_timeout(500)

                    logger.info(f"---> Analyzing photo {i+1}...")
                    uploader_type = self._get_current_uploader_type(
                        page, business_title
                    )
                    attributions.append({"uploader": uploader_type})
                    logger.info(f"   -> Classified as: {uploader_type}")

                    if i >= self.PHOTO_CHECK_LIMIT - 1:
                        logger.info("Reached photo check limit.")
                        break

                    try:
                        next_button = page.locator(self.SELECTORS["next_button"])
                        next_button.wait_for(state="visible", timeout=2500)

                        if not next_button.is_enabled():
                            logger.info(
                                "'Next' button is disabled. End of gallery reached."
                            )
                            break

                        next_button.click()

                    except PlaywrightTimeoutError:
                        logger.info(
                            "Could not find a visible 'Next' button. Assuming end of gallery."  # noqa
                        )
                        break

            except Exception as e:
                logger.error(f"Critical error during scraping process: {e}")
                if "page" in locals() and not page.is_closed():
                    screenshot_path = os.path.join(
                        self.output_dir, f"fatal_error_{place_id}.png"
                    )
                    page.screenshot(path=screenshot_path)
                    logger.info(f"Screenshot saved to {screenshot_path}")
            finally:
                if browser:
                    browser.close()
        logger.info("Photo scraping finished.")
        return attributions
