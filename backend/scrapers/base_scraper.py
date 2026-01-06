"""
Base scraper with common utilities for web scraping
"""
import time
import random
import logging
from typing import Optional
from playwright.sync_api import sync_playwright, Page, Browser
from config import USER_AGENT, SCRAPER_DELAY_SECONDS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseScraper:
    """Base class for all scrapers with common functionality"""

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None

    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()

    def start(self):
        """Initialize browser"""
        logger.info("Starting browser...")
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=self.headless)
        self.page = self.browser.new_page(user_agent=USER_AGENT)
        logger.info("Browser started successfully")

    def stop(self):
        """Close browser"""
        if self.page:
            self.page.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        logger.info("Browser stopped")

    def random_delay(self, min_seconds: float = None, max_seconds: float = None):
        """Random delay to avoid rate limiting"""
        if min_seconds is None:
            min_seconds = SCRAPER_DELAY_SECONDS
        if max_seconds is None:
            max_seconds = SCRAPER_DELAY_SECONDS + 2

        delay = random.uniform(min_seconds, max_seconds)
        logger.debug(f"Waiting {delay:.2f} seconds...")
        time.sleep(delay)

    def safe_get_text(self, selector: str, default: str = "") -> str:
        """Safely extract text from element"""
        try:
            element = self.page.query_selector(selector)
            if element:
                return element.inner_text().strip()
        except Exception as e:
            logger.debug(f"Error getting text from {selector}: {e}")
        return default

    def safe_get_attribute(self, selector: str, attribute: str, default: str = "") -> str:
        """Safely extract attribute from element"""
        try:
            element = self.page.query_selector(selector)
            if element:
                value = element.get_attribute(attribute)
                return value.strip() if value else default
        except Exception as e:
            logger.debug(f"Error getting attribute {attribute} from {selector}: {e}")
        return default

    def scroll_page(self, times: int = 3):
        """Scroll page to load dynamic content"""
        for i in range(times):
            self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(1)

    def wait_for_load(self, timeout: int = 10000):
        """Wait for page to load"""
        try:
            self.page.wait_for_load_state("networkidle", timeout=timeout)
        except Exception as e:
            logger.warning(f"Page load timeout: {e}")
