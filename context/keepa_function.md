# Keepa API Integration Documentation

## Overview

This documentation explains how to utilize the Keepa API integration from this codebase to fetch comprehensive Amazon product details in another application. The main function `get_basic_product_details()` retrieves detailed product information including pricing, ratings, images, category data, and more.

## Prerequisites

### Required Dependencies

```bash
pip install requests
```

### Required API Key

You'll need a valid Keepa API key. Set it as an environment variable:

```bash
export KEEPA_API_KEY="your_keepa_api_key_here"
```

### Required Files

Copy these files from the original codebase:
- `keyword_research/productinfo.py` - Main Keepa integration function
- `app/common/constants.py` - Country-to-domain mappings

## Core Function

### `get_basic_product_details(asin: str, country: str = "US")`

Fetches comprehensive product details from the Keepa API.

**Parameters:**
- `asin` (str): Amazon Standard Identification Number (10-character alphanumeric code)
- `country` (str): Country code for Amazon marketplace (default: "US")

**Returns:**
- `Dict[str, Any]`: Dictionary containing product details

**Raises:**
- `ValueError`: If ASIN format is invalid
- `Exception`: If Keepa API returns an error or no product data found

## Code Examples

### Example 1: Standalone Usage

```python
import os
import requests
from typing import Dict, Any

# Country to Keepa domain ID mapping
COUNTRY_TO_DOMAIN = {
    "US": 1,  "GB": 2,  "UK": 2,  "DE": 3,  "FR": 4,
    "JP": 5,  "CA": 6,  "IT": 8,  "ES": 9,  "IN": 10,
    "MX": 11, "BR": 12, "AU": 13, "NL": 14
}

def get_basic_product_details(asin: str, country: str = "US") -> Dict[str, Any]:
    """Get product details from Keepa API"""
    
    # Validate ASIN
    if not asin or len(asin) != 10:
        raise ValueError("Invalid ASIN format")
    
    # Get API key from environment
    KEEPA_API_KEY = os.environ.get("KEEPA_API_KEY")
    if not KEEPA_API_KEY:
        raise ValueError("KEEPA_API_KEY not found in environment variables")
    
    # Get domain ID for country
    domain_id = COUNTRY_TO_DOMAIN.get(country.upper(), 1)
    
    # Prepare API request parameters
    params = {
        'key': KEEPA_API_KEY,
        'domain': domain_id,
        'asin': [asin],
        'aplus': 1,      # Include A+ content
        'stats': 7,      # Calculate stats for last 7 days
        'rating': 1      # Include rating history
    }
    
    # Make API request
    response = requests.get('https://api.keepa.com/product', params=params)
    response.raise_for_status()
    data = response.json()
    
    if 'error' in data:
        raise Exception(f"Keepa API error: {data['error']}")
    
    if not data.get("products"):
        raise Exception(f"No product data found for ASIN: {asin}")
    
    product = data["products"][0]
    
    # Extract and format product data
    features = product.get("features", [])
    features_str = "|".join(features) if features else ""
    
    # Extract A+ content
    aplus_content = product.get("aPlus")
    if not aplus_content or not isinstance(aplus_content, list):
        aplus_content = None
    
    # Extract images
    images_data = product.get("images", [])
    main_image_url = ""
    gallery_image_urls = []
    
    if images_data and isinstance(images_data, list):
        if len(images_data) > 0:
            main_img = images_data[0]
            if isinstance(main_img, dict):
                if 'l' in main_img:
                    main_image_url = f"https://images-na.ssl-images-amazon.com/images/I/{main_img['l']}"
                elif 'm' in main_img:
                    main_image_url = f"https://images-na.ssl-images-amazon.com/images/I/{main_img['m']}"
        
        for i in range(1, len(images_data)):
            img = images_data[i]
            if isinstance(img, dict):
                if 'l' in img:
                    gallery_image_urls.append(f"https://images-na.ssl-images-amazon.com/images/I/{img['l']}")
                elif 'm' in img:
                    gallery_image_urls.append(f"https://images-na.ssl-images-amazon.com/images/I/{img['m']}")
    
    # Extract category information
    category_tree = product.get("categoryTree", []) or []
    cat_id = product.get("rootCategory", 0) or 0
    category_name = ""
    
    if category_tree and isinstance(category_tree, list):
        for category in category_tree:
            if isinstance(category, dict) and category.get("catId") == cat_id:
                category_name = category.get("name", "")
                break
    
    # Extract metrics from stats array
    parent_asin = product.get("parentAsin", "") or ""
    review_count = 0
    rating = 0.0
    sales_rank = 0
    price = 0.0
    
    if "stats" in product and product["stats"]:
        stats = product["stats"]
        if "current" in stats and isinstance(stats["current"], list):
            current_stats = stats["current"]
            
            # Sales rank (index 3)
            if len(current_stats) > 3 and current_stats[3] is not None and current_stats[3] != -1:
                sales_rank = current_stats[3]
            
            # Rating (index 16, 0-50 scale, convert to 0-5)
            if len(current_stats) > 16 and current_stats[16] is not None and current_stats[16] != -1:
                rating = current_stats[16] / 10.0
            
            # Review count (index 17)
            if len(current_stats) > 17 and current_stats[17] is not None and current_stats[17] != -1:
                review_count = current_stats[17]
            
            # Price (index 1, in cents, convert to dollars)
            if len(current_stats) > 1 and current_stats[1] is not None and current_stats[1] != -1:
                price = current_stats[1] / 100.0
    
    # Extract category-specific attributes
    category_attributes = {}
    attributes_to_extract = {
        "activeIngredients": "activeIngredients",
        "ingredients": "ingredients",
        "specialIngredients": "specialIngredients",
        "itemForm": "itemForm",
        "recommendedUsesForProduct": "recommendedUsesForProduct",
        "productBenefit": "productBenefit",
        "safetyWarning": "safetyWarning",
        "material": "material",
        "size": "size",
        "color": "color",
        "style": "style",
        "scent": "scent",
        "model": "model"
    }
    
    for display_name, keepa_field in attributes_to_extract.items():
        value = product.get(keepa_field)
        if value is not None and value != "" and value != [] and value != {} and value != -1:
            category_attributes[display_name] = value
    
    # Build response
    return {
        "asin": product.get("asin") or "",
        "brand": product.get("brand") or "",
        "product_title": product.get("title") or "",
        "product_features": features_str,
        "description": product.get("description") or "",
        "aplus_content": aplus_content,
        "main_image_url": main_image_url,
        "gallery_image_urls": gallery_image_urls,
        "category_tree": category_tree,
        "cat_id": cat_id,
        "category_name": category_name,
        "parent_asin": parent_asin,
        "review_count": review_count,
        "rating": rating,
        "sales_rank": sales_rank,
        "price": price,
        "category_attributes": category_attributes if category_attributes else None
    }

# Usage Example
if __name__ == "__main__":
    try:
        # Fetch product details for a hero ASIN
        hero_asin = "B0CJTL53NK"
        country = "US"
        
        product_details = get_basic_product_details(hero_asin, country)
        
        print(f"Product: {product_details['product_title']}")
        print(f"Brand: {product_details['brand']}")
        print(f"Price: ${product_details['price']:.2f}")
        print(f"Rating: {product_details['rating']:.1f}/5.0 ({product_details['review_count']} reviews)")
        print(f"Sales Rank: {product_details['sales_rank']}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
```

### Example 2: FastAPI Integration

```python
from fastapi import FastAPI, HTTPException
from typing import Optional
import os

app = FastAPI()

@app.get("/api/product/{asin}")
async def get_product(asin: str, country: Optional[str] = "US"):
    """
    Get Amazon product details by ASIN
    
    Args:
        asin: Amazon Standard Identification Number
        country: Country code (US, UK, DE, etc.)
    """
    try:
        # Validate ASIN format
        if not asin or len(asin) != 10:
            raise HTTPException(status_code=400, detail="Invalid ASIN format")
        
        # Get product details
        product_data = get_basic_product_details(asin, country)
        
        return {
            "success": True,
            "data": product_data
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch product: {str(e)}")
```

### Example 3: Error Handling and Retry Logic

```python
import time
from typing import Dict, Any, Optional

def get_product_with_retry(
    asin: str, 
    country: str = "US", 
    max_retries: int = 3,
    retry_delay: int = 2
) -> Optional[Dict[str, Any]]:
    """
    Get product details with automatic retry on failure
    
    Args:
        asin: Amazon ASIN
        country: Country code
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds
    
    Returns:
        Product details dict or None if all retries failed
    """
    for attempt in range(max_retries):
        try:
            return get_basic_product_details(asin, country)
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                print(f"All retries exhausted for ASIN: {asin}")
                return None
```

## Response Example

Here's a complete example response from the `get_basic_product_details()` function:

```json
{
  "asin": "B0CJTL53NK",
  "brand": "HUM",
  "product_title": "HUM Best of Berberine Supplement 1200mg - Pure Potency for Metabolic Wellness, Enhanced with BioPerine for Maximum Absorption (60 Capsules)",
  "product_features": "Comprehensive Metabolism and Weight Management Support - Best of Berberine supports metabolic function which helps to maintain healthy cholesterol and lipid levels within normal ranges, while also promoting healthy weight management.|Gut Health and Microbiome Balance – Promotes a balanced gut microbiome by encouraging the growth of beneficial bacteria. BioPerine enhances absorption, supporting berberine's effectiveness for gut and digestive health.|Clinically Tested Efficacious Dose: 1,200 mg of Berberine in just 2 capsules|Blood Sugar Support – Berberine helps optimize glucose metabolism and supports healthy blood sugar levels, contributing to sustained energy and reduced cravings.|Trusted Clean Label Product: 3rd Party Tested, Non GMO, Made in the USA, Vegan",
  "description": "",
  "aplus_content": [
    {
      "fromManufacturer": false,
      "module": [
        {
          "image": [
            "https://m.media-amazon.com/images/S/aplus-media-library-service-media/220dcec5-fe8b-4993-8918-bcbe2c3d8f90.png"
          ],
          "imageAltText": ["b"],
          "text": [
            "Made with 1200 mg of pure Berberine",
            "Higher dose to deliver results",
            "Gain confidence and optimize your results with Best of Berberine, is a 1200 mg formula which has shown in clinical studies to be effective in supporting healthy cholesterol levels + fat metabolism."
          ]
        }
      ]
    }
  ],
  "main_image_url": "https://images-na.ssl-images-amazon.com/images/I/71vA3yXjzZL.jpg",
  "gallery_image_urls": [
    "https://images-na.ssl-images-amazon.com/images/I/81H9RlnEqyL.jpg",
    "https://images-na.ssl-images-amazon.com/images/I/81v5xQjy8LL.jpg",
    "https://images-na.ssl-images-amazon.com/images/I/81PQD8eQnRL.jpg",
    "https://images-na.ssl-images-amazon.com/images/I/81W6V1H9SQL.jpg",
    "https://images-na.ssl-images-amazon.com/images/I/71jKaKW2YZL.jpg"
  ],
  "category_tree": [
    {
      "catId": 121414011,
      "name": "Health & Household"
    },
    {
      "catId": 3760901,
      "name": "Vitamins & Dietary Supplements"
    },
    {
      "catId": 3765321,
      "name": "Herbal Supplements"
    },
    {
      "catId": 3765591,
      "name": "Single Herbal Supplements"
    }
  ],
  "cat_id": 121414011,
  "category_name": "Health & Household",
  "parent_asin": "",
  "review_count": 85,
  "rating": 4.3,
  "sales_rank": 12453,
  "price": 29.99,
  "category_attributes": {
    "itemForm": "Capsule",
    "primarySupplement": "Berberine",
    "unitCount": 60.0,
    "numberOfItems": 1,
    "specificUsesForProduct": "Weight Management, Blood Sugar Support",
    "productBenefit": "Metabolism Support, Gut Health",
    "ingredients": "Berberine HCl, BioPerine (Black Pepper Extract)"
  }
}
```

## Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `asin` | string | Amazon Standard Identification Number |
| `brand` | string | Product brand name |
| `product_title` | string | Full product title |
| `product_features` | string | Key features (pipe-separated) |
| `description` | string | Product description |
| `aplus_content` | array/null | A+ enhanced content (if available) |
| `main_image_url` | string | URL of the main product image |
| `gallery_image_urls` | array | Array of additional product image URLs |
| `category_tree` | array | Hierarchical category path |
| `cat_id` | integer | Root category ID |
| `category_name` | string | Root category name |
| `parent_asin` | string | Parent ASIN for variations |
| `review_count` | integer | Number of customer reviews |
| `rating` | float | Average rating (0-5 scale) |
| `sales_rank` | integer | Current sales rank in category |
| `price` | float | Current price in dollars |
| `category_attributes` | object/null | Category-specific attributes |

## Supported Countries

| Country | Code | Domain ID |
|---------|------|-----------|
| United States | US | 1 |
| United Kingdom | UK/GB | 2 |
| Germany | DE | 3 |
| France | FR | 4 |
| Japan | JP | 5 |
| Canada | CA | 6 |
| Italy | IT | 8 |
| Spain | ES | 9 |
| India | IN | 10 |
| Mexico | MX | 11 |
| Brazil | BR | 12 |
| Australia | AU | 13 |
| Netherlands | NL | 14 |

## Keepa API Parameters Explained

- `aplus: 1` - Include A+ enhanced content
- `stats: 7` - Calculate statistics for the last 7 days
- `rating: 1` - Include rating and review count history
- `domain` - Country-specific Amazon marketplace

## Important Notes

### Data Interpretation

1. **Price**: Keepa returns prices in cents. The function converts to dollars automatically.
2. **Rating**: Keepa uses a 0-50 scale. The function converts to standard 0-5 scale.
3. **No Data**: Keepa uses `-1` to indicate no data available. The function handles this gracefully.
4. **Features**: Multiple features are joined with pipe (`|`) separator for easy parsing.

### ASIN + Country Uniqueness

ASINs are NOT globally unique. The same ASIN can represent different products in different countries with:
- Different pricing and currencies
- Different availability and inventory
- Different descriptions and translations
- Different review counts and ratings
- Different sales rankings
- Different category classifications

Always specify both ASIN and country when fetching product data.

### Rate Limiting

Keepa API has rate limits based on your subscription plan:
- Basic: 100 requests per minute
- Premium: Higher limits based on plan
- Consider implementing caching to reduce API calls

### Best Practices

1. **Cache Results**: Store fetched data for at least 7 days to minimize API calls
2. **Validate ASINs**: Always validate ASIN format before making API calls
3. **Handle Errors**: Implement proper error handling for network issues and API errors
4. **Batch Requests**: Keepa supports multiple ASINs per request (modify the function for batch processing)
5. **Monitor Usage**: Track your API usage to stay within limits

## Troubleshooting

### Common Errors

1. **"Invalid ASIN format"**: ASIN must be exactly 10 alphanumeric characters
2. **"KEEPA_API_KEY not found"**: Set the environment variable with your API key
3. **"No product data found"**: ASIN doesn't exist or is not available in the specified country
4. **"Keepa API error"**: Check your API key validity and subscription status

### Debug Tips

```python
# Enable request debugging
import logging
logging.basicConfig(level=logging.DEBUG)

# Print raw Keepa response
response = requests.get('https://api.keepa.com/product', params=params)
print(response.json())  # Inspect raw response structure
```

## License and Attribution

This code integrates with the Keepa API. You must have a valid Keepa API subscription to use this functionality. Visit [keepa.com](https://keepa.com/#!api) for API access and pricing information.