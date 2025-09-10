"""
Pydantic models for the keyword analysis API
"""
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, validator


class KeywordAnalysisWithASIN(BaseModel):
    """Request model when user provides ASIN"""
    asin: str = Field(..., min_length=10, max_length=10, description="Amazon Standard Identification Number")
    country: str = Field(default="US", description="Country code for Amazon marketplace")
    keywords: List[str] = Field(..., min_items=1, description="List of keywords to analyze")
    
    @validator('asin')
    def validate_asin(cls, v):
        if not v.isalnum():
            raise ValueError("ASIN must be alphanumeric")
        return v.upper()
    
    @validator('country')
    def validate_country(cls, v):
        valid_countries = ["US", "GB", "UK", "DE", "FR", "JP", "CA", "IT", "ES", "IN", "MX", "BR", "AU", "NL"]
        if v.upper() not in valid_countries:
            raise ValueError(f"Country must be one of: {', '.join(valid_countries)}")
        return v.upper()


class KeywordAnalysisWithDescription(BaseModel):
    """Request model when user provides product description"""
    product_description: str = Field(..., min_length=10, description="Text description of the product")
    keywords: List[str] = Field(..., min_items=1, description="List of keywords to analyze")


class KeywordAnalysisRequest(BaseModel):
    """Union request model that accepts either ASIN or product description"""
    asin: Optional[str] = Field(None, min_length=10, max_length=10)
    country: Optional[str] = Field(default="US")
    product_description: Optional[str] = Field(None, min_length=10)
    keywords: List[str] = Field(..., min_items=1, description="List of keywords to analyze")
    
    @validator('keywords')
    def validate_keywords(cls, v):
        # Remove duplicates while preserving order
        seen = set()
        unique_keywords = []
        for keyword in v:
            keyword_lower = keyword.lower().strip()
            if keyword_lower and keyword_lower not in seen:
                seen.add(keyword_lower)
                unique_keywords.append(keyword.strip())
        return unique_keywords
    
    @validator('asin', pre=True)
    def validate_asin(cls, v):
        if v and not v.isalnum():
            raise ValueError("ASIN must be alphanumeric")
        return v.upper() if v else v
    
    @validator('country')
    def validate_country(cls, v):
        valid_countries = ["US", "GB", "UK", "DE", "FR", "JP", "CA", "IT", "ES", "IN", "MX", "BR", "AU", "NL"]
        if v and v.upper() not in valid_countries:
            raise ValueError(f"Country must be one of: {', '.join(valid_countries)}")
        return v.upper() if v else v
    
    def validate_input_type(self):
        """Validate that either ASIN or product_description is provided, but not both"""
        if self.asin and self.product_description:
            raise ValueError("Provide either ASIN or product_description, not both")
        if not self.asin and not self.product_description:
            raise ValueError("Either ASIN or product_description must be provided")
        return True


class ProductDetails(BaseModel):
    """Product details model (from Keepa or user description)"""
    asin: Optional[str] = None
    brand: Optional[str] = None
    product_title: Optional[str] = None
    product_features: Optional[str] = None
    description: Optional[str] = None
    main_image_url: Optional[str] = None
    gallery_image_urls: Optional[List[str]] = None
    category_tree: Optional[List[Dict[str, Any]]] = None
    cat_id: Optional[int] = None
    category_name: Optional[str] = None
    parent_asin: Optional[str] = None
    review_count: Optional[int] = None
    rating: Optional[float] = None
    sales_rank: Optional[int] = None
    price: Optional[float] = None
    category_attributes: Optional[Dict[str, Any]] = None
    # For text description input
    raw_description: Optional[str] = None


class KeywordResult(BaseModel):
    """Individual keyword analysis result"""
    keyword: str
    type: str = Field(..., description="Classification: generic, our_brand, or competitor_brand")
    score: int = Field(..., ge=1, le=10, description="Relevance score from 1-10")
    reasoning: str = Field(..., description="Brief explanation for the classification and score")


class AnalysisSummary(BaseModel):
    """Summary statistics for the analysis"""
    total_keywords: int
    analyzed: int
    failed: int
    by_type: Dict[str, int] = Field(default_factory=dict)
    average_score: Optional[float] = None
    processing_time: Optional[float] = None


class KeywordAnalysisResponse(BaseModel):
    """Complete response model"""
    input_type: str = Field(..., description="Either 'asin' or 'description'")
    product_info: ProductDetails
    analysis_results: List[KeywordResult]
    summary: AnalysisSummary
    errors: Optional[List[str]] = None