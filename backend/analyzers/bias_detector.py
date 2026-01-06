"""
Bias detection for identifying fake or managed reviews
"""
import logging
from typing import List, Dict
from collections import defaultdict
from datetime import datetime, timedelta
import numpy as np
from models.review import Review, Restaurant
from config import CROSS_PLATFORM_VARIANCE_THRESHOLD
from analyzers.review_analyzer import ReviewAnalyzer

logger = logging.getLogger(__name__)


class BiasDetector:
    """Detects fake or managed reviews using multiple signals"""

    def __init__(self):
        self.review_analyzer = ReviewAnalyzer()

    def detect_bias(self, restaurant: Restaurant) -> Restaurant:
        """Run all bias detection methods on a restaurant"""
        logger.info(f"Running bias detection for: {restaurant.name}")

        # 1. Cross-platform variance
        cross_platform_bias = self.detect_cross_platform_variance(restaurant)

        # 2. Timing analysis (if we have dates)
        timing_bias = self.detect_timing_anomalies(restaurant)

        # 3. Language patterns using AI
        language_bias = self.detect_language_patterns(restaurant)

        # Aggregate bias signals
        restaurant.bias_detected = (
            cross_platform_bias or
            timing_bias or
            language_bias
        )

        logger.info(f"  Bias detected: {restaurant.bias_detected}")

        return restaurant

    def detect_cross_platform_variance(self, restaurant: Restaurant) -> bool:
        """Detect if ratings vary significantly across platforms"""
        ratings = []

        if restaurant.google_rating:
            ratings.append(restaurant.google_rating)
        if restaurant.yelp_rating:
            ratings.append(restaurant.yelp_rating)
        if restaurant.tripadvisor_rating:
            ratings.append(restaurant.tripadvisor_rating)

        if len(ratings) < 2:
            return False

        # Calculate variance
        variance = np.max(ratings) - np.min(ratings)

        if variance > CROSS_PLATFORM_VARIANCE_THRESHOLD:
            logger.warning(
                f"  Cross-platform variance detected: "
                f"Google={restaurant.google_rating}, "
                f"Yelp={restaurant.yelp_rating}, "
                f"TripAdvisor={restaurant.tripadvisor_rating} "
                f"(variance={variance:.2f})"
            )

            # Flag suspicious reviews
            for review in restaurant.reviews:
                if variance > CROSS_PLATFORM_VARIANCE_THRESHOLD:
                    review.bias_flags.append("cross_platform_variance")
                    review.is_suspicious = True

            return True

        return False

    def detect_timing_anomalies(self, restaurant: Restaurant) -> bool:
        """Detect suspicious timing patterns (review spikes)"""
        # Group reviews by date
        reviews_with_dates = [r for r in restaurant.reviews if r.date]

        if len(reviews_with_dates) < 10:
            return False  # Not enough data

        # Count reviews by week
        weekly_counts = defaultdict(int)

        for review in reviews_with_dates:
            # Get week number
            week = review.date.isocalendar()[1]
            year = review.date.year
            key = f"{year}-W{week}"
            weekly_counts[key] += 1

        if not weekly_counts:
            return False

        # Calculate average and look for spikes
        avg_per_week = len(reviews_with_dates) / len(weekly_counts)
        max_week_count = max(weekly_counts.values())

        # If more than 50% of reviews came in a single week, it's suspicious
        if max_week_count > len(reviews_with_dates) * 0.5:
            logger.warning(
                f"  Timing anomaly detected: {max_week_count} reviews in one week "
                f"(avg={avg_per_week:.1f})"
            )

            # Flag reviews from that week
            suspicious_week = max(weekly_counts, key=weekly_counts.get)

            for review in reviews_with_dates:
                week = review.date.isocalendar()[1]
                year = review.date.year
                key = f"{year}-W{week}"

                if key == suspicious_week:
                    review.bias_flags.append("timing_spike")
                    review.is_suspicious = True

            return True

        return False

    def detect_language_patterns(self, restaurant: Restaurant) -> bool:
        """Detect generic/repetitive language using AI"""
        suspicious_count = 0

        # Sample up to 20 reviews for language analysis (to save API costs)
        sample_size = min(20, len(restaurant.reviews))
        sample_reviews = restaurant.reviews[:sample_size]

        for review in sample_reviews:
            # Skip very short reviews
            if len(review.text) < 20:
                continue

            # Use AI to detect bias
            bias_result = self.review_analyzer.detect_language_bias(review.text)

            if bias_result.get("is_suspicious", False):
                confidence = bias_result.get("confidence", 0.0)

                if confidence > 0.6:  # High confidence
                    review.bias_flags.append("suspicious_language")
                    review.is_suspicious = True
                    suspicious_count += 1

                    reasons = bias_result.get("reasons", [])
                    logger.debug(f"  Suspicious language: {reasons}")

        # If more than 30% of sampled reviews are suspicious, flag the restaurant
        if suspicious_count > sample_size * 0.3:
            logger.warning(
                f"  Language bias detected: {suspicious_count}/{sample_size} "
                f"reviews have suspicious patterns"
            )
            return True

        return False

    def calculate_bias_penalty(self, review: Review) -> float:
        """Calculate bias penalty for a review (0.0 to 1.0)"""
        if not review.is_suspicious:
            return 0.0

        # Base penalty
        penalty = 0.3

        # Increase penalty based on number of bias flags
        penalty += len(review.bias_flags) * 0.15

        # Cap at 0.8 (never completely discard a review)
        return min(0.8, penalty)
