"""
AI-powered review analyzer using Claude API
"""
import logging
import json
from typing import List, Dict, Optional
from anthropic import Anthropic
from models.review import Review
from config import ANTHROPIC_API_KEY, AI_MODEL, AI_TEMPERATURE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ReviewAnalyzer:
    """Analyzes reviews using Claude AI to extract aspect-based scores"""

    ASPECTS = [
        "food_quality",
        "service",
        "ambiance",
        "value",
        "cleanliness",
        "location"
    ]

    def __init__(self):
        import os
        # Clear any proxy settings that might interfere
        env_vars_to_clear = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']
        for var in env_vars_to_clear:
            if var in os.environ:
                del os.environ[var]

        self.client = Anthropic(api_key=ANTHROPIC_API_KEY)
        self.model = AI_MODEL

    def analyze_review(self, review: Review) -> Review:
        """Analyze a single review to extract aspect scores"""
        try:
            prompt = self._build_prompt(review.text, review.rating)
            response = self.client.messages.create(
                model=self.model,
                max_tokens=500,
                temperature=AI_TEMPERATURE,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # Parse JSON response
            response_text = response.content[0].text.strip()
            aspects = self._parse_response(response_text)

            review.aspects = aspects
            logger.debug(f"Analyzed review: {aspects}")

        except Exception as e:
            logger.error(f"Error analyzing review: {e}")
            # Set default aspects on error
            review.aspects = {aspect: None for aspect in self.ASPECTS}

        return review

    def analyze_reviews_batch(self, reviews: List[Review], batch_size: int = 10) -> List[Review]:
        """Analyze multiple reviews in batches for efficiency"""
        logger.info(f"Analyzing {len(reviews)} reviews...")

        analyzed_reviews = []

        for i in range(0, len(reviews), batch_size):
            batch = reviews[i:i+batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}/{(len(reviews)-1)//batch_size + 1}")

            for review in batch:
                analyzed_review = self.analyze_review(review)
                analyzed_reviews.append(analyzed_review)

        logger.info(f"Completed analyzing {len(analyzed_reviews)} reviews")
        return analyzed_reviews

    def _build_prompt(self, review_text: str, overall_rating: float) -> str:
        """Build the prompt for Claude API"""
        return f"""Analyze this restaurant review and extract scores (1-5) for specific aspects. If an aspect is not mentioned in the review, return null for that aspect.

Review: "{review_text}"
Overall Rating: {overall_rating}/5

Extract scores for these aspects:
- food_quality: How good is the food? Quality, taste, freshness
- service: How is the staff/service? Friendliness, attentiveness, speed
- ambiance: Atmosphere, decor, noise level, comfort
- value: Price vs quality (value for money)
- cleanliness: Hygiene, cleanliness of restaurant
- location: Convenience, accessibility, parking, neighborhood

Return ONLY a JSON object in this exact format (no other text):
{{
  "food_quality": <number 1-5 or null>,
  "service": <number 1-5 or null>,
  "ambiance": <number 1-5 or null>,
  "value": <number 1-5 or null>,
  "cleanliness": <number 1-5 or null>,
  "location": <number 1-5 or null>
}}

Example response:
{{"food_quality": 4.5, "service": 3.0, "ambiance": 4.0, "value": 3.5, "cleanliness": null, "location": 4.0}}"""

    def _parse_response(self, response_text: str) -> Dict[str, Optional[float]]:
        """Parse Claude's JSON response"""
        try:
            # Try to extract JSON from response
            # Sometimes Claude adds extra text, so find the JSON object
            start = response_text.find('{')
            end = response_text.rfind('}') + 1

            if start == -1 or end == 0:
                raise ValueError("No JSON object found in response")

            json_str = response_text[start:end]
            aspects = json.loads(json_str)

            # Validate and clean
            result = {}
            for aspect in self.ASPECTS:
                value = aspects.get(aspect)
                if value is not None:
                    # Ensure it's a float and within range
                    value = float(value)
                    value = max(1.0, min(5.0, value))  # Clamp to 1-5
                result[aspect] = value

            return result

        except Exception as e:
            logger.error(f"Error parsing response: {e}\nResponse: {response_text}")
            # Return all None on error
            return {aspect: None for aspect in self.ASPECTS}

    def detect_language_bias(self, review_text: str) -> Dict[str, any]:
        """Use AI to detect if review language seems fake or biased"""
        try:
            prompt = f"""Analyze this restaurant review for signs of being fake, managed, or biased.

Review: "{review_text}"

Look for:
1. Generic/template language ("great experience", "highly recommend" without specifics)
2. Overly promotional tone
3. Lack of specific details
4. Repetitive phrases
5. Unnatural language

Return ONLY a JSON object:
{{
  "is_suspicious": <true or false>,
  "confidence": <0.0 to 1.0>,
  "reasons": ["reason1", "reason2"]
}}"""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=300,
                temperature=AI_TEMPERATURE,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            response_text = response.content[0].text.strip()

            # Parse JSON
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            json_str = response_text[start:end]
            result = json.loads(json_str)

            return result

        except Exception as e:
            logger.error(f"Error detecting language bias: {e}")
            return {
                "is_suspicious": False,
                "confidence": 0.0,
                "reasons": []
            }
