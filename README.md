# Google Business Profile Analyzer API

A powerful REST API that analyzes Google Business Profile (GBP) health and provides detailed insights using AI-powered analysis. This tool helps businesses understand their online presence and get actionable recommendations for improvement.

## 🌟 Features

- **Complete Business Analysis**: Analyzes ratings, reviews, photos, posts, and profile completeness
- **AI-Powered Insights**: Uses Google Gemini AI to provide detailed, human-readable analysis
- **Photo Attribution Analysis**: Distinguishes between owner and customer photos using web scraping
- **Recent Activity Tracking**: Monitors recent reviews and posts within the last month
- **Social Media Detection**: Identifies website and social media links
- **Health Scoring**: Provides a numerical score (0-10) based on multiple factors

## 🚀 Quick Start

### Prerequisites

- Python 3.12 or higher
- Docker (optional, for containerized deployment)
- SerpApi account (for Google Maps data)
- Google AI Studio account (for Gemini API)

### Installation

1. **Clone the repository**

   ```bash
   git clone <your-repository-url>
   cd gbp-analyzer
   ```

2. **Install dependencies using Poetry**

   ```bash
   # Install Poetry if you haven't already
   pip install poetry

   # Install project dependencies
   poetry install
   ```

3. **Set up environment variables**

   Create a `.env` file in the root directory (see [Environment Setup](#environment-setup) below)

4. **Run the application**

   ```bash
   # Using Poetry
   poetry run start

   # Or activate virtual environment and run directly
   poetry shell
   uvicorn src.main:app --host 0.0.0.0 --port 8000
   ```

5. **Access the API**
   - API will be available at: `http://localhost:8000`
   - Interactive documentation: `http://localhost:8000/docs`
   - Alternative docs: `http://localhost:8000/redoc`

## 🔧 Environment Setup

Create a `.env` file in the root directory with the following variables:

```env
# Required API Keys
SERP_API_KEY=your_serpapi_key_here
GEMINI_API_KEY=your_google_ai_studio_key_here

# Gemini Model Configuration (Optional - defaults provided)
GEMINI_MODEL_FLASH=gemini-2.5-flash
GEMINI_MODEL_PRO=gemini-2.5-pro

# Application Configuration (Optional)
APP_HOST=0.0.0.0
APP_PORT=8000
```

### Getting API Keys

#### 1. SerpApi Key (Required)

- Visit [SerpApi](https://serpapi.com/)
- Sign up for an account
- Go to your dashboard to get your API key
- Free tier includes 100 searches/month

#### 2. Google Gemini API Key (Required)

- Visit [Google AI Studio](https://aistudio.google.com/)
- Sign in with your Google account
- Go to "Get API Key" section
- Create a new API key
- Free tier includes generous usage limits

## 🏗️ Project Structure

```
gbp-analyzer/
├── src/
│   ├── api/
│   │   └── v1/
│   │       ├── routers/
│   │       │   ├── analyzer.py          # Main analysis endpoint
│   │       │   ├── llm_analysis.py      # AI-powered detailed analysis
│   │       │   ├── site_socials.py      # Website/social links endpoint
│   │       │   └── reviews.py           # Legacy analyzer (deprecated)
│   │       └── schemas/
│   │           └── analyzer_schemas.py   # API request/response models
│   ├── core/
│   │   └── config.py                    # Configuration management
│   ├── scrapers/
│   │   ├── photo_scraper.py             # Web scraper for photo analysis
│   │   └── uploader_scraper_process.py  # Multi-process photo scraping
│   ├── services/
│   │   ├── gbp_analyzer.py              # Main business logic
│   │   └── llm_detailed_analysis.py     # AI analysis service
│   ├── utils/
│   │   ├── analyzer_helper.py           # Helper functions
│   │   ├── computation.py               # Score calculation
│   │   ├── parsing.py                   # Date/data parsing utilities
│   │   └── scoring.py                   # Scoring algorithms
│   ├── main.py                          # FastAPI application
│   └── run.py                           # Application runner
├── assets/
│   └── pre-prompt.txt                   # AI analysis prompt template
├── .env                                 # Environment variables (create this)
├── pyproject.toml                       # Python dependencies
├── Dockerfile                           # Docker configuration
├── compose.yaml                         # Docker Compose setup
└── README.md                            # This file
```

## 📖 API Usage

### 1. Analyze Business Profile

**Endpoint**: `POST /v1/analyze`

Performs a complete analysis of a Google Business Profile.

```bash
# Using business name (recommended for ease of use)
curl -X 'POST' \
  'http://127.0.0.1:8000/v1/detailed_analysis' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
    "score": 7.1,
    "data": {
        "title": "Excelsior Coffee",
        "place_id": "ChIJdefTJb9_j4ARM99sfJXvgtg",
        "address": "4495 Mission St, San Francisco, CA 94112, United States",
        "phone": "+1 415-347-7333",
        "website": "https://www.xlcrsf.com/",
        "description": "Petite neighborhood coffeehouse with an industrial edge that presents coffee & baked goods by day.",
        "attributes_count": 26,
        "rating": 4.7,
        "reviews_count": 261,
        "social_links": [
            {
                "name": "Facebook",
                "link": "https://www.facebook.com/excelsiorcoffeesf"
            }
        ],
        "recent_reviews_in_last_month_count": 5,
        "posts_count": 0,
        "photo_counts_by_uploader": {
            "owner_photo_count": 3,
            "customer_photo_count": 97
        },
        "total_photos_analyzed": 100
    }
}'
# Using Google Place ID (more precise)
curl -X POST "http://localhost:8000/v1/analyze" \
-H "Content-Type: application/json" \
-d '{
  "place_id": "ChIJN1t_tDeuEmsRUsoyG83frY4"
}'
```

**Response Example**:

```json
{
  "score": 7.8,
  "data": {
    "title": "Starbucks",
    "place_id": "ChIJN1t_tDeuEmsRUsoyG83frY4",
    "address": "123 Main St, Chicago, IL",
    "phone": "+1-312-555-0123",
    "website": "https://starbucks.com",
    "rating": 4.2,
    "reviews_count": 150,
    "recent_reviews_in_last_month_count": 12,
    "posts_count": 3,
    "photo_counts_by_uploader": {
      "owner_photo_count": 15,
      "customer_photo_count": 45
    },
    "total_photos_analyzed": 60,
    "social_links": [...]
  }
}
```

### 2. Get Detailed AI Analysis

**Endpoint**: `POST /v1/detailed_analysis`

Generates a human-readable analysis using AI.

```bash
curl -X POST "http://localhost:8000/v1/detailed_analysis" \
-H "Content-Type: application/json" \
-d '{
  "score": 7.8,
  "data": { /* business data from previous endpoint */ },
  "model_choice": "flash"
}'
```

### 3. Get Website & Social Links Only

**Endpoint**: `POST /v1/website_socials`

Quickly retrieves just the website and social media links.

```bash
curl -X POST "http://localhost:8000/v1/website_socials" \
-H "Content-Type: application/json" \
-d '{
  "business_name": "Starbucks Chicago Downtown"
}'
```

## 🐳 Docker Deployment

### Using Docker Compose (Recommended)

```bash
# Build and start the application
docker compose up --build

# Run in background
docker compose up -d --build
```

### Using Docker directly

```bash
# Build the image
docker build -t gbp-analyzer .

# Run the container
docker run -p 8000:8000 --env-file .env gbp-analyzer
```

## 🧪 Testing

Run the command-line test script to verify your setup:

```bash
# Test with a business query
python test.py "Starbucks Chicago"
```

## ⚖️ Scoring System

The API calculates a health score (0-10) based on:

- **Google Posts (20%)**: Recent posts within the last month
- **Photos (20%)**: Balance of owner and customer photos
- **Review Recency (20%)**: Recent reviews within the last month
- **Star Rating (15%)**: Overall rating quality
- **Review Count (15%)**: Total number of reviews
- **Profile Completeness (5%)**: Attributes and description filled
- **NAPW Data (5%)**: Name, Address, Phone, Website completeness

## 🔧 Configuration

### Model Selection

Choose between two AI models for detailed analysis:

- **flash**: Faster, cost-effective (default)
- **pro**: More detailed, higher quality analysis

### Customization

- **Photo Analysis Limit**: Modify `check_limit` in `PhotoScraper` class
- **Pagination Limits**: Adjust in `analyzer_helper.py`
- **AI Prompts**: Edit `assets/pre-prompt.txt`

## 📊 Use Cases

### For Business Owners

- **Profile Optimization**: Identify areas for improvement
- **Competitor Analysis**: Compare against other businesses
- **Performance Tracking**: Monitor changes over time
- **Action Items**: Get specific recommendations

### For Marketing Agencies

- **Client Reporting**: Generate detailed health reports
- **Audit Services**: Comprehensive GBP audits
- **Strategy Planning**: Data-driven optimization plans
- **Bulk Analysis**: Analyze multiple client profiles

### For Developers

- **Integration**: Embed analysis into existing tools
- **Automation**: Build automated monitoring systems
- **Custom Scoring**: Modify scoring algorithms
- **Data Export**: Extract structured business data

## 🚨 Troubleshooting

### Common Issues

1. **"Service Unavailable" Error**

   - Check your API keys in `.env` file
   - Verify SerpApi and Gemini API keys are valid

2. **"No GBP found" Error**

   - Try a more specific business name with location
   - Use the exact business name as it appears on Google Maps

3. **Photo Scraping Timeouts**

   - Some businesses have many photos; this is normal
   - Consider reducing the `check_limit` parameter

4. **Rate Limits**
   - SerpApi has monthly limits on free tier
   - Monitor your usage in the SerpApi dashboard

### Performance Tips

- Use `place_id` when possible for faster, more accurate results
- Cache results for frequently analyzed businesses
- Consider upgrading API plans for high-volume usage

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔗 Links

- [SerpApi Documentation](https://serpapi.com/google-maps-api)
- [Google AI Studio](https://aistudio.google.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Playwright Documentation](https://playwright.dev/python/)

---

**Need help?** Open an issue or contact the development team.
