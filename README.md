# Google Business Profile Analyzer API

A comprehensive REST API that analyzes Google Business Profile (GBP) health and provides detailed insights using AI-powered analysis. This tool helps businesses, marketing agencies, and developers understand online presence and get actionable recommendations for improvement.

## 🎯 What This Project Does

The Google Business Profile Analyzer is a sophisticated tool that evaluates how well a business is managing their Google Business Profile. It examines multiple factors that impact local SEO and customer engagement, then provides both a numerical health score (0-10) and detailed AI-powered recommendations.

### Key Analysis Areas:

- **Profile Completeness**: Checks if all business information fields are filled
- **Photo Analysis**: Distinguishes between owner-uploaded and customer-uploaded photos
- **Review Activity**: Monitors recent customer reviews and engagement
- **Google Posts**: Tracks business updates and announcements
- **Contact Information**: Validates Name, Address, Phone, Website (NAPW) data
- **Social Media Links**: Identifies connected social media accounts

## 🔄 How It Works

### 1. Data Collection Process

```
Business Query/Place ID → SerpApi → Google Maps Data → Raw Business Information
                                                    ↓
Photo Scraping (Playwright) → Attribution Analysis → Owner vs Customer Photos
                                                    ↓
Review Analysis → Recent Activity Filter → Engagement Metrics
                                                    ↓
Social Links Detection → Knowledge Graph → Connected Platforms
```

### 2. Scoring Algorithm

The system calculates a weighted health score based on:

| Component      | Weight | What It Measures                                                       |
| -------------- | ------ | ---------------------------------------------------------------------- |
| Google Posts   | 20%    | Recent business updates (last 30 days)                                 |
| Photos         | 20%    | Balance of owner photos (professional) vs customer photos (engagement) |
| Review Recency | 20%    | Fresh customer reviews (last 30 days)                                  |
| Star Rating    | 15%    | Overall customer satisfaction                                          |
| Review Count   | 15%    | Total social proof volume                                              |
| Profile Fields | 5%     | Completeness of attributes and description                             |
| NAPW Data      | 5%     | Basic contact information completeness                                 |

### 3. AI Analysis Generation

- Uses Google Gemini AI models (Flash or Pro)
- Converts raw data into human-readable insights
- Provides specific, actionable recommendations
- Maintains professional, encouraging tone

## 🌟 Core Features

- **Complete Business Analysis**: Comprehensive 360° view of GBP health
- **AI-Powered Insights**: Human-readable analysis with specific recommendations
- **Photo Attribution Intelligence**: Advanced web scraping to classify photo sources
- **Real-Time Activity Monitoring**: Tracks recent reviews, posts, and engagement
- **Social Media Discovery**: Automatically finds connected social platforms
- **Numerical Health Scoring**: Easy-to-understand 0-10 rating system
- **Multiple AI Models**: Choose between speed (Flash) or depth (Pro) analysis
- **Docker Ready**: Containerized deployment for scalability

## 📋 Prerequisites

Before using this application, you need:

### Required API Keys

1. **SerpApi Account** (Required)

   - Sign up at [SerpApi.com](https://serpapi.com/)
   - Free tier: 100 searches/month
   - Used for: Google Maps data extraction

2. **Google AI Studio Account** (Required)
   - Sign up at [Google AI Studio](https://aistudio.google.com/)
   - Free tier: Generous usage limits
   - Used for: AI-powered analysis generation

### System Requirements

- **Python 3.12+** (for local development)
- **Docker** (recommended for deployment)
- **8GB RAM minimum** (for web scraping processes)
- **Internet connection** (for API calls and web scraping)

### Technical Dependencies

- **Poetry** (Python dependency management)
- **Playwright** (Web scraping engine)
- **FastAPI** (API framework)
- **Google Generative AI** (LLM integration)

## 🚀 Quick Start

### Option 1: Docker Deployment (Recommended)

1. **Clone and Setup**

   ```bash
   git clone <your-repository-url>
   cd gbp-analyzer
   ```

2. **Create Environment File**

   ```bash
   # Create .env file with your API keys
   cp .env.example .env
   # Edit .env with your actual API keys (see Environment Setup below)
   ```

3. **Deploy with Docker**

   ```bash
   # Build and start the application
   docker compose up --build

   # Or run in background
   docker compose up -d --build
   ```

4. **Access the API**
   - API: `http://localhost:8000`
   - Documentation: `http://localhost:8000/docs`

### Option 2: Local Development

1. **Clone and Install**

   ```bash
   git clone <your-repository-url>
   cd gbp-analyzer

   # Install Poetry if not already installed
   pip install poetry

   # Install dependencies
   poetry install

   # Install Playwright browsers
   poetry run playwright install chromium
   ```

2. **Setup Environment**

   ```bash
   # Create .env file (see Environment Setup below)
   touch .env
   ```

3. **Run Application**

   ```bash
   # Using Poetry
   poetry run start

   # Or activate environment and run directly
   poetry shell
   uvicorn src.main:app --host 0.0.0.0 --port 8000
   ```

## 🔧 Environment Setup

Create a `.env` file in the root directory:

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

# Analysis Configuration (Optional)
GBP_ANALYSIS_PROMPT_PATH=assets/pre-prompt.txt
```

### Getting Your API Keys

#### 1. SerpApi Key Setup

1. Visit [SerpApi](https://serpapi.com/)
2. Create an account (free tier available)
3. Go to your dashboard
4. Copy your API key
5. Free plan includes 100 searches/month

#### 2. Google Gemini API Key Setup

1. Visit [Google AI Studio](https://aistudio.google.com/)
2. Sign in with your Google account
3. Navigate to "Get API Key"
4. Create a new API key
5. Copy the key to your `.env` file
6. Free tier includes generous usage limits

## 🏗️ Project Architecture

```
gbp-analyzer/
├── src/
│   ├── api/v1/                          # API Layer
│   │   ├── routers/
│   │   │   ├── analyzer.py              # Main analysis endpoint
│   │   │   ├── llm_analysis.py          # AI analysis endpoint
│   │   │   └── site_socials.py          # Social/website endpoint
│   │   └── schemas/
│   │       └── analyzer_schemas.py      # Request/response models
│   ├── core/
│   │   └── config.py                    # Configuration management
│   ├── scrapers/                        # Web Scraping Layer
│   │   ├── photo_scraper.py             # Playwright photo scraper
│   │   └── uploader_scraper_process.py  # Multi-process wrapper
│   ├── services/                        # Business Logic Layer
│   │   ├── gbp_analyzer.py              # Main analyzer service
│   │   └── llm_detailed_analysis.py     # AI analysis service
│   ├── utils/                           # Utility Layer
│   │   ├── analyzer_helper.py           # Helper functions
│   │   ├── computation.py               # Score calculation
│   │   ├── parsing.py                   # Date/data parsing
│   │   └── scoring.py                   # Scoring algorithms
│   ├── main.py                          # FastAPI application
│   └── run.py                           # Application runner
├── assets/
│   └── pre-prompt.txt                   # AI analysis prompt template
├── .env                                 # Environment variables (create this)
├── pyproject.toml                       # Python dependencies
├── Dockerfile                           # Container configuration
├── compose.yaml                         # Docker Compose setup
└── test.py                              # Command-line testing tool
```

## 📖 API Usage Guide

### 1. Primary Analysis Endpoint

**Endpoint**: `POST /v1/analyze`

Performs complete business profile analysis and returns numerical score with raw data.

```bash
# Using business name (easier for humans)
curl -X POST "http://localhost:8000/v1/analyze" \
-H "Content-Type: application/json" \
-d '{
  "business_name": "Starbucks Chicago Downtown",
  "star_rating": 4.2,
  "review_count": 150,
  "address": "123 Main St, Chicago, IL"
}'

# Using Place ID (more precise, faster)
curl -X POST "http://localhost:8000/v1/analyze" \
-H "Content-Type: application/json" \
-d '{
  "place_id": "ChIJN1t_tDeuEmsRUsoyG83frY4"
}'
```

**Response Structure**:

```json
{
  "score": 7.8,
  "data": {
    "title": "Starbucks",
    "place_id": "ChIJN1t_tDeuEmsRUsoyG83frY4",
    "address": "123 Main St, Chicago, IL",
    "phone": "+1-312-555-0123",
    "website": "https://starbucks.com",
    "description": "Coffee shop chain...",
    "attributes_count": 26,
    "rating": 4.2,
    "reviews_count": 150,
    "social_links": [
      {
        "name": "Facebook",
        "link": "https://facebook.com/starbucks"
      }
    ],
    "recent_reviews_in_last_month_count": 12,
    "posts_count": 3,
    "photo_counts_by_uploader": {
      "owner_photo_count": 15,
      "customer_photo_count": 45
    },
    "total_photos_analyzed": 60
  }
}
```

### 2. AI-Powered Detailed Analysis

**Endpoint**: `POST /v1/detailed_analysis`

Converts raw data into human-readable insights and recommendations.

```bash
curl -X POST "http://localhost:8000/v1/detailed_analysis" \
-H "Content-Type: application/json" \
-d '{
  "score": 7.8,
  "data": { /* use data from /analyze endpoint */ },
  "model_choice": "flash"
}'
```

**Sample AI Response**:

```json
{
  "detailed_analysis": "**Overall Assessment**\n\nStarbucks Chicago Downtown shows strong fundamentals with a solid 4.2-star rating and healthy customer engagement. However, there are opportunities to enhance their Google Business Profile presence.\n\n**Key Strengths**\n• Strong customer satisfaction with 4.2/5 stars\n• Good customer photo engagement (45 photos)\n• Recent review activity shows ongoing engagement\n\n**Areas for Improvement**\n• Increase owner-generated content (only 15 photos)\n• Post more frequent Google Business updates\n• Enhance profile completeness with missing attributes"
}
```

### 3. Quick Social/Website Lookup

**Endpoint**: `POST /v1/website_socials`

Fast endpoint for retrieving just website and social media information.

```bash
curl -X POST "http://localhost:8000/v1/website_socials" \
-H "Content-Type: application/json" \
-d '{
  "business_name": "Starbucks Chicago Downtown"
}'
```

## 🧪 Testing & Development

### Command-Line Testing Tool

Use the included test script to experiment with businesses before API integration:

```bash
# Test with a business query (finds Place ID automatically)
python test.py "Starbucks Chicago"

# Test with a specific location
python test.py "Pizza Hut, 60601"

# Test with business name and area
python test.py "McDonald's Times Square New York"
```

This tool is helpful for:

- Discovering Place IDs for frequently analyzed businesses
- Testing scoring algorithms with real data
- Debugging analysis logic during development

### Development Workflow

1. **Local Development**

   ```bash
   # Start in development mode
   poetry shell
   uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Testing Changes**

   ```bash
   # Test specific business
   python test.py "Your Test Business"

   # Check API documentation
   open http://localhost:8000/docs
   ```

3. **Production Deployment**
   ```bash
   # Deploy with Docker
   docker compose up --build -d
   ```

## 🎯 Use Cases & Applications

### For Business Owners

- **Profile Health Checkups**: Regular monitoring of GBP performance
- **Competitive Analysis**: Compare against competitors in the same area
- **Optimization Guidance**: Get specific recommendations for improvement
- **Performance Tracking**: Monitor progress over time
- **Local SEO Enhancement**: Improve local search visibility

### For Marketing Agencies

- **Client Audits**: Comprehensive GBP health assessments
- **Reporting Automation**: Generate detailed client reports
- **Strategy Development**: Data-driven local SEO strategies
- **Before/After Analysis**: Track improvement campaigns
- **Bulk Analysis**: Analyze multiple client profiles efficiently

### For Software Developers

- **Integration Projects**: Embed GBP analysis into existing platforms
- **Monitoring Systems**: Build automated health monitoring
- **Custom Scoring**: Modify algorithms for specific industries
- **White-Label Solutions**: Create branded analysis tools
- **API Aggregation**: Combine with other local SEO tools

### For Data Analysts

- **Local Market Research**: Analyze business landscapes
- **Trend Analysis**: Track local business patterns
- **Competitive Intelligence**: Market positioning insights
- **Performance Benchmarking**: Industry standard comparisons
- **Geographic Analysis**: Location-based business insights

## ⚖️ Scoring System Deep Dive

### Scoring Components Explained

**Google Posts (20% weight)**

- Measures: Recent business updates and announcements
- Best Practice: 4+ posts per month
- Impact: Shows business is active and engaged

**Photo Balance (20% weight)**

- Owner Photos: Professional, branded content
- Customer Photos: Organic engagement and social proof
- Best Practice: 10+ owner photos, 30+ customer photos
- Impact: Visual appeal and credibility

**Review Recency (20% weight)**

- Measures: Fresh customer feedback in last 30 days
- Best Practice: 5+ recent reviews monthly
- Impact: Shows ongoing customer satisfaction

**Star Rating (15% weight)**

- Measures: Overall customer satisfaction
- Best Practice: 4.0+ stars with consistent quality
- Impact: Primary ranking factor for local search

**Review Volume (15% weight)**

- Measures: Total social proof and credibility
- Best Practice: 100+ reviews for established businesses
- Impact: Trust signal for potential customers

**Profile Completeness (5% weight)**

- Measures: Filled attributes and business description
- Best Practice: Complete all relevant fields
- Impact: Better matching for relevant searches

**Contact Information (5% weight)**

- Measures: Name, Address, Phone, Website completeness
- Best Practice: All fields accurate and consistent
- Impact: Essential for local search rankings

## 🔧 Configuration & Customization

### Model Selection

Choose AI analysis depth:

- **flash**: Faster processing, good for bulk analysis
- **pro**: Detailed insights, better for comprehensive reports

### Photo Analysis Limits

Modify `check_limit` in PhotoScraper class:

```python
# In src/scrapers/photo_scraper.py
def __init__(self, check_limit: int = 100):  # Adjust this number
```

### Custom Scoring Weights

Modify weights in `src/utils/computation.py`:

```python
# Adjust these multipliers based on your priorities
weighted_google_post_score = google_post_score * 0.20  # Posts importance
weighted_image_score = total_image_score * 0.20        # Photos importance
weighted_review_recency_score = review_recency_score * 0.20  # Recent reviews
```

### AI Prompt Customization

Edit `assets/pre-prompt.txt` to modify AI analysis style:

- Change tone (professional, casual, technical)
- Add industry-specific guidance
- Modify output format
- Include custom recommendations

## 🚨 Troubleshooting Guide

### Common Issues & Solutions

**1. "Service Unavailable" Error**

```
Cause: Missing or invalid API keys
Solution:
- Verify .env file exists and contains valid keys
- Check API key quotas in respective dashboards
- Ensure no extra spaces in .env file
```

**2. "No GBP found" Error**

```
Cause: Business name too vague or doesn't exist
Solution:
- Add location to business name: "Starbucks Chicago Downtown"
- Use exact business name from Google Maps
- Try with Place ID instead of business name
```

**3. Photo Scraping Timeouts**

```
Cause: Business has many photos or slow connection
Solution:
- Reduce check_limit in PhotoScraper
- Increase timeout in scraper settings
- Check internet connection stability
```

**4. Rate Limiting Issues**

```
Cause: Exceeded API quotas
Solution:
- Monitor usage in SerpApi dashboard
- Implement request caching
- Upgrade API plans for higher limits
- Add delays between requests
```

**5. Docker Container Issues**

```
Cause: Missing environment variables or port conflicts
Solution:
- Ensure .env file is in correct location
- Check port 8000 isn't already in use
- Verify Docker has sufficient memory allocated
```

### Performance Optimization

**For High-Volume Usage**:

- Cache frequently requested business data
- Use Place IDs instead of business names when possible
- Implement request queuing for bulk operations
- Consider upgrading to paid API tiers

**For Resource-Constrained Environments**:

- Reduce photo analysis limits
- Disable image/font loading in scraper
- Use "flash" model instead of "pro"
- Implement result caching

## 📊 Monitoring & Analytics

### Built-in Logging

The application includes comprehensive logging:

- API request/response logging
- Scraping process monitoring
- Error tracking and debugging
- Performance metrics

### Health Monitoring

Monitor application health:

```bash
# Check if API is running
curl http://localhost:8000/

# View API documentation
curl http://localhost:8000/docs
```

### Usage Analytics

Track your API usage:

- Monitor SerpApi quota in dashboard
- Track Gemini API usage in Google Cloud Console
- Log analysis requests for billing/usage tracking

## 🤝 Contributing

We welcome contributions to improve the Google Business Profile Analyzer!

### Development Setup

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Install development dependencies: `poetry install`
4. Make your changes
5. Run tests: `python test.py "Test Business"`
6. Submit a pull request

### Contribution Guidelines

- Follow existing code style (Black formatting)
- Add comments for complex logic
- Update documentation for new features
- Test changes with real business data
- Ensure Docker compatibility

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔗 Additional Resources

### API Documentation

- [SerpApi Google Maps API](https://serpapi.com/google-maps-api)
- [Google AI Studio Documentation](https://ai.google.dev/docs)
- [FastAPI Framework Guide](https://fastapi.tiangolo.com/)
- [Playwright Python Documentation](https://playwright.dev/python/)

### Local SEO Resources

- [Google Business Profile Best Practices](https://support.google.com/business/)
- [Local Search Ranking Factors](https://www.brightlocal.com/research/local-search-ranking-factors/)
- [Google Maps Platform Documentation](https://developers.google.com/maps/documentation/)

### Technical Support

- **Issues & Bug Reports**: Open a GitHub issue
- **Feature Requests**: Submit via GitHub discussions
- **General Questions**: Check existing documentation first
- **API Rate Limits**: Monitor usage in respective dashboards

---

**Ready to analyze your Google Business Profile?** Start with the Quick Start guide above, or jump straight to testing with the command-line tool!
