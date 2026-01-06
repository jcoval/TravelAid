"""
Yelp scraper for restaurant reviews
"""
import logging
import re
from typing import List
from urllib.parse import quote
from scrapers.base_scraper import BaseScraper
from models.review import Restaurant, Review

logger = logging.getLogger(__name__)


class YelpScraper(BaseScraper):
    """Scraper for Yelp reviews"""

    BASE_URL = "https://www.yelp.com"

    def search_restaurants(self, city: str, limit: int = 100) -> List[Restaurant]:
        """Search for restaurants in a city"""
        logger.info(f"Searching Yelp for restaurants in {city}")

        # Yelp search URL format
        search_url = f"{self.BASE_URL}/search?find_desc=restaurants&find_loc={quote(city)}"

        self.page.goto(search_url)
        self.wait_for_load()
        self.random_delay()

        restaurants = []

        # Extract restaurant links from search results
        try:
            # Wait for results
            self.page.wait_for_selector('[data-testid="serp-ia-card"]', timeout=10000)

            # Get all restaurant cards
            cards = self.page.query_selector_all('[data-testid="serp-ia-card"]')

            for i, card in enumerate(cards[:limit]):
                try:
                    # Extract name
                    name_element = card.query_selector('a[href*="/biz/"]')
                    if not name_element:
                        continue

                    name = name_element.inner_text().strip()
                    restaurant_url = self.BASE_URL + name_element.get_attribute("href")

                    # Extract rating
                    rating_element = card.query_selector('[role="img"][aria-label*="star rating"]')
                    rating = None
                    if rating_element:
                        aria_label = rating_element.get_attribute("aria-label")
                        match = re.search(r'(\d+\.?\d*)', aria_label)
                        if match:
                            rating = float(match.group(1))

                    # Extract review count
                    review_count = 0
                    review_count_element = card.query_selector('span[aria-label*="review"]')
                    if review_count_element:
                        aria_label = review_count_element.get_attribute("aria-label")
                        match = re.search(r'(\d+)', aria_label)
                        if match:
                            review_count = int(match.group(1))

                    restaurant = Restaurant(
                        name=name,
                        yelp_rating=rating,
                        yelp_review_count=review_count
                    )

                    restaurants.append(restaurant)
                    logger.info(f"  {i+1}. {name} ({rating}★, {review_count} reviews)")

                except Exception as e:
                    logger.warning(f"Error extracting restaurant {i}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error searching Yelp: {e}")

        logger.info(f"Found {len(restaurants)} restaurants on Yelp")
        return restaurants

    def scrape_restaurant_details(self, restaurant: Restaurant) -> Restaurant:
        """Scrape detailed reviews for a restaurant"""
        logger.info(f"Scraping Yelp reviews for: {restaurant.name}")

        # Search for the specific restaurant
        search_url = f"{self.BASE_URL}/search?find_desc={quote(restaurant.name)}"
        self.page.goto(search_url)
        self.wait_for_load()
        self.random_delay()

        # Click on the first result
        try:
            first_link = self.page.wait_for_selector('a[href*="/biz/"]', timeout=5000)
            if first_link:
                restaurant_url = self.BASE_URL + first_link.get_attribute("href")
                self.page.goto(restaurant_url)
                self.wait_for_load()
                self.random_delay()
        except Exception as e:
            logger.warning(f"Could not navigate to restaurant page: {e}")
            return restaurant

        # Extract address
        address_element = self.page.query_selector('address')
        if address_element:
            restaurant.address = address_element.inner_text().strip()

        # Extract overall rating
        rating_element = self.page.query_selector('[role="img"][aria-label*="star rating"]')
        if rating_element:
            aria_label = rating_element.get_attribute("aria-label")
            match = re.search(r'(\d+\.?\d*)', aria_label)
            if match:
                restaurant.yelp_rating = float(match.group(1))

        # Extract reviews
        reviews = self.extract_reviews()
        restaurant.reviews.extend(reviews)
        logger.info(f"  Extracted {len(reviews)} Yelp reviews")

        return restaurant

    def extract_reviews(self) -> List[Review]:
        """Extract reviews from current page"""
        reviews = []

        try:
            # Find all review elements
            review_elements = self.page.query_selector_all('[data-testid*="review"]')

            for element in review_elements:
                try:
                    # Extract review text
                    text_element = element.query_selector('p[lang]')
                    text = text_element.inner_text().strip() if text_element else ""

                    if not text:
                        # Try alternative selector
                        text_element = element.query_selector('.comment__09f24__D0cxf')
                        text = text_element.inner_text().strip() if text_element else ""

                    if not text:
                        continue

                    # Extract rating
                    rating_element = element.query_selector('[role="img"][aria-label*="star rating"]')
                    rating = 0.0
                    if rating_element:
                        aria_label = rating_element.get_attribute("aria-label")
                        match = re.search(r'(\d+)', aria_label)
                        if match:
                            rating = float(match.group(1))

                    # Extract reviewer name
                    name_element = element.query_selector('a[href*="/user_details"]')
                    reviewer_name = name_element.inner_text().strip() if name_element else "Anonymous"

                    review = Review(
                        text=text,
                        rating=rating,
                        reviewer_name=reviewer_name,
                        source="yelp"
                    )

                    reviews.append(review)

                except Exception as e:
                    logger.debug(f"Error extracting individual review: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error extracting Yelp reviews: {e}")

        return reviews
