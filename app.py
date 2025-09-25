"""
FastAPI application for keyword analysis
"""
import asyncio
import time
from typing import List, Optional
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

from models import (
    KeywordAnalysisRequest,
    KeywordAnalysisResponse,
    ProductDetails,
    AnalysisSummary,
    RootAnalysisRequest,
    RootAnalysisResponse,
)
from keepa_client import get_basic_product_details
from keyword_analyzer import analyze_keywords
from root_analysis_service import generate_root_analysis

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="Keyword Analysis API",
    description="Analyze Amazon keywords for product relevance using AI",
    version="1.0.0"
)

# Configure CORS - use environment variable for frontend URL
frontend_url = os.environ.get("FRONTEND_URL", "*")
allowed_origins = [frontend_url] if frontend_url != "*" else ["*"]

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Keyword Analysis API",
        "version": "1.0.0",
        "endpoints": {
            "POST /analyze-keywords": "Analyze keywords for product relevance",
            "POST /root-analysis": "Generate normalized root keywords from CSV data",
        },
        "documentation": "/docs"
    }


@app.post("/analyze-keywords", response_model=KeywordAnalysisResponse)
async def analyze_keywords_endpoint(request: KeywordAnalysisRequest):
    """
    Analyze keywords for product relevance
    
    Accepts either:
    1. ASIN + country (fetches product details from Keepa)
    2. Product description text (uses directly for analysis)
    """
    
    # Validate input type
    try:
        request.validate_input_type()
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    
    # Start timing
    start_time = time.time()
    
    # Determine input type and prepare product details
    input_type = "asin" if request.asin else "description"
    product_details = None
    product_description = None
    errors = []
    
    try:
        if input_type == "asin":
            # Fetch product details from Keepa
            print(f"Fetching product details for ASIN: {request.asin}")
            try:
                keepa_data = get_basic_product_details(request.asin, request.country)
                product_details = ProductDetails(**keepa_data)
            except Exception as e:
                # If Keepa fails, return error
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Failed to fetch product details from Keepa: {str(e)}"
                )
        else:
            # Use provided description
            product_description = request.product_description
            product_details = ProductDetails(raw_description=product_description)
        
        # Analyze keywords
        print(f"Analyzing {len(request.keywords)} keywords...")
        analysis_results = await analyze_keywords(
            keywords=request.keywords,
            product_details=product_details if input_type == "asin" else None,
            product_description=product_description if input_type == "description" else None,
            retry_failed=True
        )
        
        # Calculate summary statistics
        analyzed_count = len(analysis_results)
        failed_count = len(request.keywords) - analyzed_count
        
        # Count by type
        by_type = {}
        total_score = 0
        for result in analysis_results:
            by_type[result.type] = by_type.get(result.type, 0) + 1
            total_score += result.score
        
        # Calculate average score
        average_score = total_score / analyzed_count if analyzed_count > 0 else 0
        
        # Processing time
        processing_time = time.time() - start_time
        
        # Create summary
        summary = AnalysisSummary(
            total_keywords=len(request.keywords),
            analyzed=analyzed_count,
            failed=failed_count,
            by_type=by_type,
            average_score=round(average_score, 2) if average_score > 0 else None,
            processing_time=round(processing_time, 2)
        )
        
        # Add any failed keywords to errors
        if failed_count > 0:
            failed_keywords = set(request.keywords) - {r.keyword for r in analysis_results}
            errors.append(f"Failed to analyze {failed_count} keywords: {', '.join(list(failed_keywords)[:10])}")
        
        # Create response
        response = KeywordAnalysisResponse(
            input_type=input_type,
            product_info=product_details,
            analysis_results=analysis_results,
            summary=summary,
            errors=errors if errors else None
        )
        
        print(f"Analysis complete in {processing_time:.2f} seconds")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error during analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )


@app.post("/root-analysis", response_model=RootAnalysisResponse)
async def root_analysis_endpoint(request: RootAnalysisRequest):
    """Aggregate uploaded keyword rows into normalized roots."""

    rows = [(row.keyword.strip(), row.search_volume) for row in request.keywords if row.keyword.strip()]
    if not rows:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No valid keywords supplied")

    try:
        payload = generate_root_analysis(rows, request.mode)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - safeguard for unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Root analysis failed: {str(exc)}"
        ) from exc

    return RootAnalysisResponse(**payload)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    # Check if required API keys are configured
    openrouter_configured = bool(os.environ.get("OPENROUTER_API_KEY"))
    keepa_configured = bool(os.environ.get("KEEPA_API_KEY")) and os.environ.get("KEEPA_API_KEY") != "your_keepa_api_key_here"
    
    max_concurrent = os.environ.get("MAX_CONCURRENT_REQUESTS", "0")
    concurrency_desc = "unlimited (all at once)" if max_concurrent == "0" else max_concurrent
    
    return {
        "status": "healthy",
        "configuration": {
            "openrouter_api_key": "configured" if openrouter_configured else "missing",
            "keepa_api_key": "configured" if keepa_configured else "missing",
            "model": os.environ.get("OPENROUTER_MODEL", "google/gemini-2.5-flash-lite"),
            "batch_size": os.environ.get("BATCH_SIZE", 30),
            "max_concurrent_requests": concurrency_desc
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    # Run the FastAPI app
    print("Starting Keyword Analysis API...")
    print("Documentation available at: http://localhost:8000/docs")
    print("Health check at: http://localhost:8000/health")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True
    )
