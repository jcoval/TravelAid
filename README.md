# TravelAid - Meta-Review Aggregator

A sophisticated restaurant review analysis tool that aggregates reviews from multiple sources (Google Maps, Yelp, TripAdvisor), detects bias, and provides weighted ratings based on your preferences.

## Features

- **Multi-source scraping**: Collects reviews from Google, Yelp, and TripAdvisor
- **AI-powered analysis**: Uses Claude AI to extract aspect-based ratings (food quality, service, ambiance, value, cleanliness, location)
- **Bias detection**: Identifies fake/managed reviews using cross-platform variance and other signals
- **Custom weighting**: Slider-based interface to prioritize what matters most to you
- **Statistical confidence**: Shows adjusted ratings with confidence intervals (e.g., "4.2 ± 0.3")
- **Pre-computed data**: Fast results for supported cities

## Tech Stack

### Backend
- Python 3.11+
- Playwright (web scraping)
- Anthropic Claude API (AI analysis)
- FastAPI (REST API)
- pandas, numpy, scipy (data processing & statistics)

### Frontend
- React 18
- Vite
- Tailwind CSS

## Project Structure

```
TravelAid/
├── backend/
│   ├── scrapers/          # Web scrapers for each platform
│   ├── analyzers/         # AI analysis & bias detection
│   ├── models/            # Data models
│   ├── data/              # Raw, analyzed, and pre-computed data
│   ├── config.py          # Configuration
│   └── api.py             # FastAPI endpoints
├── frontend/
│   └── src/
│       ├── components/    # React components
│       └── App.jsx        # Main app
└── scripts/
    └── precompute_city.py # Pre-scrape & analyze a city
```

## Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- Anthropic API key (get one at https://console.anthropic.com/)

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Configure API key
# Create .env file with:
# ANTHROPIC_API_KEY=your_key_here
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## Usage

### Pre-compute a City

```bash
cd backend
source venv/bin/activate
python scripts/precompute_city.py --city "Boston, MA" --limit 100
```

This will:
1. Scrape top 100 restaurants from Google, Yelp, and TripAdvisor
2. Analyze all reviews with Claude AI
3. Detect bias
4. Save results to `backend/data/precomputed/`

### Start the Backend API

```bash
cd backend
source venv/bin/activate
python api.py
```

API will run on http://localhost:8000

### Start the Frontend

```bash
cd frontend
npm run dev
```

Frontend will run on http://localhost:5173

## API Endpoints

- `GET /api/cities` - List available pre-computed cities
- `POST /api/search` - Search with custom weights
  ```json
  {
    "city": "Boston, MA",
    "weights": {
      "food_quality": 0.8,
      "service": 0.2,
      "ambiance": 0.0,
      "value": 0.0,
      "cleanliness": 0.5,
      "location": 0.3
    }
  }
  ```

## How It Works

### 1. Data Collection
Web scrapers extract reviews from multiple platforms using Playwright (handles JavaScript-rendered content).

### 2. AI Analysis
Each review is analyzed by Claude AI to extract aspect-specific scores:
- Food quality
- Service
- Ambiance
- Value/price
- Cleanliness
- Location

### 3. Bias Detection
Multiple signals identify potentially fake or managed reviews:
- Cross-platform rating variance (>1.5 stars difference)
- Review timing patterns (spikes)
- Language analysis (generic/repetitive text)

### 4. Aggregation
Final ratings are calculated using:
```
Adjusted Score = Σ(aspect_score × user_weight × recency_weight × (1 - bias_penalty))
Standard Error = σ / √n
Confidence Interval = score ± (1.96 × SE)  [95% confidence]
```

### 5. Presentation
Results show:
- Adjusted rating based on your preferences
- Confidence interval (tighter = more reviews, more consistent)
- Bias warnings
- Source breakdown

## Configuration

Edit `backend/.env` to customize:
- `TARGET_CITY`: Default city to scrape
- `MAX_RESTAURANTS`: Number of restaurants to scrape
- `MIN_REVIEWS_PER_RESTAURANT`: Minimum review threshold
- `SCRAPER_DELAY_SECONDS`: Delay between requests (avoid rate limiting)
- `AI_MODEL`: Claude model to use
- `CROSS_PLATFORM_VARIANCE_THRESHOLD`: Bias detection sensitivity

## Development Status

**Current Phase**: MVP Development
- ✅ Project structure
- ✅ Backend infrastructure
- ✅ Frontend UI with sliders
- 🚧 Web scrapers (in progress)
- ⏳ AI analysis
- ⏳ Bias detection
- ⏳ Aggregation engine
- ⏳ API endpoints
- ⏳ Pre-computation for Boston

## Roadmap

### MVP (Current)
- Single city (Boston)
- 3 review sources
- Basic bias detection
- Slider-based weighting

### Future Enhancements
- Multiple cities
- Hotels (in addition to restaurants)
- Natural language queries
- Advanced bias detection (timing, reviewer history)
- User accounts & saved preferences
- Map view
- Mobile app

## Cost Estimates

For pre-computing 100 restaurants with ~50 reviews each:
- Scraping: Free
- AI analysis: ~$1-2 (using Claude 3.5 Haiku)

## License

Personal use project.

## Author

Built for savvy travelers who want unbiased restaurant recommendations.
