#!/usr/bin/env python3
"""
Diagnostic script to identify why keywords are being lost
"""
import asyncio
import aiohttp
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = os.environ.get("OPENROUTER_MODEL", "google/gemini-2.5-flash-lite")

# Test with sample keywords from your CSV
TEST_KEYWORDS = [
    "thermal underwears",
    "winter underwear thermal men",
    "men's long john",
    "thermal underwear￼",  # Note: has special character
    "thermal mens underwear",
    "men's long johns",  # Note: has apostrophe
    "mens long johns bottoms",
    "insulated underwear for men",
    "men's thermal underwear bottoms",
    "men thermal underwear"
]

async def test_api_response():
    """Test what the API actually returns for keywords"""
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8000",
        "X-Title": "Keyword Analysis Diagnostic"
    }
    
    prompt = f"""Analyze these {len(TEST_KEYWORDS)} keywords. Return a JSON array with one object per keyword.
Product: Generic thermal underwear for men

Keywords to analyze:
{json.dumps(TEST_KEYWORDS, indent=2)}

Return ONLY a valid JSON array:
[
  {{
    "keyword": "exact keyword text as provided",
    "type": "generic|our_brand|competitor_brand",
    "score": 1-10,
    "reasoning": "brief explanation"
  }}
]"""
    
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 2000
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(OPENROUTER_API_URL, json=payload, headers=headers) as response:
            if response.status == 200:
                result = await response.json()
                content = result['choices'][0]['message']['content']
                
                # Clean up response
                if content.startswith('```json'):
                    content = content[7:]
                elif content.startswith('```'):
                    content = content[3:]
                if content.endswith('```'):
                    content = content[:-3]
                content = content.strip()
                
                try:
                    parsed = json.loads(content)
                    return parsed
                except json.JSONDecodeError as e:
                    print(f"Failed to parse JSON: {e}")
                    print(f"Raw content: {content}")
                    return None
            else:
                error = await response.text()
                print(f"API error: {error}")
                return None

def analyze_differences(original_keywords, api_response):
    """Compare original keywords with API response"""
    
    if not api_response:
        print("No API response to analyze")
        return
    
    print("\n" + "="*60)
    print("KEYWORD MATCHING ANALYSIS")
    print("="*60)
    
    # Create mapping like the actual code does
    processed_keywords = {}
    for item in api_response:
        if 'keyword' in item:
            processed_keywords[item['keyword'].lower()] = item
    
    print(f"\nOriginal keywords sent: {len(original_keywords)}")
    print(f"Keywords in API response: {len(api_response)}")
    print(f"Unique processed keywords (lowercase): {len(processed_keywords)}")
    
    # Check which keywords match
    matched = []
    unmatched = []
    
    for orig_keyword in original_keywords:
        keyword_lower = orig_keyword.lower()
        if keyword_lower in processed_keywords:
            matched.append(orig_keyword)
        else:
            unmatched.append(orig_keyword)
    
    print(f"\nMatched keywords: {len(matched)}/{len(original_keywords)}")
    print(f"Unmatched keywords: {len(unmatched)}/{len(original_keywords)}")
    
    if unmatched:
        print("\n⚠️  UNMATCHED KEYWORDS (would be lost):")
        for keyword in unmatched:
            print(f"  - '{keyword}'")
            # Try to find similar keywords in response
            for api_item in api_response:
                api_keyword = api_item.get('keyword', '')
                if keyword.lower() in api_keyword.lower() or api_keyword.lower() in keyword.lower():
                    print(f"    → API returned: '{api_keyword}'")
    
    print("\n📊 API RESPONSE KEYWORDS:")
    for item in api_response:
        orig_keyword = item.get('keyword', 'MISSING')
        print(f"  - '{orig_keyword}'")
        
        # Check for modifications
        found_original = False
        for orig in original_keywords:
            if orig.lower() == orig_keyword.lower():
                found_original = True
                if orig != orig_keyword:
                    print(f"    ⚠️  Case changed: '{orig}' → '{orig_keyword}'")
                break
        
        if not found_original:
            print(f"    ❌ NOT in original list or modified!")

async def main():
    """Run diagnostic"""
    
    print("Keyword Processing Diagnostic")
    print(f"Testing with {len(TEST_KEYWORDS)} sample keywords")
    
    # Get API response
    print("\nCalling API...")
    api_response = await test_api_response()
    
    if api_response:
        # Analyze differences
        analyze_differences(TEST_KEYWORDS, api_response)
        
        # Show the issue
        print("\n" + "="*60)
        print("DIAGNOSIS SUMMARY")
        print("="*60)
        print("\nThe issue is likely one of these:")
        print("1. API is not returning keywords exactly as sent")
        print("2. Special characters (like ￼) are being modified")
        print("3. API might be skipping or combining similar keywords")
        print("4. Response parsing is failing for some batches")
    else:
        print("\n❌ Failed to get API response for analysis")

if __name__ == "__main__":
    asyncio.run(main())