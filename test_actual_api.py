#!/usr/bin/env python3
"""
Test the actual API endpoint with the real CSV to diagnose the issue
"""
import requests
import csv
import json

# Load keywords from CSV
csv_file = "/Users/brian/Desktop/Coding/keyword-analysis-API/Thermal J Keyword Research -full set.csv"
keywords = []

with open(csv_file, 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        keywords.append(row['Search Terms'])

print(f"Loaded {len(keywords)} keywords from CSV")

# Test with the actual API
api_url = "http://localhost:8000/analyze-keywords"

# Prepare request with a test description
request_data = {
    "product_description": "Men's thermal underwear set for cold weather. High-quality thermal long johns and base layer clothing.",
    "keywords": keywords
}

print(f"\nSending {len(keywords)} keywords to API...")
print("This will take a moment...")

try:
    response = requests.post(api_url, json=request_data, timeout=120)
    
    if response.status_code == 200:
        result = response.json()
        
        print("\n" + "="*60)
        print("API RESPONSE ANALYSIS")
        print("="*60)
        
        # Check summary
        summary = result.get('summary', {})
        print(f"\nSummary from API:")
        print(f"  Total keywords sent: {summary.get('total_keywords', 'N/A')}")
        print(f"  Keywords analyzed: {summary.get('analyzed', 'N/A')}")
        print(f"  Failed keywords: {summary.get('failed', 'N/A')}")
        print(f"  Processing time: {summary.get('processing_time', 'N/A')}s")
        
        # Check actual results
        analysis_results = result.get('analysis_results', [])
        print(f"\nActual results received: {len(analysis_results)}")
        
        # Find missing keywords
        received_keywords = {r['keyword'].lower() for r in analysis_results}
        sent_keywords = {k.lower() for k in keywords}
        
        missing = sent_keywords - received_keywords
        print(f"\nMissing keywords: {len(missing)}")
        
        if missing and len(missing) < 50:  # Show first 50 missing
            print("\nFirst missing keywords:")
            for i, keyword in enumerate(list(missing)[:50]):
                print(f"  {i+1}. {keyword}")
        
        # Check for errors
        errors = result.get('errors', [])
        if errors:
            print(f"\nErrors reported: {errors}")
        
        # Calculate the discrepancy
        print("\n" + "="*60)
        print("DIAGNOSIS")
        print("="*60)
        expected = len(keywords)
        actual = len(analysis_results)
        loss_rate = ((expected - actual) / expected) * 100
        
        print(f"\n❌ DATA LOSS CONFIRMED!")
        print(f"  Expected: {expected} keywords")
        print(f"  Received: {actual} keywords")
        print(f"  Lost: {expected - actual} keywords ({loss_rate:.1f}%)")
        
        # Save full response for debugging
        with open('api_response_debug.json', 'w') as f:
            json.dump(result, f, indent=2)
        print("\nFull response saved to api_response_debug.json for debugging")
        
    else:
        print(f"\n❌ API Error: {response.status_code}")
        print(f"Response: {response.text[:500]}")
        
except requests.exceptions.Timeout:
    print("\n❌ Request timed out after 120 seconds")
except Exception as e:
    print(f"\n❌ Error: {e}")