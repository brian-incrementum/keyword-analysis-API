#!/usr/bin/env python3
"""
Test the backend logic directly to find where keywords are lost
"""
import csv
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from keyword_analyzer import analyze_keywords
from models import ProductDetails

# Load keywords from CSV
csv_file = "/Users/brian/Desktop/Coding/keyword-analysis-API/Thermal J Keyword Research -full set.csv"
keywords = []

with open(csv_file, 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        keywords.append(row['Search Terms'])

print(f"Loaded {len(keywords)} keywords from CSV")

# Remove duplicates (like the API does)
seen = set()
unique_keywords = []
for keyword in keywords:
    keyword_lower = keyword.lower().strip()
    if keyword_lower and keyword_lower not in seen:
        seen.add(keyword_lower)
        unique_keywords.append(keyword.strip())

print(f"After deduplication: {len(unique_keywords)} unique keywords")

async def test_analysis():
    """Test the keyword analysis function directly"""
    
    print(f"\nTesting keyword_analyzer.analyze_keywords with {len(unique_keywords)} keywords...")
    
    # Use a simple product description
    product_description = "Men's thermal underwear set for cold weather"
    
    try:
        results = await analyze_keywords(
            keywords=unique_keywords,
            product_details=None,
            product_description=product_description,
            retry_failed=True
        )
        
        print(f"\n" + "="*60)
        print("RESULTS")
        print("="*60)
        print(f"Keywords sent: {len(unique_keywords)}")
        print(f"Results received: {len(results)}")
        print(f"Keywords lost: {len(unique_keywords) - len(results)}")
        
        if len(results) < len(unique_keywords):
            # Find which keywords were lost
            result_keywords = {r.keyword.lower() for r in results}
            sent_keywords = {k.lower() for k in unique_keywords}
            missing = sent_keywords - result_keywords
            
            print(f"\n❌ KEYWORDS LOST: {len(missing)}")
            
            # Show sample of missing keywords
            if missing:
                print("\nFirst 20 missing keywords:")
                for i, keyword in enumerate(list(missing)[:20]):
                    # Find original case
                    orig = next((k for k in unique_keywords if k.lower() == keyword), keyword)
                    print(f"  {i+1}. '{orig}'")
        
        return results
        
    except Exception as e:
        print(f"\n❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        return []

# Run the test
if __name__ == "__main__":
    results = asyncio.run(test_analysis())
    
    if results:
        print(f"\n✅ Test completed - {len(results)} keywords processed")