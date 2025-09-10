# Keyword Analysis API Documentation

## API Endpoint

**Base URL:** `http://localhost:8000` (or your deployed URL)

**Main Endpoint:** `POST /analyze-keywords`

## Request Format

The API accepts two types of input:

### Option 1: ASIN-based Product Lookup

When you have an Amazon ASIN, the API will fetch product details from Keepa automatically.

```json
{
  "asin": "B018DQI53G",
  "country": "US",
  "keywords": [
    "thermal underwear men",
    "thermajohn long johns",
    "fleece lined base layer",
    "cold weather gear",
    "mens thermals",
    "carhartt thermal underwear",
    "winter base layer",
    "long underwear mens",
    "thermal pajamas",
    "best thermal underwear"
  ]
}
```

### Option 2: Product Description Text

When you don't have an ASIN, provide a text description of the product.

```json
{
  "product_description": "Thermajohn Long Johns Thermal Underwear for Men Fleece Lined Base Layer Set for Cold Weather. Brand: Thermajohn, Rating: 4.6/5 with 53,869 reviews, Price: $31.49. Features heat retention, ultra soft fleece lining, moisture wicking fabric, 4-way stretch material. Perfect for layering during winter or wearing as pajamas.",
  "keywords": [
    "thermal underwear men",
    "thermajohn long johns",
    "fleece lined base layer",
    "cold weather gear",
    "mens thermals",
    "carhartt thermal underwear",
    "winter base layer",
    "long underwear mens",
    "thermal pajamas",
    "best thermal underwear"
  ]
}
```

## Response Format

### Successful Response (200 OK)

```json
{
  "input_type": "asin",
  "product_info": {
    "asin": "B018DQI53G",
    "brand": "Thermajohn",
    "product_title": "Thermajohn Long Johns Thermal Underwear for Men Fleece Lined Base Layer Set for Cold Weather",
    "product_features": "Heat Retention: When it comes to warmth and everyday wear, these long johns for men is designed specifically for you to stay protected from the cold.|Ultra Soft Fleece: Designed with a fleece lining & quality material, these ultra soft mens thermal underwear set will keep you feeling comfortable throughout the day.|Moisture Wicking: Stay dry with these long underwear mens as they're made from breathable fabric that effectively wicks away moisture and perspiration.|4 Way Stretch: Made with stretchable material, these thermals for men allows you freedom of movement with no chafing or bunching up when you move.|Layer Up: Layering is essential to ward off the cold, so bundle up with a pair of mens thermals this winter and stay comfortable while outside or in bed as a pajama.",
    "description": "",
    "main_image_url": "https://images-na.ssl-images-amazon.com/images/I/71KqR4LYXPL.jpg",
    "gallery_image_urls": [
      "https://images-na.ssl-images-amazon.com/images/I/81B9sQ2LYPL.jpg",
      "https://images-na.ssl-images-amazon.com/images/I/71aDQ3LYXPL.jpg"
    ],
    "category_tree": [
      {
        "catId": 7141123011,
        "name": "Clothing, Shoes & Jewelry"
      },
      {
        "catId": 7147441011,
        "name": "Men"
      }
    ],
    "cat_id": 7141123011,
    "category_name": "Clothing, Shoes & Jewelry",
    "parent_asin": "",
    "review_count": 53869,
    "rating": 4.6,
    "sales_rank": 1234,
    "price": 29.99,
    "category_attributes": {
      "material": "95% Polyester, 5% Spandex",
      "size": "Medium",
      "color": "Black"
    },
    "raw_description": null
  },
  "analysis_results": [
    {
      "keyword": "thermal underwear men",
      "type": "generic",
      "score": 9,
      "reasoning": "Highly relevant generic keyword that directly describes the product category and target audience"
    },
    {
      "keyword": "thermajohn long johns",
      "type": "our_brand",
      "score": 10,
      "reasoning": "Perfect match - contains exact brand name 'Thermajohn' with product type 'long johns'"
    },
    {
      "keyword": "fleece lined base layer",
      "type": "generic",
      "score": 9,
      "reasoning": "Directly matches key product features - fleece lining and base layer functionality"
    },
    {
      "keyword": "cold weather gear",
      "type": "generic",
      "score": 7,
      "reasoning": "Relevant broader category term that encompasses thermal underwear"
    },
    {
      "keyword": "mens thermals",
      "type": "generic",
      "score": 8,
      "reasoning": "Highly relevant alternative term for men's thermal underwear"
    },
    {
      "keyword": "carhartt thermal underwear",
      "type": "competitor_brand",
      "score": 2,
      "reasoning": "Competitor brand keyword - low relevance as it's searching for a different brand"
    },
    {
      "keyword": "winter base layer",
      "type": "generic",
      "score": 8,
      "reasoning": "Relevant seasonal category term that matches product use case"
    },
    {
      "keyword": "long underwear mens",
      "type": "generic",
      "score": 9,
      "reasoning": "Direct product type match with target audience specification"
    },
    {
      "keyword": "thermal pajamas",
      "type": "generic",
      "score": 6,
      "reasoning": "Moderately relevant - product can be used as pajamas but primarily marketed as thermal underwear"
    },
    {
      "keyword": "best thermal underwear",
      "type": "generic",
      "score": 8,
      "reasoning": "High-intent generic search term for the exact product category"
    }
  ],
  "summary": {
    "total_keywords": 10,
    "analyzed": 10,
    "failed": 0,
    "by_type": {
      "generic": 8,
      "our_brand": 1,
      "competitor_brand": 1
    },
    "average_score": 7.6,
    "processing_time": 2.34
  },
  "errors": null
}
```

### Response with Product Description Input

When using product description instead of ASIN, the response structure is the same except:
- `input_type` will be `"description"`
- `product_info` will have most fields as `null` except `raw_description` which contains your input text

```json
{
  "input_type": "description",
  "product_info": {
    "asin": null,
    "brand": null,
    "product_title": null,
    "product_features": null,
    "description": null,
    "main_image_url": null,
    "gallery_image_urls": null,
    "category_tree": null,
    "cat_id": null,
    "category_name": null,
    "parent_asin": null,
    "review_count": null,
    "rating": null,
    "sales_rank": null,
    "price": null,
    "category_attributes": null,
    "raw_description": "Thermajohn Long Johns Thermal Underwear for Men Fleece Lined Base Layer Set for Cold Weather. Brand: Thermajohn, Rating: 4.6/5 with 53,869 reviews, Price: $31.49. Features heat retention, ultra soft fleece lining, moisture wicking fabric, 4-way stretch material."
  },
  "analysis_results": [
    // Same structure as above
  ],
  "summary": {
    // Same structure as above
  }
}
```

## Error Responses

### 400 Bad Request - Invalid Input

```json
{
  "detail": "Either ASIN or product_description must be provided"
}
```

### 503 Service Unavailable - Keepa API Error

```json
{
  "detail": "Failed to fetch product details from Keepa: No product data found for ASIN: B123456789"
}
```

### 500 Internal Server Error

```json
{
  "detail": "Analysis failed: [error message]"
}
```

## Field Descriptions

### Request Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `asin` | string | Conditional* | 10-character Amazon ASIN |
| `country` | string | No | Country code (default: "US"). Options: US, UK, DE, FR, JP, CA, IT, ES, IN, MX, BR, AU, NL |
| `product_description` | string | Conditional* | Text description of the product |
| `keywords` | array[string] | Yes | List of keywords to analyze (min: 1 keyword) |

*Either `asin` OR `product_description` must be provided, but not both.

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `input_type` | string | "asin" or "description" indicating which input method was used |
| `product_info` | object | Product details (full data for ASIN, minimal for description) |
| `analysis_results` | array | List of keyword analysis results |
| `summary` | object | Summary statistics of the analysis |
| `errors` | array/null | List of any errors encountered during processing |

### Analysis Result Fields

| Field | Type | Description |
|-------|------|-------------|
| `keyword` | string | The analyzed keyword |
| `type` | string | Classification: "generic", "our_brand", or "competitor_brand" |
| `score` | integer | Relevance score from 1-10 |
| `reasoning` | string | Brief explanation for the classification and score |

### Summary Fields

| Field | Type | Description |
|-------|------|-------------|
| `total_keywords` | integer | Total number of keywords submitted |
| `analyzed` | integer | Number of keywords successfully analyzed |
| `failed` | integer | Number of keywords that failed to analyze |
| `by_type` | object | Count of keywords by classification type |
| `average_score` | float | Average relevance score across all analyzed keywords |
| `processing_time` | float | Total processing time in seconds |

## Classification Types Explained

- **generic**: General product category keywords (e.g., "thermal underwear", "base layer")
- **our_brand**: Keywords containing the product's brand name (e.g., "Thermajohn" for a Thermajohn product)
- **competitor_brand**: Keywords containing competitor brand names (e.g., "Carhartt" when analyzing a Thermajohn product)

## Relevance Scoring Guide

- **1-3**: Low relevance - Unrelated or competitor-focused keywords
- **4-6**: Medium relevance - Somewhat related but not directly matching
- **7-9**: High relevance - Closely matching product features or category
- **10**: Perfect match - Exact brand and product match

## Rate Limits and Performance

- **Batch Size**: Keywords are processed in batches of 30 (configurable)
- **Concurrency**: Unlimited concurrent requests to OpenRouter API (for paid models)
- **Typical Performance**: ~2-5 seconds for 100 keywords
- **Maximum Keywords**: No hard limit, but larger requests will take longer

## Example cURL Commands

### Example 1: Using ASIN

```bash
curl -X POST "http://localhost:8000/analyze-keywords" \
  -H "Content-Type: application/json" \
  -d '{
    "asin": "B018DQI53G",
    "country": "US",
    "keywords": ["thermal underwear", "winter clothing", "base layer"]
  }'
```

### Example 2: Using Product Description

```bash
curl -X POST "http://localhost:8000/analyze-keywords" \
  -H "Content-Type: application/json" \
  -d '{
    "product_description": "High-quality thermal underwear for men, fleece-lined for extra warmth",
    "keywords": ["thermal underwear", "winter clothing", "base layer"]
  }'
```

## Health Check Endpoint

**GET `/health`**

Returns the API status and configuration:

```json
{
  "status": "healthy",
  "configuration": {
    "openrouter_api_key": "configured",
    "keepa_api_key": "configured",
    "model": "google/gemini-2.5-flash-lite",
    "batch_size": "30",
    "max_concurrent_requests": "unlimited (all at once)"
  }
}
```

## Notes for Frontend Implementation

1. **Input Validation**: Ensure either `asin` or `product_description` is provided, but not both
2. **Keyword Deduplication**: The API automatically removes duplicate keywords (case-insensitive)
3. **Error Handling**: Implement proper error handling for 400, 503, and 500 status codes
4. **Loading States**: Processing can take 2-10+ seconds depending on the number of keywords
5. **CORS**: The API has CORS enabled for all origins (configurable in production)
6. **Async Processing**: All keyword analysis is done asynchronously for optimal performance