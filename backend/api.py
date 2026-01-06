"""
FastAPI backend for TravelAid
"""
import os
import json
import logging
from typing import Dict, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from models.review import Restaurant
from analyzers.aggregator import Aggregator
from config import PRECOMPUTED_DATA_DIR, DEFAULT_ASPECT_WEIGHTS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="TravelAid API", version="1.0.0")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SearchRequest(BaseModel):
    """Request model for search endpoint"""
    city: str
    weights: Dict[str, float] = DEFAULT_ASPECT_WEIGHTS


@app.get("/")
def root():
    """Root endpoint"""
    return {
        "name": "TravelAid API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/api/cities")
def get_cities():
    """Get list of available pre-computed cities"""
    try:
        cities = []

        if os.path.exists(PRECOMPUTED_DATA_DIR):
            for filename in os.listdir(PRECOMPUTED_DATA_DIR):
                if filename.endswith('.json'):
                    city_name = filename.replace('.json', '').replace('_', ' ').title()
                    cities.append(city_name)

        return {"cities": cities}

    except Exception as e:
        logger.error(f"Error getting cities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/search")
def search(request: SearchRequest):
    """Search restaurants with custom weights"""
    try:
        logger.info(f"Search request for: {request.city}")
        logger.info(f"Weights: {request.weights}")

        # Load pre-computed data
        city_filename = request.city.lower().replace(' ', '_').replace(',', '') + '.json'
        filepath = os.path.join(PRECOMPUTED_DATA_DIR, city_filename)

        if not os.path.exists(filepath):
            raise HTTPException(
                status_code=404,
                detail=f"No pre-computed data for {request.city}. "
                       f"Please run precompute script first."
            )

        # Load restaurant data
        with open(filepath, 'r') as f:
            data = json.load(f)

        # Convert to Restaurant objects
        restaurants = []
        for item in data:
            restaurant = Restaurant(
                name=item['name'],
                address=item.get('address', ''),
                google_rating=item.get('google_rating'),
                yelp_rating=item.get('yelp_rating'),
                tripadvisor_rating=item.get('tripadvisor_rating'),
                google_review_count=item.get('google_review_count', 0),
                yelp_review_count=item.get('yelp_review_count', 0),
                tripadvisor_review_count=item.get('tripadvisor_review_count', 0),
            )

            # Load reviews (simplified - just the analyzed aspects)
            from models.review import Review
            for review_data in item.get('reviews', []):
                review = Review(
                    text=review_data.get('text', ''),
                    rating=review_data.get('rating', 0.0),
                    source=review_data.get('source', ''),
                    aspects=review_data.get('aspects'),
                    is_suspicious=review_data.get('is_suspicious', False),
                    bias_flags=review_data.get('bias_flags', [])
                )
                restaurant.reviews.append(review)

            restaurants.append(restaurant)

        # Re-aggregate with user weights
        aggregator = Aggregator()
        aggregated_restaurants = aggregator.aggregate_multiple_restaurants(
            restaurants,
            request.weights
        )

        # Format response
        results = []
        for restaurant in aggregated_restaurants:
            results.append({
                "name": restaurant.name,
                "address": restaurant.address,
                "adjusted_rating": round(restaurant.adjusted_rating, 2),
                "confidence_interval": round(restaurant.confidence_interval, 2),
                "bias_detected": restaurant.bias_detected,
                "review_count": restaurant.total_review_count,
                "source_ratings": {
                    "google": restaurant.google_rating,
                    "yelp": restaurant.yelp_rating,
                    "tripadvisor": restaurant.tripadvisor_rating
                },
                "aspect_scores": restaurant.aspect_scores
            })

        logger.info(f"Returning {len(results)} results")

        return {"restaurants": results}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in search: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
