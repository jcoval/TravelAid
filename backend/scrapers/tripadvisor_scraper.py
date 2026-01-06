"""
TripAdvisor scraper for restaurant reviews
"""
import logging
import re
from typing import List
from urllib.parse import quote
from scrapers.base_scraper import BaseScraper
from models.review import Restaurant, Review

logger = logging.getLogger(__name__)


class TripAdvisorScraper(BaseScraper):
    """Scraper for TripAdvisor reviews"""

    BASE_URL = "https://www.tripadvisor.com"

    def search_restaurants(self, city: str, limit: int = 100) -> List[Restaurant]:
        """Search for restaurants in a city"""
        logger.info(f"Searching TripAdvisor for restaurants in {city}")

        # TripAdvisor search URL
        search_url = f"{self.BASE_URL}/Search?q=restaurants+{quote(city)}"

        self.page.goto(search_url)
        self.wait_for_load()
        self.random_delay()

        restaurants = []

        try:
            # Look for restaurant results
            # TripAdvisor often shows results in different formats
            self.page.wait_for_selector('a[href*="/Restaurant_Review"]', timeout=10000)

            # Extract restaurant links
            links = self.page.query_selector_all('a[href*="/Restaurant_Review"]')

            for i, link in enumerate(links[:limit]):
                try:
                    # Extract name
                    name = link.inner_text().strip()
                    if not name:
                        continue

                    restaurant = Restaurant(name=name)
                    restaurants.append(restaurant)

                    logger.info(f"  {i+1}. {name}")

                except Exception as e:
                    logger.warning(f"Error extracting restaurant {i}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error searching TripAdvisor: {e}")

        logger.info(f"Found {len(restaurants)} restaurants on TripAdvisor")
        return restaurants

    def scrape_restaurant_details(self, restaurant: Restaurant) -> Restaurant:
        """Scrape detailed reviews for a restaurant"""
        logger.info(f"Scraping TripAdvisor reviews for: {restaurant.name}")

        # Search for the specific restaurant
        search_url = f"{self.BASE_URL}/Search?q={quote(restaurant.name)}"
        self.page.goto(search_url)
        self.wait_for_load()
        self.random_delay()

        # Click on the first restaurant result
        try:
            first_link = self.page.wait_for_selector('a[href*="/Restaurant_Review"]', timeout=5000)
            if first_link:
                first_link.click()
                self.wait_for_load()
                self.random_delay()
        except Exception as e:
            logger.warning(f"Could not navigate to restaurant page: {e}")
            return restaurant

        # Extract address
        address_element = self.page.query_selector('a[href*="/ShowUrl?"]')
        if address_element:
            # Address is often in parent element
            parent = address_element.query_selector('..')
            if parent:
                restaurant.address = parent.inner_text().strip()

        # Extract overall rating
        rating_element = self.page.query_selector('[data-test-target="review-rating"]')
        if not rating_element:
            rating_element = self.page.query_selector('.overallRating')

        if rating_element:
            rating_text = rating_element.inner_text()
            match = re.search(r'(\d+\.?\d*)', rating_text)
            if match:
                restaurant.tripadvisor_rating = float(match.group(1))

        # Extract review count
        review_count_element = self.page.query_selector('a[href*="#REVIEWS"]')
        if review_count_element:
            review_text = review_count_element.inner_text()
            match = re.search(r'([\d,]+)', review_text)
            if match:
                restaurant.tripadvisor_review_count = int(match.group(1).replace(',', ''))

        # Extract reviews
        reviews = self.extract_reviews()
        restaurant.reviews.extend(reviews)
        logger.info(f"  Extracted {len(reviews)} TripAdvisor reviews")

        return restaurant

    def extract_reviews(self) -> List[Review]:
        """Extract reviews from current page"""
        reviews = []

        try:
            # Scroll to load reviews
            self.scroll_page(3)

            # Find all review elements
            # TripAdvisor has changed selectors multiple times, try several
            review_selectors = [
                '[data-test-target="HR_CC_CARD"]',
                '.review-container',
                '.reviewSelector'
            ]

            review_elements = []
            for selector in review_selectors:
                review_elements = self.page.query_selector_all(selector)
                if review_elements:
                    break

            for element in review_elements:
                try:
                    # Extract review text
                    text = ""
                    text_selectors = [
                        '.prw_reviews_text_summary_hsx',
                        '[data-test-target="review-text"]',
                        '.partial_entry'
                    ]

                    for selector in text_selectors:
                        text_element = element.query_selector(selector)
                        if text_element:
                            text = text_element.inner_text().strip()
                            break

                    if not text:
                        continue

                    # Extract rating (bubble rating out of 5)
                    rating = 0.0
                    rating_element = element.query_selector('.ui_bubble_rating')
                    if rating_element:
                        class_name = rating_element.get_attribute('class')
                        # Class format: ui_bubble_rating bubble_50 -> 5.0 rating
                        match = re.search(r'bubble_(\d+)', class_name)
                        if match:
                            rating = int(match.group(1)) / 10.0

                    # Extract reviewer name
                    reviewer_name = "Anonymous"
                    name_selectors = [
                        '[class*="member_info"]',
                        '.info_text',
                        '[class*="username"]'
                    ]

                    for selector in name_selectors:
                        name_element = element.query_selector(selector)
                        if name_element:
                            reviewer_name = name_element.inner_text().strip()
                            break

                    review = Review(
                        text=text,
                        rating=rating,
                        reviewer_name=reviewer_name,
                        source="tripadvisor"
                    )

                    reviews.append(review)

                except Exception as e:
                    logger.debug(f"Error extracting individual review: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error extracting TripAdvisor reviews: {e}")

        return reviews
