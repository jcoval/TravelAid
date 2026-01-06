"""
Data models for reviews and restaurants
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, List


@dataclass
class Review:
    """Individual review from a platform"""
    text: str
    rating: float  # 1-5 scale
    date: Optional[datetime] = None
    reviewer_name: Optional[str] = None
    reviewer_id: Optional[str] = None
    source: str = ""  # google, yelp, tripadvisor

    # AI-extracted aspects (populated during analysis)
    aspects: Optional[Dict[str, float]] = None  # {food_quality: 4.5, service: 3.0, ...}

    # Bias indicators
    is_suspicious: bool = False
    bias_flags: List[str] = field(default_factory=list)

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'text': self.text,
            'rating': self.rating,
            'date': self.date.isoformat() if self.date else None,
            'reviewer_name': self.reviewer_name,
            'reviewer_id': self.reviewer_id,
            'source': self.source,
            'aspects': self.aspects,
            'is_suspicious': self.is_suspicious,
            'bias_flags': self.bias_flags
        }


@dataclass
class Restaurant:
    """Restaurant with aggregated data from multiple sources"""
    name: str
    address: str = ""

    # Overall ratings per source
    google_rating: Optional[float] = None
    yelp_rating: Optional[float] = None
    tripadvisor_rating: Optional[float] = None

    # Review counts
    google_review_count: int = 0
    yelp_review_count: int = 0
    tripadvisor_review_count: int = 0

    # All collected reviews
    reviews: List[Review] = field(default_factory=list)

    # Analysis results
    adjusted_rating: Optional[float] = None
    confidence_interval: Optional[float] = None
    bias_detected: bool = False

    # Aspect averages
    aspect_scores: Optional[Dict[str, float]] = None

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'name': self.name,
            'address': self.address,
            'google_rating': self.google_rating,
            'yelp_rating': self.yelp_rating,
            'tripadvisor_rating': self.tripadvisor_rating,
            'google_review_count': self.google_review_count,
            'yelp_review_count': self.yelp_review_count,
            'tripadvisor_review_count': self.tripadvisor_review_count,
            'total_reviews': len(self.reviews),
            'reviews': [r.to_dict() for r in self.reviews],
            'adjusted_rating': self.adjusted_rating,
            'confidence_interval': self.confidence_interval,
            'bias_detected': self.bias_detected,
            'aspect_scores': self.aspect_scores
        }

    @property
    def total_review_count(self):
        """Total reviews across all sources"""
        return len(self.reviews)

    @property
    def source_ratings(self):
        """Get ratings dict for frontend"""
        return {
            'google': self.google_rating,
            'yelp': self.yelp_rating,
            'tripadvisor': self.tripadvisor_rating
        }
