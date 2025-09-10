"""
Keepa API integration for fetching Amazon product details
"""
import os
import requests
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Country to Keepa domain ID mapping
COUNTRY_TO_DOMAIN = {
    "US": 1,  "GB": 2,  "UK": 2,  "DE": 3,  "FR": 4,
    "JP": 5,  "CA": 6,  "IT": 8,  "ES": 9,  "IN": 10,
    "MX": 11, "BR": 12, "AU": 13, "NL": 14
}


def get_basic_product_details(asin: str, country: str = "US") -> Dict[str, Any]:
    """
    Get product details from Keepa API
    
    Args:
        asin: Amazon Standard Identification Number (10-character alphanumeric code)
        country: Country code for Amazon marketplace (default: "US")
    
    Returns:
        Dictionary containing product details
    
    Raises:
        ValueError: If ASIN format is invalid or API key not found
        Exception: If Keepa API returns an error or no product data found
    """
    
    # Validate ASIN
    if not asin or len(asin) != 10:
        raise ValueError("Invalid ASIN format")
    
    # Get API key from environment
    KEEPA_API_KEY = os.environ.get("KEEPA_API_KEY")
    if not KEEPA_API_KEY or KEEPA_API_KEY == "your_keepa_api_key_here":
        raise ValueError("Valid KEEPA_API_KEY not found in environment variables")
    
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
    
    try:
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
    
    except requests.RequestException as e:
        raise Exception(f"Failed to connect to Keepa API: {str(e)}")
    except Exception as e:
        raise Exception(f"Error fetching product details: {str(e)}")