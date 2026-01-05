"""
Configuration module for TravelAid backend
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Target city
TARGET_CITY = os.getenv("TARGET_CITY", "Boston, MA")

# Scraping settings
MAX_RESTAURANTS = int(os.getenv("MAX_RESTAURANTS", "100"))
MIN_REVIEWS_PER_RESTAURANT = int(os.getenv("MIN_REVIEWS_PER_RESTAURANT", "10"))
SCRAPER_DELAY_SECONDS = int(os.getenv("SCRAPER_DELAY_SECONDS", "3"))

# AI Model settings
AI_MODEL = os.getenv("AI_MODEL", "claude-3-5-haiku-20241022")
AI_TEMPERATURE = float(os.getenv("AI_TEMPERATURE", "0.1"))

# Bias detection thresholds
CROSS_PLATFORM_VARIANCE_THRESHOLD = float(os.getenv("CROSS_PLATFORM_VARIANCE_THRESHOLD", "1.5"))
MIN_REVIEW_COUNT = int(os.getenv("MIN_REVIEW_COUNT", "10"))

# Aspect weights (default equal weighting)
DEFAULT_ASPECT_WEIGHTS = {
    "food_quality": 1.0,
    "service": 1.0,
    "ambiance": 1.0,
    "value": 1.0,
    "cleanliness": 1.0,
    "location": 1.0
}

# Data paths
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
RAW_DATA_DIR = os.path.join(DATA_DIR, "raw")
ANALYZED_DATA_DIR = os.path.join(DATA_DIR, "analyzed")
PRECOMPUTED_DATA_DIR = os.path.join(DATA_DIR, "precomputed")

# Recency weighting (half-life in days)
RECENCY_HALF_LIFE_DAYS = 180  # 6 months

# User agent for scraping
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
