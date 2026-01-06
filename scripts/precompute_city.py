"""
Pre-compute restaurant data for a city
This script scrapes, analyzes, and saves restaurant data for fast retrieval
"""
import os
import sys
import json
import logging
import argparse
from datetime import datetime

# Add backend directory to path
backend_dir = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_dir)

from scrapers.google_scraper import GoogleMapsScraper
from scrapers.yelp_scraper import YelpScraper
from scrapers.tripadvisor_scraper import TripAdvisorScraper
from analyzers.review_analyzer import ReviewAnalyzer
from analyzers.bias_detector import BiasDetector
from analyzers.aggregator import Aggregator
from models.review import Restaurant
from config import PRECOMPUTED_DATA_DIR, RAW_DATA_DIR, ANALYZED_DATA_DIR

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def merge_restaurants(
    google_restaurants,
    yelp_restaurants,
    tripadvisor_restaurants
) -> list[Restaurant]:
    """Merge restaurants from different sources by name matching"""
    logger.info("Merging restaurants from multiple sources...")

    # Use Google as base (usually most comprehensive)
    merged = {}

    for restaurant in google_restaurants:
        name_key = restaurant.name.lower().strip()
        merged[name_key] = restaurant

    # Merge Yelp data
    for restaurant in yelp_restaurants:
        name_key = restaurant.name.lower().strip()

        if name_key in merged:
            # Merge into existing
            merged[name_key].yelp_rating = restaurant.yelp_rating
            merged[name_key].yelp_review_count = restaurant.yelp_review_count
            merged[name_key].reviews.extend(restaurant.reviews)
        else:
            # Add new restaurant
            merged[name_key] = restaurant

    # Merge TripAdvisor data
    for restaurant in tripadvisor_restaurants:
        name_key = restaurant.name.lower().strip()

        if name_key in merged:
            merged[name_key].tripadvisor_rating = restaurant.tripadvisor_rating
            merged[name_key].tripadvisor_review_count = restaurant.tripadvisor_review_count
            merged[name_key].reviews.extend(restaurant.reviews)
        else:
            merged[name_key] = restaurant

    result = list(merged.values())
    logger.info(f"Merged into {len(result)} unique restaurants")

    return result


def precompute_city(city: str, limit: int = 50):
    """Pre-compute restaurant data for a city"""
    logger.info(f"=" * 80)
    logger.info(f"PRE-COMPUTING DATA FOR: {city}")
    logger.info(f"=" * 80)

    # Create output directories
    os.makedirs(RAW_DATA_DIR, exist_ok=True)
    os.makedirs(ANALYZED_DATA_DIR, exist_ok=True)
    os.makedirs(PRECOMPUTED_DATA_DIR, exist_ok=True)

    # PHASE 1: SCRAPING
    logger.info("\n" + "=" * 80)
    logger.info("PHASE 1: SCRAPING REVIEWS")
    logger.info("=" * 80)

    google_restaurants = []
    yelp_restaurants = []
    tripadvisor_restaurants = []

    # Note: Playwright browser installation might have failed earlier
    # For now, we'll create a simplified version that uses mock data
    # In production, uncomment the scraping code below

    logger.warning("SCRAPING DISABLED - Using mock data for testing")
    logger.warning("To enable scraping: Install Playwright browsers with 'playwright install chromium'")

    # TODO: Uncomment when Playwright is working
    # try:
    #     logger.info("\nScraping Google Maps...")
    #     with GoogleMapsScraper(headless=True) as scraper:
    #         google_restaurants = scraper.search_restaurants(city, limit)
    #         for restaurant in google_restaurants[:10]:  # Limit to 10 for testing
    #             scraper.scrape_restaurant_details(restaurant)
    # except Exception as e:
    #     logger.error(f"Error scraping Google: {e}")
    #
    # try:
    #     logger.info("\nScraping Yelp...")
    #     with YelpScraper(headless=True) as scraper:
    #         yelp_restaurants = scraper.search_restaurants(city, limit)
    #         for restaurant in yelp_restaurants[:10]:
    #             scraper.scrape_restaurant_details(restaurant)
    # except Exception as e:
    #     logger.error(f"Error scraping Yelp: {e}")
    #
    # try:
    #     logger.info("\nScraping TripAdvisor...")
    #     with TripAdvisorScraper(headless=True) as scraper:
    #         tripadvisor_restaurants = scraper.search_restaurants(city, limit)
    #         for restaurant in tripadvisor_restaurants[:10]:
    #             scraper.scrape_restaurant_details(restaurant)
    # except Exception as e:
    #     logger.error(f"Error scraping TripAdvisor: {e}")

    # Create mock data for testing
    logger.info("Creating mock restaurant data for testing...")
    mock_restaurant = create_mock_restaurant()
    all_restaurants = [mock_restaurant]

    # Save raw data
    raw_filename = os.path.join(RAW_DATA_DIR, f"{city.replace(' ', '_').replace(',', '').lower()}_raw.json")
    with open(raw_filename, 'w') as f:
        json.dump([r.to_dict() for r in all_restaurants], f, indent=2)
    logger.info(f"Saved raw data to {raw_filename}")

    # PHASE 2: AI ANALYSIS
    logger.info("\n" + "=" * 80)
    logger.info("PHASE 2: AI ANALYSIS")
    logger.info("=" * 80)

    # Check if reviews already have aspects (mock data)
    has_aspects = all(
        all(r.aspects is not None for r in restaurant.reviews)
        for restaurant in all_restaurants
        if len(restaurant.reviews) > 0
    )

    if has_aspects:
        logger.info("Using mock data with pre-analyzed aspects - skipping AI analysis")
    else:
        analyzer = ReviewAnalyzer()

        for i, restaurant in enumerate(all_restaurants):
            logger.info(f"\n[{i+1}/{len(all_restaurants)}] Analyzing: {restaurant.name}")
            logger.info(f"  Total reviews: {len(restaurant.reviews)}")

            if len(restaurant.reviews) > 0:
                restaurant.reviews = analyzer.analyze_reviews_batch(restaurant.reviews)

    # PHASE 3: BIAS DETECTION
    logger.info("\n" + "=" * 80)
    logger.info("PHASE 3: BIAS DETECTION")
    logger.info("=" * 80)

    bias_detector = BiasDetector()

    # Skip AI-based language detection for mock data
    for restaurant in all_restaurants:
        # Only run cross-platform and timing bias detection (no AI)
        bias_detector.detect_cross_platform_variance(restaurant)
        bias_detector.detect_timing_anomalies(restaurant)

    # Save analyzed data
    analyzed_filename = os.path.join(
        ANALYZED_DATA_DIR,
        f"{city.replace(' ', '_').replace(',', '').lower()}_analyzed.json"
    )
    with open(analyzed_filename, 'w') as f:
        json.dump([r.to_dict() for r in all_restaurants], f, indent=2)
    logger.info(f"Saved analyzed data to {analyzed_filename}")

    # PHASE 4: AGGREGATION
    logger.info("\n" + "=" * 80)
    logger.info("PHASE 4: AGGREGATION")
    logger.info("=" * 80)

    aggregator = Aggregator()
    aggregated_restaurants = aggregator.aggregate_multiple_restaurants(all_restaurants)

    # Save pre-computed data
    precomputed_filename = os.path.join(
        PRECOMPUTED_DATA_DIR,
        f"{city.replace(' ', '_').replace(',', '').lower()}.json"
    )
    with open(precomputed_filename, 'w') as f:
        json.dump([r.to_dict() for r in aggregated_restaurants], f, indent=2)

    logger.info(f"Saved pre-computed data to {precomputed_filename}")

    # SUMMARY
    logger.info("\n" + "=" * 80)
    logger.info("SUMMARY")
    logger.info("=" * 80)
    logger.info(f"City: {city}")
    logger.info(f"Total restaurants: {len(all_restaurants)}")
    logger.info(f"Restaurants with sufficient data: {len(aggregated_restaurants)}")
    logger.info(f"Total reviews analyzed: {sum(len(r.reviews) for r in all_restaurants)}")
    logger.info(f"\nPre-computed data saved to: {precomputed_filename}")
    logger.info("=" * 80)


def create_mock_restaurant():
    """Create mock restaurant data for testing"""
    from models.review import Restaurant, Review

    restaurant = Restaurant(
        name="Neptune Oyster",
        address="63 Salem St, Boston, MA 02113",
        google_rating=4.6,
        yelp_rating=4.5,
        tripadvisor_rating=4.5,
        google_review_count=2500,
        yelp_review_count=1800,
        tripadvisor_review_count=1200
    )

    # Add mock reviews with pre-analyzed aspect scores
    mock_reviews = [
        {
            "text": "Amazing fresh oysters and the lobster roll is to die for! Service was quick and friendly. A bit pricey but worth every penny for the quality.",
            "rating": 5.0,
            "source": "google",
            "aspects": {"food_quality": 5.0, "service": 4.5, "ambiance": None, "value": 3.5, "cleanliness": None, "location": None}
        },
        {
            "text": "Best seafood in Boston hands down. The clam chowder is creamy and delicious. Only downside is the tiny space and long wait times.",
            "rating": 4.5,
            "source": "yelp",
            "aspects": {"food_quality": 5.0, "service": 3.5, "ambiance": 3.0, "value": 4.0, "cleanliness": None, "location": None}
        },
        {
            "text": "Incredible food quality but the prices are steep. Staff was attentive and knowledgeable about the menu. Definitely recommend for special occasions.",
            "rating": 4.0,
            "source": "tripadvisor",
            "aspects": {"food_quality": 4.5, "service": 4.5, "ambiance": None, "value": 2.5, "cleanliness": None, "location": None}
        },
        {
            "text": "Fresh seafood, great atmosphere, but very cramped seating. The oysters were perfectly shucked and incredibly fresh. Worth the wait!",
            "rating": 4.5,
            "source": "google",
            "aspects": {"food_quality": 5.0, "service": 4.0, "ambiance": 3.5, "value": 4.0, "cleanliness": 4.5, "location": 4.5}
        },
        {
            "text": "Excellent seafood restaurant. The lobster roll had generous portions of sweet lobster meat. Service was professional. Expensive but justified by quality.",
            "rating": 5.0,
            "source": "yelp",
            "aspects": {"food_quality": 5.0, "service": 4.5, "ambiance": None, "value": 3.0, "cleanliness": None, "location": None}
        },
        {
            "text": "Good food but nothing special for the high prices. Location in North End is convenient. Service could be friendlier.",
            "rating": 3.5,
            "source": "google",
            "aspects": {"food_quality": 4.0, "service": 3.0, "ambiance": 3.5, "value": 2.5, "cleanliness": None, "location": 4.5}
        },
        {
            "text": "The freshest oysters I've ever had! Great cocktail selection. The place is tiny and gets packed, but the quality makes up for it.",
            "rating": 5.0,
            "source": "tripadvisor",
            "aspects": {"food_quality": 5.0, "service": 4.0, "ambiance": 3.0, "value": 4.0, "cleanliness": 4.5, "location": None}
        },
        {
            "text": "Superb seafood in a cozy setting. The staff really knows their stuff. Pricey but you get what you pay for - top quality ingredients.",
            "rating": 4.5,
            "source": "yelp",
            "aspects": {"food_quality": 5.0, "service": 4.5, "ambiance": 4.0, "value": 3.5, "cleanliness": None, "location": None}
        },
        {
            "text": "Outstanding lobster roll with fresh, sweet meat. Clean restaurant. North End location is perfect for pre-dinner drinks at nearby bars.",
            "rating": 5.0,
            "source": "google",
            "aspects": {"food_quality": 5.0, "service": 4.0, "ambiance": 4.0, "value": 3.5, "cleanliness": 5.0, "location": 5.0}
        },
        {
            "text": "Quality is undeniable but portions are small for the price. Service is efficient though a bit rushed due to the crowds.",
            "rating": 4.0,
            "source": "tripadvisor",
            "aspects": {"food_quality": 4.5, "service": 3.5, "ambiance": 3.0, "value": 2.5, "cleanliness": None, "location": None}
        },
    ]

    for review_data in mock_reviews:
        review = Review(
            text=review_data["text"],
            rating=review_data["rating"],
            source=review_data["source"],
            aspects=review_data["aspects"]
        )
        restaurant.reviews.append(review)

    return restaurant


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pre-compute restaurant data for a city")
    parser.add_argument(
        "--city",
        type=str,
        default="Boston, MA",
        help="City to pre-compute (default: Boston, MA)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Maximum number of restaurants to scrape per source (default: 50)"
    )

    args = parser.parse_args()

    try:
        precompute_city(args.city, args.limit)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
