"""
Google Maps scraper for restaurant reviews
"""
import logging
import re
from datetime import datetime
from typing import List, Optional
from urllib.parse import quote
from scrapers.base_scraper import BaseScraper
from models.review import Restaurant, Review

logger = logging.getLogger(__name__)


class GoogleMapsScraper(BaseScraper):
    """Scraper for Google Maps reviews"""

    BASE_URL = "https://www.google.com/maps/search/"

    def search_restaurants(self, city: str, limit: int = 100) -> List[Restaurant]:
        """Search for restaurants in a city"""
        logger.info(f"Searching Google Maps for restaurants in {city}")

        query = f"restaurants in {city}"
        search_url = f"{self.BASE_URL}{quote(query)}"

        self.page.goto(search_url)
        self.wait_for_load()
        self.random_delay()

        # Scroll to load more results
        logger.info("Scrolling to load more restaurants...")
        self.scroll_results_panel()

        # Extract restaurant links
        restaurants = self.extract_restaurant_list(limit)
        logger.info(f"Found {len(restaurants)} restaurants")

        return restaurants

    def scroll_results_panel(self, times: int = 10):
        """Scroll the results panel to load more restaurants"""
        # Google Maps has a scrollable div for results
        for i in range(times):
            try:
                # Scroll the results panel
                self.page.evaluate("""
                    const panel = document.querySelector('[role="feed"]');
                    if (panel) {
                        panel.scrollTop = panel.scrollHeight;
                    }
                """)
                self.random_delay(1, 2)
            except Exception as e:
                logger.warning(f"Error scrolling results: {e}")
                break

    def extract_restaurant_list(self, limit: int) -> List[Restaurant]:
        """Extract restaurant basic info from search results"""
        restaurants = []

        try:
            # Wait for results to load
            self.page.wait_for_selector('[role="feed"]', timeout=10000)

            # Find all restaurant links in the feed
            links = self.page.query_selector_all('a[href*="/maps/place/"]')

            for i, link in enumerate(links[:limit]):
                if i >= limit:
                    break

                try:
                    # Extract name from aria-label
                    aria_label = link.get_attribute("aria-label")
                    if not aria_label:
                        continue

                    # Parse name and rating from aria-label
                    # Format: "Restaurant Name\n4.5 stars\n123 reviews\n..."
                    name = aria_label.split('\n')[0] if '\n' in aria_label else aria_label

                    restaurant = Restaurant(name=name)
                    restaurants.append(restaurant)

                    logger.info(f"  {i+1}. {name}")

                except Exception as e:
                    logger.warning(f"Error extracting restaurant {i}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error extracting restaurant list: {e}")

        return restaurants

    def scrape_restaurant_details(self, restaurant: Restaurant) -> Restaurant:
        """Scrape detailed reviews for a restaurant"""
        logger.info(f"Scraping details for: {restaurant.name}")

        # Search for the specific restaurant
        search_url = f"{self.BASE_URL}{quote(restaurant.name)}"
        self.page.goto(search_url)
        self.wait_for_load()
        self.random_delay()

        # Click on the first result to open details
        try:
            first_result = self.page.wait_for_selector('a[href*="/maps/place/"]', timeout=5000)
            if first_result:
                first_result.click()
                self.wait_for_load()
                self.random_delay()
        except Exception as e:
            logger.warning(f"Could not open restaurant details: {e}")
            return restaurant

        # Extract overall rating and address
        restaurant.address = self.safe_get_text('button[data-item-id="address"]')

        # Try to get rating
        rating_text = self.safe_get_text('[jsaction*="pane.rating"]')
        if rating_text:
            match = re.search(r'(\d+\.?\d*)', rating_text)
            if match:
                restaurant.google_rating = float(match.group(1))

        # Get review count
        review_count_text = self.safe_get_text('button[jsaction*="pane.reviews"]')
        if review_count_text:
            match = re.search(r'([\d,]+)', review_count_text)
            if match:
                restaurant.google_review_count = int(match.group(1).replace(',', ''))

        # Click on reviews tab
        try:
            reviews_button = self.page.query_selector('button[jsaction*="pane.reviews"]')
            if reviews_button:
                reviews_button.click()
                self.random_delay(2, 3)

                # Scroll to load more reviews
                self.scroll_reviews_panel()

                # Extract reviews
                restaurant.reviews = self.extract_reviews()
                logger.info(f"  Extracted {len(restaurant.reviews)} reviews")

        except Exception as e:
            logger.warning(f"Error accessing reviews: {e}")

        return restaurant

    def scroll_reviews_panel(self, times: int = 5):
        """Scroll reviews panel to load more reviews"""
        for i in range(times):
            try:
                self.page.evaluate("""
                    const panel = document.querySelector('[role="feed"]');
                    if (panel) {
                        panel.scrollTop = panel.scrollHeight;
                    }
                """)
                self.random_delay(1, 2)
            except Exception as e:
                logger.warning(f"Error scrolling reviews: {e}")
                break

    def extract_reviews(self) -> List[Review]:
        """Extract individual reviews from current page"""
        reviews = []

        try:
            # Find all review elements
            review_elements = self.page.query_selector_all('[data-review-id]')

            for element in review_elements:
                try:
                    # Extract review text
                    text_element = element.query_selector('.wiI7pd')
                    text = text_element.inner_text().strip() if text_element else ""

                    # Skip empty reviews
                    if not text:
                        continue

                    # Extract rating (count stars)
                    rating_element = element.query_selector('[role="img"][aria-label*="star"]')
                    rating = 0.0
                    if rating_element:
                        aria_label = rating_element.get_attribute("aria-label")
                        match = re.search(r'(\d+)', aria_label)
                        if match:
                            rating = float(match.group(1))

                    # Extract reviewer name
                    name_element = element.query_selector('.d4r55')
                    reviewer_name = name_element.inner_text().strip() if name_element else "Anonymous"

                    # Extract date (relative like "3 months ago")
                    date_element = element.query_selector('.rsqaWe')
                    date_text = date_element.inner_text().strip() if date_element else ""

                    review = Review(
                        text=text,
                        rating=rating,
                        reviewer_name=reviewer_name,
                        source="google"
                    )

                    reviews.append(review)

                except Exception as e:
                    logger.debug(f"Error extracting individual review: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error extracting reviews: {e}")

        return reviews
