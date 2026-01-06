"""
Aggregation engine for calculating weighted scores and statistics
"""
import logging
import math
from typing import Dict, List
from datetime import datetime
import numpy as np
from scipy import stats
from models.review import Review, Restaurant
from config import DEFAULT_ASPECT_WEIGHTS, RECENCY_HALF_LIFE_DAYS, MIN_REVIEW_COUNT
from analyzers.bias_detector import BiasDetector

logger = logging.getLogger(__name__)


class Aggregator:
    """Aggregates reviews into weighted ratings with confidence intervals"""

    def __init__(self):
        self.bias_detector = BiasDetector()

    def aggregate_restaurant(
        self,
        restaurant: Restaurant,
        user_weights: Dict[str, float] = None
    ) -> Restaurant:
        """Calculate adjusted rating for a restaurant based on user weights"""

        if user_weights is None:
            user_weights = DEFAULT_ASPECT_WEIGHTS

        logger.info(f"Aggregating reviews for: {restaurant.name}")

        # Filter out reviews without aspect scores
        valid_reviews = [r for r in restaurant.reviews if r.aspects]

        if len(valid_reviews) < MIN_REVIEW_COUNT:
            logger.warning(
                f"  Not enough valid reviews ({len(valid_reviews)} < {MIN_REVIEW_COUNT})"
            )
            restaurant.adjusted_rating = None
            restaurant.confidence_interval = None
            return restaurant

        # Calculate aspect averages
        aspect_scores = self._calculate_aspect_averages(valid_reviews)
        restaurant.aspect_scores = aspect_scores

        # Calculate weighted scores for each review
        review_scores = []

        for review in valid_reviews:
            score = self._calculate_review_score(
                review,
                user_weights,
                today=datetime.now()
            )
            review_scores.append(score)

        # Calculate adjusted rating (mean)
        adjusted_rating = np.mean(review_scores)

        # Calculate standard error
        std_dev = np.std(review_scores, ddof=1)
        n = len(review_scores)
        standard_error = std_dev / math.sqrt(n)

        # 95% confidence interval (1.96 * SE)
        confidence_interval = 1.96 * standard_error

        restaurant.adjusted_rating = float(adjusted_rating)
        restaurant.confidence_interval = float(confidence_interval)

        logger.info(
            f"  Result: {adjusted_rating:.2f} ± {confidence_interval:.2f} "
            f"(from {n} reviews)"
        )

        return restaurant

    def _calculate_aspect_averages(self, reviews: List[Review]) -> Dict[str, float]:
        """Calculate average score for each aspect across all reviews"""
        aspect_totals = {}
        aspect_counts = {}

        for review in reviews:
            if not review.aspects:
                continue

            for aspect, score in review.aspects.items():
                if score is not None:
                    if aspect not in aspect_totals:
                        aspect_totals[aspect] = 0.0
                        aspect_counts[aspect] = 0

                    aspect_totals[aspect] += score
                    aspect_counts[aspect] += 1

        # Calculate averages
        aspect_averages = {}
        for aspect in aspect_totals:
            if aspect_counts[aspect] > 0:
                aspect_averages[aspect] = aspect_totals[aspect] / aspect_counts[aspect]
            else:
                aspect_averages[aspect] = None

        return aspect_averages

    def _calculate_review_score(
        self,
        review: Review,
        user_weights: Dict[str, float],
        today: datetime
    ) -> float:
        """Calculate weighted score for a single review"""

        # Get aspect scores
        aspects = review.aspects
        if not aspects:
            return review.rating

        # Calculate recency weight
        recency_weight = self._calculate_recency_weight(review.date, today)

        # Calculate bias penalty
        bias_penalty = self.bias_detector.calculate_bias_penalty(review)

        # Calculate weighted score
        total_weight = 0.0
        weighted_sum = 0.0

        for aspect, user_weight in user_weights.items():
            aspect_score = aspects.get(aspect)

            if aspect_score is not None and user_weight > 0:
                # Apply all weights and penalties
                effective_weight = user_weight * recency_weight * (1 - bias_penalty)

                weighted_sum += aspect_score * effective_weight
                total_weight += effective_weight

        if total_weight == 0:
            # Fallback to original rating if no valid aspects
            return review.rating

        # Normalize
        final_score = weighted_sum / total_weight

        return final_score

    def _calculate_recency_weight(
        self,
        review_date: datetime,
        today: datetime
    ) -> float:
        """Calculate recency weight using exponential decay"""

        if review_date is None:
            # If no date, use moderate weight
            return 0.7

        # Calculate days old
        days_old = (today - review_date).days

        # Exponential decay with half-life
        # weight = 0.5 ^ (days_old / half_life)
        weight = 0.5 ** (days_old / RECENCY_HALF_LIFE_DAYS)

        # Ensure minimum weight
        return max(0.1, weight)

    def aggregate_multiple_restaurants(
        self,
        restaurants: List[Restaurant],
        user_weights: Dict[str, float] = None
    ) -> List[Restaurant]:
        """Aggregate multiple restaurants and sort by adjusted rating"""

        logger.info(f"Aggregating {len(restaurants)} restaurants...")

        aggregated = []

        for restaurant in restaurants:
            # Skip if not enough reviews
            if len(restaurant.reviews) < MIN_REVIEW_COUNT:
                continue

            agg_restaurant = self.aggregate_restaurant(restaurant, user_weights)

            if agg_restaurant.adjusted_rating is not None:
                aggregated.append(agg_restaurant)

        # Sort by adjusted rating (descending)
        aggregated.sort(key=lambda r: r.adjusted_rating, reverse=True)

        logger.info(f"Aggregated {len(aggregated)} restaurants")

        return aggregated
