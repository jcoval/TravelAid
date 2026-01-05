# TravelAid - Meta-Review Aggregator Implementation Plan

## Project Overview

**Goal**: Build a web app that analyzes restaurant and hotel reviews from multiple sources (Google, Yelp, TripAdvisor) to provide bias-adjusted ratings with confidence intervals, weighted by user-specified criteria.

**Target Users**: Savvy solo and family travelers doing international travel research

**Key Differentiators**:
- Aspect-based weighting (e.g., prioritize food quality over service)
- Bias detection across multiple review platforms
- Statistical confidence intervals on ratings
- Cross-platform meta-analysis

---

## System Architecture

### 1. Data Collection Layer (Web Scraping)
**Purpose**: Gather reviews from multiple sources

**Components**:
- `GoogleScraper`: Scrape Google Maps reviews
- `TripAdvisorScraper`: Scrape TripAdvisor reviews
- `YelpScraper`: Scrape Yelp reviews
- `BaseScraper`: Shared scraping utilities

**Technology**: Playwright (handles JavaScript-rendered content)

**Output**: Raw review data (text, rating, date, reviewer info)

---

### 2. Analysis Layer (AI/NLP)
**Purpose**: Extract structured insights from unstructured review text

**Components**:
- `ReviewAnalyzer`: Uses LLM to extract aspects and sentiment
  - Aspects: food_quality, service, ambiance, value, cleanliness, location
  - Per-aspect sentiment scores (1-5 scale)
- `BiasDetector`: Identifies fake/managed reviews
  - Cross-platform rating variance
  - Timing anomalies (review spikes)
  - Language patterns (generic/repetitive text)
  - Reviewer credibility (new accounts, single reviews)

**Technology**: OpenAI API or Anthropic Claude API

**Output**: Structured review data with aspect scores and bias flags

---

### 3. Aggregation Layer
**Purpose**: Compute adjusted ratings based on user preferences

**Components**:
- `Aggregator`: Calculates weighted scores
  - Applies user-defined weights to aspects
  - Adjusts for detected bias
  - Weights recent reviews more heavily
  - Computes standard error and confidence intervals
  - Requires minimum review threshold

**Formulas**:
```
Adjusted Score = Σ(aspect_score × user_weight × recency_weight × (1 - bias_penalty))
Standard Error = σ / √n  (where σ = standard deviation, n = review count)
Confidence Interval = score ± (1.96 × SE)  [95% confidence]
```

**Output**: Final ratings with confidence metrics

---

### 4. Presentation Layer (Web UI)
**Purpose**: User interface for searching and customizing results

**Features**:
- City/location search input
- Restaurant/hotel category toggle
- Slider controls for aspect weights:
  - Food Quality: [0-100%]
  - Service: [0-100%]
  - Ambiance: [0-100%]
  - Value/Price: [0-100%]
  - Cleanliness: [0-100%]
  - Location: [0-100%]
- Results display:
  - Name, address, overall adjusted rating
  - Confidence interval (e.g., "4.2 ± 0.3")
  - Bias indicators (if detected)
  - Source breakdown (Google: 4.1, Yelp: 4.5, TripAdvisor: 3.9)
  - Review count per source
- Sort/filter options

**Technology**: React + Vite (fast, modern) OR vanilla HTML/JS (simpler)

---

## Tech Stack

### Backend
- **Language**: Python 3.11+
- **Web Scraping**: Playwright
- **AI/NLP**: OpenAI API (gpt-4o-mini for cost efficiency) or Anthropic Claude
- **API Framework**: FastAPI (modern, async) or Flask (simpler)
- **Data Storage**: SQLite (structured data) + JSON (pre-computed results)
- **Data Processing**: pandas, numpy, scipy (statistics)

### Frontend
- **Framework**: React 18 + Vite
- **Styling**: Tailwind CSS (rapid UI development)
- **State Management**: React hooks (useState, useEffect)
- **HTTP Client**: fetch API or axios

### Development Tools
- **Environment**: Python venv
- **Package Management**: pip (backend), npm (frontend)
- **Version Control**: git

---

## Project Structure

```
TravelAid/
├── backend/
│   ├── scrapers/
│   │   ├── __init__.py
│   │   ├── base_scraper.py          # Shared scraping utilities
│   │   ├── google_scraper.py        # Google Maps scraper
│   │   ├── tripadvisor_scraper.py   # TripAdvisor scraper
│   │   └── yelp_scraper.py          # Yelp scraper
│   ├── analyzers/
│   │   ├── __init__.py
│   │   ├── review_analyzer.py       # AI-powered aspect extraction
│   │   ├── bias_detector.py         # Fake review detection
│   │   └── aggregator.py            # Weighted scoring & statistics
│   ├── models/
│   │   ├── __init__.py
│   │   ├── restaurant.py            # Data models
│   │   └── review.py
│   ├── data/
│   │   ├── raw/                     # Raw scraped data
│   │   ├── analyzed/                # AI-analyzed reviews
│   │   └── precomputed/             # Final aggregated data
│   ├── api.py                       # FastAPI/Flask endpoints
│   ├── config.py                    # Configuration & constants
│   ├── requirements.txt             # Python dependencies
│   └── .env                         # API keys (gitignored)
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   │   ├── SearchBar.jsx
│   │   │   ├── WeightSliders.jsx
│   │   │   ├── ResultsList.jsx
│   │   │   └── RestaurantCard.jsx
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── scripts/
│   ├── precompute_city.py           # Pre-scrape & analyze a city
│   └── test_scraper.py              # Test individual scrapers
├── .gitignore
├── README.md
└── IMPLEMENTATION_PLAN.md (this file)
```

---

## Implementation Phases

### Phase 1: Setup & Infrastructure (Day 1)
**Goal**: Get development environment ready

1. ✅ Create project structure
2. Set up Python virtual environment
3. Install backend dependencies (playwright, openai/anthropic, fastapi, etc.)
4. Set up frontend (React + Vite)
5. Create configuration files (.env template, .gitignore)
6. Initialize data directories

**Validation**: Run `python --version`, `npm --version`, install Playwright browsers

---

### Phase 2: Web Scraping (Days 2-3)
**Goal**: Collect raw review data from multiple sources

7. Implement `base_scraper.py` with common utilities
8. Implement `google_scraper.py`
   - Search for restaurants in a city
   - Extract name, address, rating, review count
   - Scrape individual reviews (text, rating, date, reviewer)
9. Implement `yelp_scraper.py`
10. Implement `tripadvisor_scraper.py`
11. Create test script to scrape 10 sample restaurants
12. Store raw data in JSON format

**Validation**: Successfully scrape 10 restaurants from one city (e.g., "Paris, France") with 20+ reviews each from each platform

**Challenges**:
- Rate limiting (add delays between requests)
- Anti-bot detection (use realistic user agents, randomize delays)
- Dynamic content loading (Playwright handles this)
- Inconsistent HTML structure across sites (robust selectors needed)

---

### Phase 3: AI Analysis (Days 4-5)
**Goal**: Extract structured insights from review text

13. Design AI prompt for aspect extraction
    - Input: Review text + overall rating
    - Output: JSON with aspect scores (food_quality, service, ambiance, value, cleanliness, location)
14. Implement `review_analyzer.py`
    - Batch reviews to minimize API calls
    - Parse AI responses into structured format
    - Handle API errors gracefully
15. Test on sample reviews
16. Fine-tune prompt for accuracy

**Sample Prompt**:
```
Analyze this restaurant review and extract scores (1-5) for these aspects:
- food_quality: How good is the food?
- service: How is the staff/service?
- ambiance: Atmosphere, decor, noise level
- value: Price vs quality (value for money)
- cleanliness: Hygiene, cleanliness
- location: Convenience, accessibility

Review: "[review text]"
Overall Rating: [X/5]

Return JSON: {"food_quality": X, "service": X, ...}
If an aspect isn't mentioned, return null.
```

**Validation**: Analyze 50 reviews, manually verify 10 for accuracy

---

### Phase 4: Bias Detection & Aggregation (Days 6-7)
**Goal**: Identify fake reviews and compute adjusted ratings

17. Implement cross-platform variance detection
    - Flag establishments with >1.5 star difference between platforms
18. Implement timing analysis
    - Detect review spikes (>30% of reviews in short period)
19. Implement language pattern detection
    - Use AI to identify generic/repetitive phrasing
    - Flag reviews with suspiciously similar wording
20. Implement `aggregator.py`
    - Calculate weighted average based on user weights
    - Apply recency weighting (exponential decay)
    - Apply bias penalty for flagged reviews
    - Compute standard error and confidence intervals
    - Filter out establishments with <10 total reviews

**Formulas**:
```python
# Recency weight (half-life = 6 months)
days_old = (today - review_date).days
recency_weight = 0.5 ** (days_old / 180)

# Bias penalty
bias_penalty = 0.5 if flagged else 0.0

# Weighted score
weighted_score = sum(
    aspect_scores[aspect] * user_weights[aspect] * recency_weight * (1 - bias_penalty)
    for aspect in aspects
) / sum(user_weights.values())

# Standard error
SE = stdev(individual_scores) / sqrt(len(individual_scores))
```

**Validation**: Test on 10 restaurants with known characteristics (e.g., one with fake reviews, one highly rated, one controversial)

---

### Phase 5: Web Interface (Days 8-9)
**Goal**: Build user-facing application

21. Set up React + Vite project
22. Create `SearchBar` component (city input)
23. Create `WeightSliders` component (6 sliders for aspects)
24. Create `ResultsList` and `RestaurantCard` components
    - Display: name, address, adjusted rating
    - Display: confidence interval (e.g., "4.2 ± 0.3")
    - Display: bias flags ("⚠️ Possible bias detected")
    - Display: source breakdown (expandable)
25. Add sort/filter options (by rating, confidence, review count)
26. Style with Tailwind CSS

**Validation**: UI is functional and displays mock data correctly

---

### Phase 6: Backend API (Day 10)
**Goal**: Connect frontend to data

27. Implement FastAPI endpoints:
    - `GET /api/cities` - List available pre-computed cities
    - `POST /api/search` - Search with user weights
      - Body: `{city, weights: {food_quality: 0.8, service: 0.2, ...}}`
      - Response: List of restaurants with adjusted ratings
28. Serve pre-computed data from `backend/data/precomputed/`
29. Enable CORS for frontend-backend communication

**Validation**: Frontend successfully fetches and displays data from backend

---

### Phase 7: Integration & Pre-computation (Days 11-12)
**Goal**: Run full pipeline on a test city

30. Create `precompute_city.py` script:
    - Input: city name (e.g., "Paris, France")
    - Steps:
      1. Scrape top 50-100 restaurants from each source
      2. Analyze all reviews with AI
      3. Detect bias
      4. Save to `backend/data/precomputed/paris.json`
31. Run pre-computation for one test city
32. Validate results:
    - Spot-check 5 restaurants manually
    - Verify bias detection is working
    - Ensure confidence intervals make sense
33. Test full user workflow:
    - User adjusts sliders → sees re-ranked results
    - User clicks on restaurant → sees detail view

**Validation**: End-to-end system works for one city

---

### Phase 8: Refinement & Documentation (Day 13+)
**Goal**: Polish and prepare for use

34. Add error handling throughout
35. Improve scraper resilience (retry logic, better selectors)
36. Optimize AI prompts for accuracy and cost
37. Add loading states in UI
38. Write README with setup instructions
39. Document API keys needed (.env template)
40. Add sample screenshots

**Validation**: Another person (or you on a fresh machine) can set it up and use it

---

## MVP Scope for Initial "Does It Work?" Test

**Minimum Viable Product**:
- ✅ Single city (pick one: Paris, Tokyo, New York)
- ✅ 3 review sources (Google, Yelp, TripAdvisor)
- ✅ Restaurants only (not hotels yet)
- ✅ 6 aspects (food, service, ambiance, value, cleanliness, location)
- ✅ Basic bias detection (cross-platform variance only)
- ✅ Slider-based weighting
- ✅ Results with confidence intervals
- ✅ Web UI (no mobile app)
- ✅ Pre-computed data (no real-time scraping)

**Explicitly Out of Scope for MVP**:
- ❌ Multiple cities
- ❌ Hotels
- ❌ Natural language queries (slider only)
- ❌ User accounts / saved preferences
- ❌ Map view
- ❌ Real-time scraping
- ❌ Advanced bias detection (timing, language patterns)

---

## Key Decisions & Trade-offs

### Web Scraping vs. APIs
**Decision**: Use web scraping
**Rationale**:
- TripAdvisor has no public API
- Google Places API is expensive (~$17/1000 reviews)
- Yelp API has strict rate limits
- Personal use, so legal risk is minimal
**Trade-off**: More fragile (scrapers break when sites change), slower

### Real-time vs. Pre-computed
**Decision**: Pre-compute data for single city
**Rationale**:
- Faster user experience
- Cheaper (scrape once, serve many times)
- Easier to validate results
- Good for MVP validation
**Trade-off**: Data becomes stale, limited to pre-selected cities

### AI Model Selection
**Decision**: Use OpenAI gpt-4o-mini or Claude 3.5 Haiku
**Rationale**:
- Fast and cheap (~$0.01-0.02 per 100 reviews)
- Good enough accuracy for aspect extraction
- Easy API integration
**Trade-off**: Ongoing API costs, requires internet

### Frontend Framework
**Decision**: React + Vite
**Rationale**:
- Modern, fast development
- Component reusability (sliders, cards)
- Easy state management
- Good for future expansion
**Trade-off**: Slightly more complex than vanilla JS for MVP

---

## Cost Estimates (MVP)

**For pre-computing one city with 100 restaurants, 50 reviews each = 5,000 reviews:**

- **Scraping**: Free (uses Playwright)
- **AI Analysis**:
  - 5,000 reviews × $0.0002/review (gpt-4o-mini) = **$1**
  - Or 5,000 reviews × $0.0004/review (Claude Haiku) = **$2**
- **Hosting** (if deployed): $0 for now (run locally)

**Total MVP cost: ~$1-2**

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Scrapers break due to site changes | High | Use robust selectors, add error handling, test regularly |
| AI aspect extraction is inaccurate | High | Test on sample reviews, fine-tune prompt, consider few-shot examples |
| Rate limiting / IP blocking | Medium | Add delays (2-5 sec between requests), rotate user agents |
| API costs exceed budget | Low | Use cheapest models, batch requests, limit initial city size |
| Bias detection has false positives | Medium | Tune thresholds, show confidence levels, let users override |

---

## Success Metrics

**MVP is successful if**:
1. ✅ Can scrape 100+ restaurants from 3 sources for one city
2. ✅ AI correctly extracts aspects from >80% of reviews
3. ✅ Bias detection identifies at least one known fake-review establishment
4. ✅ UI is usable and sliders affect ranking
5. ✅ Confidence intervals correlate with review count (more reviews = tighter intervals)
6. ✅ You would actually use this for your next trip

**Next steps after MVP**:
- Expand to 5-10 major cities
- Add hotels
- Improve bias detection (timing, language analysis)
- Add natural language queries
- Mobile optimization

---

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- OpenAI API key OR Anthropic API key
- ~2GB disk space for data

### Quick Start (after implementation)
```bash
# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
playwright install chromium

# Add API key to .env
echo "OPENAI_API_KEY=your_key_here" > .env

# Pre-compute a city
python scripts/precompute_city.py --city "Paris, France" --limit 100

# Start backend API
python api.py

# Frontend setup (new terminal)
cd frontend
npm install
npm run dev

# Open http://localhost:5173
```

---

## Questions to Answer During Implementation

1. **Which city should we use for testing?** (Paris? Tokyo? NYC? Your next destination?)
2. **OpenAI or Anthropic Claude?** (Both work, similar cost)
3. **How many restaurants to scrape?** (50 = faster, 100 = better validation)
4. **Confidence interval threshold?** (Only show restaurants with SE < 0.5?)
5. **Bias detection sensitivity?** (Flag if >1.0 star variance? >1.5?)

---

## Next Steps

Ready to implement! Let's start with **Phase 1: Setup & Infrastructure**.

Would you like me to:
1. **Start implementing now** (I'll begin with project setup)
2. **Adjust the plan first** (any changes to scope, tech stack, or approach?)
3. **Answer specific questions** (clarify any part of the plan)

Let me know and I'll get started!
