"""
Keyword analysis module using OpenRouter API
"""
import asyncio
import aiohttp
import json
import os
from typing import List, Dict, Any, Optional
from contextlib import nullcontext
from dotenv import load_dotenv
from models import ProductDetails, KeywordResult

# Load environment variables
load_dotenv()

# Configuration
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = os.environ.get("OPENROUTER_MODEL", "google/gemini-2.5-flash-lite")
BATCH_SIZE = int(os.environ.get("BATCH_SIZE", 30))
# 0 means no limit - send all requests at once
MAX_CONCURRENT_REQUESTS = int(os.environ.get("MAX_CONCURRENT_REQUESTS", 0))


def create_batch_prompt_with_details(keywords: List[str], product_details: ProductDetails) -> str:
    """Create a batch prompt for multiple keywords using structured product details"""
    
    # Build product details string from Keepa data
    product_info = f"""Hero Product Details:
ASIN: {product_details.asin or 'N/A'}
Product title: {product_details.product_title or 'N/A'}
Brand: {product_details.brand or 'N/A'}
Rating: {product_details.rating or 'N/A'}
Review count: {product_details.review_count or 'N/A'}
Price: {product_details.price or 'N/A'}
Product features: {product_details.product_features or 'N/A'}"""
    
    batch_prompt = f"""Analyze the following {len(keywords)} search keywords for Amazon. Process each one individually and return a JSON array with the analysis for each keyword.

{product_info}

Task: For each keyword, classify it and score its relevance:
1. Type: generic (general category), our_brand ({product_details.brand or 'brand'}), competitor_brand (other brands)
2. Score: 1-10 relevance (1-3: low, 4-6: medium, 7-9: high, 10: perfect match)

Keywords to analyze:
{json.dumps(keywords, indent=2)}

Return ONLY a valid JSON array with one object per keyword:
[
  {{
    "keyword": "keyword text",
    "type": "generic|our_brand|competitor_brand",
    "score": 1-10,
    "reasoning": "brief explanation"
  }},
  ...
]"""
    
    return batch_prompt


def create_batch_prompt_with_description(keywords: List[str], description: str) -> str:
    """Create a batch prompt for multiple keywords using text description"""
    
    batch_prompt = f"""Analyze the following {len(keywords)} search keywords for Amazon. Process each one individually and return a JSON array with the analysis for each keyword.

Product Description:
{description}

Task: For each keyword, classify it and score its relevance to the product described above:
1. Type: generic (general category), our_brand (if brand mentioned in description), competitor_brand (other brands)
2. Score: 1-10 relevance (1-3: low, 4-6: medium, 7-9: high, 10: perfect match)

Keywords to analyze:
{json.dumps(keywords, indent=2)}

Return ONLY a valid JSON array with one object per keyword:
[
  {{
    "keyword": "keyword text",
    "type": "generic|our_brand|competitor_brand",
    "score": 1-10,
    "reasoning": "brief explanation"
  }},
  ...
]"""
    
    return batch_prompt


async def analyze_batch(
    session: aiohttp.ClientSession, 
    keywords: List[str], 
    product_details: Optional[ProductDetails] = None,
    product_description: Optional[str] = None,
    semaphore: Optional[asyncio.Semaphore] = None, 
    batch_num: int = 0
) -> List[Dict]:
    """Analyze a batch of keywords using the OpenRouter API"""
    
    context = semaphore if semaphore else nullcontext()
    async with context:
        # Create appropriate prompt based on input type
        if product_details and product_details.asin:
            batch_prompt = create_batch_prompt_with_details(keywords, product_details)
        elif product_description:
            batch_prompt = create_batch_prompt_with_description(keywords, product_description)
        else:
            raise ValueError("Either product_details or product_description must be provided")
        
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "Keyword Analysis API"
        }
        
        payload = {
            "model": MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": batch_prompt
                }
            ],
            "temperature": 0.3,
            "max_tokens": 4000
        }
        
        try:
            async with session.post(OPENROUTER_API_URL, json=payload, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    content = result['choices'][0]['message']['content']
                    print(f"✓ Batch {batch_num} completed successfully")
                    
                    # Parse the JSON response
                    try:
                        # Remove markdown code blocks if present
                        if content.startswith('```json'):
                            content = content[7:]
                        elif content.startswith('```'):
                            content = content[3:]
                        if content.endswith('```'):
                            content = content[:-3]
                        content = content.strip()
                        
                        # Try to parse as JSON array
                        parsed = json.loads(content)
                        if isinstance(parsed, dict) and 'keywords' in parsed:
                            return parsed['keywords']
                        elif isinstance(parsed, list):
                            return parsed
                        else:
                            return [parsed]
                    except json.JSONDecodeError as e:
                        print(f"Error parsing JSON response for batch {batch_num}: {e}")
                        return []
                else:
                    error_text = await response.text()
                    print(f"✗ Batch {batch_num} API error (status {response.status}): {error_text[:200]}")
                    return []
        except Exception as e:
            print(f"✗ Batch {batch_num} request error: {e}")
            return []


async def analyze_keywords(
    keywords: List[str],
    product_details: Optional[ProductDetails] = None,
    product_description: Optional[str] = None,
    retry_failed: bool = True
) -> List[KeywordResult]:
    """
    Analyze keywords for relevance to a product
    
    Args:
        keywords: List of keywords to analyze
        product_details: Structured product details (from Keepa)
        product_description: Text description of product
        retry_failed: Whether to retry failed keywords
    
    Returns:
        List of KeywordResult objects
    """
    
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY not found in environment variables")
    
    if not product_details and not product_description:
        raise ValueError("Either product_details or product_description must be provided")
    
    print(f"Processing {len(keywords)} keywords total")
    
    # Create batches
    batches = [keywords[i:i + BATCH_SIZE] for i in range(0, len(keywords), BATCH_SIZE)]
    print(f"Created {len(batches)} batches of up to {BATCH_SIZE} keywords each")
    
    # Create semaphore to limit concurrent requests (None = no limit, send all at once)
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS) if MAX_CONCURRENT_REQUESTS > 0 else None
    
    if not semaphore:
        print("No concurrency limit - sending all requests at once!")
    
    # Process all batches concurrently
    async with aiohttp.ClientSession() as session:
        tasks = []
        for i, batch in enumerate(batches):
            tasks.append(analyze_batch(
                session, 
                batch, 
                product_details=product_details,
                product_description=product_description,
                semaphore=semaphore, 
                batch_num=i+1
            ))
        
        print(f"\nSending {len(tasks)} requests to API...")
        results = await asyncio.gather(*tasks)
    
    # Convert results to KeywordResult objects
    keyword_results = []
    failed_keywords = []
    
    # Create a mapping of processed keywords
    processed_keywords = {}
    for batch_result in results:
        if batch_result:
            for item in batch_result:
                if 'keyword' in item:
                    processed_keywords[item['keyword'].lower()] = item
    
    # Map results back to original keywords
    for keyword in keywords:
        keyword_lower = keyword.lower()
        if keyword_lower in processed_keywords:
            result = processed_keywords[keyword_lower]
            # Ensure score is within valid range (1-10)
            score = result.get('score', 5)
            if isinstance(score, (int, float)):
                score = max(1, min(10, int(score)))  # Clamp between 1 and 10
            else:
                score = 5  # Default if not a number
            
            keyword_results.append(KeywordResult(
                keyword=keyword,
                type=result.get('type', 'generic'),
                score=score,
                reasoning=result.get('reasoning', '')
            ))
        else:
            failed_keywords.append(keyword)
    
    # Retry failed keywords if enabled
    if retry_failed and failed_keywords:
        print(f"\nRetrying {len(failed_keywords)} failed keywords...")
        
        # Create smaller batches for retry
        retry_batch_size = 10
        retry_batches = [failed_keywords[i:i + retry_batch_size] 
                        for i in range(0, len(failed_keywords), retry_batch_size)]
        
        async with aiohttp.ClientSession() as session:
            retry_tasks = []
            for i, batch in enumerate(retry_batches):
                retry_tasks.append(analyze_batch(
                    session, 
                    batch,
                    product_details=product_details,
                    product_description=product_description,
                    semaphore=None, 
                    batch_num=f"R{i+1}"
                ))
            
            retry_results = await asyncio.gather(*retry_tasks)
            
            # Process retry results
            retry_processed = {}
            for batch_result in retry_results:
                if batch_result:
                    for item in batch_result:
                        if 'keyword' in item:
                            retry_processed[item['keyword'].lower()] = item
            
            # Update results with successful retries
            for keyword in failed_keywords:
                keyword_lower = keyword.lower()
                if keyword_lower in retry_processed:
                    result = retry_processed[keyword_lower]
                    # Ensure score is within valid range (1-10)
                    score = result.get('score', 5)
                    if isinstance(score, (int, float)):
                        score = max(1, min(10, int(score)))  # Clamp between 1 and 10
                    else:
                        score = 5  # Default if not a number
                    
                    keyword_results.append(KeywordResult(
                        keyword=keyword,
                        type=result.get('type', 'generic'),
                        score=score,
                        reasoning=result.get('reasoning', '')
                    ))
    
    return keyword_results