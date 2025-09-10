# Keyword Analysis API

A FastAPI application that analyzes Amazon product keywords using AI to classify and score their relevance.

## Features

- **Dual Input Methods**: 
  - Provide an ASIN to fetch product details via Keepa API
  - Provide a text description of the product directly
- **Batch Processing**: Efficiently processes keywords in batches
- **AI-Powered Analysis**: Uses OpenRouter API with Google Gemini model
- **Detailed Classification**: Categorizes keywords as generic, brand, or competitor
- **Relevance Scoring**: Scores each keyword from 1-10 for relevance
- **JSON Response**: Returns structured data with analysis results and summary

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Update the `.env` file with your API keys:

```env
# Required
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Optional (needed for ASIN lookups)
KEEPA_API_KEY=your_keepa_api_key_here

# Configuration (optional, these are defaults)
OPENROUTER_MODEL=google/gemini-2.5-flash-lite
BATCH_SIZE=30
MAX_CONCURRENT_REQUESTS=0  # 0 = unlimited (send all requests at once)
```

## Running the API

Start the FastAPI server:

```bash
python app.py
```

Or use uvicorn directly:

```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## API Documentation

Interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### POST `/analyze-keywords`

Analyzes keywords for product relevance.

#### Option 1: Using ASIN (requires Keepa API key)

```json
{
  "asin": "B018DQI53G",
  "country": "US",
  "keywords": [
    "thermal underwear",
    "long johns",
    "fleece lined"
  ]
}
```

#### Option 2: Using Product Description

```json
{
  "product_description": "Thermajohn Long Johns Thermal Underwear for Men Fleece Lined Base Layer Set. Features heat retention, moisture wicking, 4-way stretch. Brand: Thermajohn, Price: $31.49",
  "keywords": [
    "thermal underwear",
    "long johns",
    "fleece lined"
  ]
}
```

#### Response Format

```json
{
  "input_type": "asin" | "description",
  "product_info": {
    "asin": "B018DQI53G",
    "product_title": "...",
    "brand": "Thermajohn",
    "rating": 4.6,
    "review_count": 53869,
    "price": 31.49,
    // ... more fields
  },
  "analysis_results": [
    {
      "keyword": "thermal underwear",
      "type": "generic",
      "score": 8,
      "reasoning": "Highly relevant generic keyword matching product category"
    }
  ],
  "summary": {
    "total_keywords": 10,
    "analyzed": 10,
    "failed": 0,
    "by_type": {
      "generic": 7,
      "our_brand": 2,
      "competitor_brand": 1
    },
    "average_score": 7.5,
    "processing_time": 2.34
  }
}
```

### GET `/health`

Health check endpoint showing API status and configuration.

## Testing

Run the test script to verify both input methods:

```bash
python test_api.py
```

## Example Usage with cURL

### With Product Description:

```bash
curl -X POST "http://localhost:8000/analyze-keywords" \
  -H "Content-Type: application/json" \
  -d '{
    "product_description": "High-quality thermal underwear for cold weather",
    "keywords": ["thermal underwear", "winter clothing"]
  }'
```

### With ASIN:

```bash
curl -X POST "http://localhost:8000/analyze-keywords" \
  -H "Content-Type: application/json" \
  -d '{
    "asin": "B018DQI53G",
    "country": "US",
    "keywords": ["thermal underwear", "winter clothing"]
  }'
```

## Keyword Classification Types

- **generic**: General category keywords (e.g., "thermal underwear", "base layer")
- **our_brand**: Keywords containing the product's brand name
- **competitor_brand**: Keywords containing competitor brand names

## Relevance Scoring

- **1-3**: Low relevance (unrelated or competitor-only keywords)
- **4-6**: Medium relevance (somewhat related keywords)
- **7-9**: High relevance (closely matching product features)
- **10**: Perfect match (exact brand/product match)

## Error Handling

The API includes comprehensive error handling:
- Invalid ASIN format validation
- Missing API keys detection
- Keepa API failure fallback
- Batch processing retry logic
- Detailed error messages in responses

## Performance

- Batch processing for efficient API usage
- Configurable concurrent request limits
- Automatic retry for failed keywords
- Processing time tracking in responses

## Security

- API keys stored in environment variables
- `.env` file excluded from version control via `.gitignore`
- CORS middleware configured for cross-origin requests