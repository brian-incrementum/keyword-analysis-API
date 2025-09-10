#!/usr/bin/env python3
"""
Keyword Analysis Script for Amazon Product Keywords
Uses OpenRouter API with Google Gemini 2.5 Flash model to analyze keywords in batches
"""

import asyncio
import aiohttp
import pandas as pd
import json
import os
from typing import List, Dict, Any
import time
from datetime import datetime
from contextlib import nullcontext
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "google/gemini-2.5-flash-lite"  # Using the specified model
BATCH_SIZE = 30
# No limits - send all requests at once
MAX_CONCURRENT_REQUESTS = None

# Load prompt template
def load_prompt_template():
    """Load the prompt template from prompt.txt"""
    with open("prompt.txt", "r") as f:
        content = f.read()
    
    # Extract the prompt_template section
    lines = content.split('\n')
    prompt_lines = []
    in_prompt = False
    
    for line in lines:
        if 'prompt_template:' in line:
            in_prompt = True
            continue
        elif line.startswith('examples:'):
            break
        elif in_prompt:
            # Remove the leading pipe if present
            if line.strip().startswith('|'):
                prompt_lines.append(line.strip()[1:].strip())
            else:
                prompt_lines.append(line)
    
    return '\n'.join(prompt_lines)

def create_batch_prompt(keywords: List[str], prompt_template: str) -> str:
    """Create a batch prompt for multiple keywords"""
    batch_prompt = f"""Analyze the following {len(keywords)} search keywords for Amazon. Process each one individually and return a JSON array with the analysis for each keyword.

Hero Product Details:
ASIN: B018DQI53G
Product title: Thermajohn Long Johns Thermal Underwear for Men Fleece Lined Base Layer Set for Cold Weather (Medium, Black)
Brand: Thermajohn
Rating: 4.6
Review count: 53869
Price: 31.49
Product features: Heat Retention: When it comes to warmth and everyday wear, these long johns for men is designed specifically for you to stay protected from the cold.|Ultra Soft Fleece: Designed with a fleece lining & quality material, these ultra soft mens thermal underwear set will keep you feeling comfortable throughout the day.|Moisture Wicking: Stay dry with these long underwear mens as they're made from breathable fabric that effectively wicks away moisture and perspiration.|4 Way Stretch: Made with stretchable material, these thermals for men allows you freedom of movement with no chafing or bunching up when you move.|Layer Up: Layering is essential to ward off the cold, so bundle up with a pair of mens thermals this winter and stay comfortable while outside or in bed as a pajama.

Task: For each keyword, classify it and score its relevance:
1. Type: generic (general category), our_brand (Thermajohn), competitor_brand (other brands)
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

async def analyze_batch(session: aiohttp.ClientSession, keywords: List[str], prompt_template: str, semaphore: asyncio.Semaphore, batch_num: int = 0) -> List[Dict]:
    """Analyze a batch of keywords using the OpenRouter API"""
    context = semaphore if semaphore else nullcontext()
    async with context:
        batch_prompt = create_batch_prompt(keywords, prompt_template)
        
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:3000",
            "X-Title": "Keyword Analysis Tool"
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
        
        # No retries - send once and handle response
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
                            content = content[7:]  # Remove ```json
                        elif content.startswith('```'):
                            content = content[3:]  # Remove ```
                        if content.endswith('```'):
                            content = content[:-3]  # Remove trailing ```
                        content = content.strip()
                        
                        # Try to parse as JSON array
                        parsed = json.loads(content)
                        if isinstance(parsed, dict) and 'keywords' in parsed:
                            return parsed['keywords']
                        elif isinstance(parsed, list):
                            return parsed
                        else:
                            # If it's a single object, wrap it in a list
                            return [parsed]
                    except json.JSONDecodeError as e:
                        print(f"Error parsing JSON response for batch {batch_num}: {e}")
                        print(f"Response content preview: {content[:200]}...")
                        return []
                else:
                    error_text = await response.text()
                    print(f"✗ Batch {batch_num} API error (status {response.status}): {error_text[:200]}")
                    return []
        except Exception as e:
            print(f"✗ Batch {batch_num} request error: {e}")
            return []

async def process_all_keywords(df: pd.DataFrame, prompt_template: str, test_mode: bool = False, retry_failed: bool = True) -> pd.DataFrame:
    """Process all keywords in the dataframe"""
    # Get keywords from the dataframe
    keywords = df['Search Terms'].tolist()
    
    if test_mode:
        # For testing, only process first 60 keywords (2 batches)
        keywords = keywords[:60]
        print(f"TEST MODE: Processing only {len(keywords)} keywords")
    else:
        print(f"Processing {len(keywords)} keywords total")
    
    # Create batches
    batches = [keywords[i:i + BATCH_SIZE] for i in range(0, len(keywords), BATCH_SIZE)]
    print(f"Created {len(batches)} batches of {BATCH_SIZE} keywords each")
    
    # Create semaphore to limit concurrent requests (or None for unlimited)
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS) if MAX_CONCURRENT_REQUESTS else None
    
    # Process all batches concurrently
    async with aiohttp.ClientSession() as session:
        tasks = []
        for i, batch in enumerate(batches):
            print(f"Preparing batch {i+1}/{len(batches)} with {len(batch)} keywords")
            tasks.append(analyze_batch(session, batch, prompt_template, semaphore, i+1))
        
        print(f"\nSending {len(tasks)} requests to API...")
        start_time = time.time()
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks)
        
        elapsed = time.time() - start_time
        print(f"All requests completed in {elapsed:.2f} seconds")
    
    # Flatten results and create a mapping
    keyword_results = {}
    for batch_result in results:
        if batch_result:
            for item in batch_result:
                if 'keyword' in item:
                    keyword_results[item['keyword'].lower()] = item
    
    # Add results to dataframe with proper data types
    df['keyword_type'] = ''
    df['relevance_score'] = 0  # Initialize as integer
    df['reasoning'] = ''
    
    # Convert to proper types to avoid pandas warnings
    df['relevance_score'] = df['relevance_score'].astype('object')
    
    for idx, row in df.iterrows():
        keyword = row['Search Terms'].lower()
        if keyword in keyword_results:
            result = keyword_results[keyword]
            df.at[idx, 'keyword_type'] = result.get('type', '')
            df.at[idx, 'relevance_score'] = result.get('score', 0)
            df.at[idx, 'reasoning'] = result.get('reasoning', '')
    
    # Retry failed keywords if enabled
    if retry_failed and not test_mode:
        failed_mask = (df['keyword_type'] == '') | (df['relevance_score'] == 0)
        failed_count = failed_mask.sum()
        
        if failed_count > 0:
            print(f"\n{'='*60}")
            print(f"RETRYING {failed_count} FAILED KEYWORDS")
            print(f"{'='*60}")
            
            # Get failed keywords
            failed_keywords = df[failed_mask]['Search Terms'].tolist()
            
            # Create smaller batches for retry (10 keywords each for better success)
            retry_batch_size = 10
            retry_batches = [failed_keywords[i:i + retry_batch_size] 
                           for i in range(0, len(failed_keywords), retry_batch_size)]
            
            print(f"Created {len(retry_batches)} retry batches of {retry_batch_size} keywords each")
            
            # Process retry batches
            async with aiohttp.ClientSession() as session:
                retry_tasks = []
                for i, batch in enumerate(retry_batches):
                    print(f"Preparing retry batch {i+1}/{len(retry_batches)} with {len(batch)} keywords")
                    retry_tasks.append(analyze_batch(session, batch, prompt_template, None, f"R{i+1}"))
                
                print(f"\nSending {len(retry_tasks)} retry requests...")
                retry_start = time.time()
                retry_results = await asyncio.gather(*retry_tasks)
                retry_elapsed = time.time() - retry_start
                print(f"Retry requests completed in {retry_elapsed:.2f} seconds")
                
                # Process retry results
                retry_keyword_results = {}
                for batch_result in retry_results:
                    if batch_result:
                        for item in batch_result:
                            if 'keyword' in item:
                                retry_keyword_results[item['keyword'].lower()] = item
                
                # Update dataframe with retry results
                retry_success = 0
                for idx, row in df[failed_mask].iterrows():
                    keyword = row['Search Terms'].lower()
                    if keyword in retry_keyword_results:
                        result = retry_keyword_results[keyword]
                        df.at[idx, 'keyword_type'] = result.get('type', '')
                        df.at[idx, 'relevance_score'] = result.get('score', 0)
                        df.at[idx, 'reasoning'] = result.get('reasoning', '')
                        retry_success += 1
                
                print(f"Successfully processed {retry_success} keywords on retry")
                remaining_failed = failed_count - retry_success
                if remaining_failed > 0:
                    print(f"Still {remaining_failed} keywords without analysis")
    
    return df

def main():
    """Main function to run the keyword analysis"""
    print("=" * 60)
    print("KEYWORD ANALYSIS TOOL")
    print("=" * 60)
    
    # Check for API key
    if not OPENROUTER_API_KEY:
        print("\n❌ ERROR: Please set your OPENROUTER_API_KEY environment variable")
        print("Example: export OPENROUTER_API_KEY='your-key-here'")
        return
    
    # Load CSV file
    csv_file = "Thermal J Keyword Research - jungle_scout_keywords (6).csv"
    print(f"\nLoading CSV file: {csv_file}")
    df = pd.read_csv(csv_file)
    print(f"Loaded {len(df)} keywords")
    
    # Load prompt template
    print("\nLoading prompt template...")
    prompt_template = load_prompt_template()
    
    # Ask user for test mode
    test_mode = input("\nRun in TEST MODE? (process only 60 keywords) [y/N]: ").lower() == 'y'
    
    # Process keywords
    print(f"\n{'TEST MODE: ' if test_mode else ''}Starting keyword analysis...")
    print(f"Model: {MODEL}")
    print(f"Batch size: {BATCH_SIZE}")
    print(f"Concurrent requests: {'UNLIMITED - All at once!' if MAX_CONCURRENT_REQUESTS is None else MAX_CONCURRENT_REQUESTS}")
    print("-" * 60)
    
    # Run async processing
    df_result = asyncio.run(process_all_keywords(df, prompt_template, test_mode=test_mode))
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"keyword_analysis_results_{timestamp}{'_test' if test_mode else ''}.csv"
    df_result.to_csv(output_file, index=False)
    
    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE!")
    print(f"Results saved to: {output_file}")
    
    # Show summary statistics
    if 'keyword_type' in df_result.columns:
        print("\nSummary Statistics:")
        print("-" * 40)
        type_counts = df_result['keyword_type'].value_counts()
        print("\nKeyword Types:")
        for ktype, count in type_counts.items():
            if ktype:  # Only show non-empty types
                print(f"  {ktype}: {count}")
        
        if 'relevance_score' in df_result.columns:
            # Convert to numeric for comparison
            df_result['relevance_score'] = pd.to_numeric(df_result['relevance_score'], errors='coerce').fillna(0).astype(int)
            scores = df_result[df_result['relevance_score'] > 0]['relevance_score']
            if len(scores) > 0:
                print(f"\nRelevance Scores:")
                print(f"  Average: {scores.mean():.2f}")
                print(f"  Min: {scores.min()}")
                print(f"  Max: {scores.max()}")
                print(f"  Analyzed: {len(scores)} keywords")
                print(f"  Not analyzed: {len(df_result) - len(scores)} keywords")
    
    print("=" * 60)

if __name__ == "__main__":
    main()