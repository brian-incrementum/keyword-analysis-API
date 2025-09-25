#!/usr/bin/env python3
"""
Test script to verify if concurrent requests are causing failures
"""
import asyncio
import aiohttp
import json
import os
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = os.environ.get("OPENROUTER_MODEL", "google/gemini-2.5-flash-lite")

# Test configuration
TEST_BATCH_SIZE = 30
TEST_TOTAL_BATCHES = 10  # Test with 10 batches first

async def test_batch(session, batch_num, test_keywords):
    """Send a test batch to OpenRouter API"""
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8000",
        "X-Title": "Keyword Analysis API Test"
    }
    
    # Simple test prompt
    prompt = f"""Analyze these {len(test_keywords)} keywords. Return a JSON array with one object per keyword:
Keywords: {json.dumps(test_keywords)}

Return format:
[{{"keyword": "word", "type": "generic", "score": 5, "reasoning": "test"}}]"""
    
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 2000
    }
    
    start_time = time.time()
    try:
        async with session.post(OPENROUTER_API_URL, json=payload, headers=headers) as response:
            elapsed = time.time() - start_time
            if response.status == 200:
                result = await response.json()
                return {
                    "batch": batch_num,
                    "status": "success",
                    "http_status": 200,
                    "time": elapsed,
                    "keywords_sent": len(test_keywords)
                }
            else:
                error_text = await response.text()
                return {
                    "batch": batch_num,
                    "status": "failed",
                    "http_status": response.status,
                    "error": error_text[:200],
                    "time": elapsed
                }
    except Exception as e:
        elapsed = time.time() - start_time
        return {
            "batch": batch_num,
            "status": "error",
            "error": str(e),
            "time": elapsed
        }

async def run_concurrent_test(num_concurrent_batches):
    """Run test with specified number of concurrent batches"""
    
    print(f"\n{'='*60}")
    print(f"Testing with {num_concurrent_batches} CONCURRENT batches")
    print(f"{'='*60}")
    
    # Generate test keywords
    test_keywords_per_batch = []
    for i in range(num_concurrent_batches):
        batch_keywords = [f"thermal underwear test {i}_{j}" for j in range(TEST_BATCH_SIZE)]
        test_keywords_per_batch.append(batch_keywords)
    
    # Send all batches concurrently
    async with aiohttp.ClientSession() as session:
        start_time = time.time()
        tasks = []
        for i, keywords in enumerate(test_keywords_per_batch):
            tasks.append(test_batch(session, i+1, keywords))
        
        print(f"Sending {num_concurrent_batches} batches simultaneously...")
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time
    
    # Analyze results
    successful = sum(1 for r in results if r["status"] == "success")
    failed = sum(1 for r in results if r["status"] == "failed")
    errors = sum(1 for r in results if r["status"] == "error")
    
    print(f"\nResults:")
    print(f"  Total time: {total_time:.2f}s")
    print(f"  Successful: {successful}/{num_concurrent_batches}")
    print(f"  Failed: {failed}/{num_concurrent_batches}")
    print(f"  Errors: {errors}/{num_concurrent_batches}")
    
    if failed > 0 or errors > 0:
        print("\nFailed/Error batches:")
        for r in results:
            if r["status"] != "success":
                print(f"  Batch {r['batch']}: Status {r.get('http_status', 'N/A')} - {r.get('error', 'Unknown error')[:100]}")
    
    return results, successful, failed, errors

async def main():
    """Main test function"""
    
    if not OPENROUTER_API_KEY:
        print("ERROR: OPENROUTER_API_KEY not found in .env")
        return
    
    print("OpenRouter Concurrent Request Test")
    print(f"Model: {MODEL}")
    print(f"Batch size: {TEST_BATCH_SIZE} keywords per batch")
    
    # Test with increasing concurrent loads
    test_scenarios = [10, 50, 100, 200]
    
    for num_batches in test_scenarios:
        results, successful, failed, errors = await run_concurrent_test(num_batches)
        
        # Calculate success rate
        success_rate = (successful / num_batches) * 100
        print(f"  Success rate: {success_rate:.1f}%")
        
        # If we start seeing failures, note it
        if success_rate < 90:
            print(f"\n⚠️  FOUND LIMIT: Performance degrades at {num_batches} concurrent requests")
            print(f"  Only {successful} out of {num_batches} batches succeeded")
            break
        
        # Wait a bit between tests to avoid any rate limit windows
        if num_batches < test_scenarios[-1]:
            print("\nWaiting 5 seconds before next test...")
            await asyncio.sleep(5)
    
    # Test your actual scenario (224 batches)
    print(f"\n{'='*60}")
    print("TESTING YOUR ACTUAL SCENARIO: 224 concurrent batches")
    print(f"{'='*60}")
    
    results, successful, failed, errors = await run_concurrent_test(224)
    success_rate = (successful / 224) * 100
    
    print(f"\n📊 FINAL VERDICT:")
    print(f"  Success rate with 224 concurrent requests: {success_rate:.1f}%")
    print(f"  Keywords that would be processed: {successful * TEST_BATCH_SIZE} out of {224 * TEST_BATCH_SIZE}")
    
    if success_rate < 90:
        print(f"\n❌ This explains your issue! Only ~{success_rate:.0f}% of batches succeed")
        print(f"  This matches your observation: ~{successful * TEST_BATCH_SIZE} keywords processed")
    else:
        print("\n✅ Concurrent requests are NOT the issue - need to investigate further")

if __name__ == "__main__":
    asyncio.run(main())