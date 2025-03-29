# ---- File: schemas/market_research.py ----

from pydantic import BaseModel, Field
from typing import List, Optional

# --- Pydantic Models for Market Research Agent ---

class CompetitorInfo(BaseModel):
    name: str = Field(..., description="Name of the competitor")
    strengths: List[str] = Field(..., description="Key strengths of the competitor")
    weaknesses: List[str] = Field(..., description="Key weaknesses of the competitor")
    market_share: Optional[str] = Field(None, description="Estimated market share if known")
    key_features: List[str] = Field(..., description="Notable features or capabilities")
    pricing: Optional[str] = Field(None, description="Pricing information if available")

class MarketTrend(BaseModel):
    trend: str = Field(..., description="Description of the market trend")
    impact: str = Field(..., description="Potential impact on the product")
    opportunity: Optional[str] = Field(None, description="Potential opportunity this presents")
    threat: Optional[str] = Field(None, description="Potential threat this presents")

class CompetitiveAnalysis(BaseModel):
    """Structured analysis of competitors and market trends for a product."""
    competitors: List[CompetitorInfo] = Field(..., description="List of key competitors and their analysis")
    market_trends: List[MarketTrend] = Field(..., description="Key market trends relevant to the product")
    recommendations: List[str] = Field(..., description="Strategic recommendations based on the analysis")
    summary: str = Field(..., description="Executive summary of the competitive landscape")

    # Keep the example config here as it's tied to this specific schema structure
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "competitors": [{"name": "ExampleCorp","strengths": ["Large user base"],"weaknesses": ["Slow innovation"],"market_share": "Approx. 30%","key_features": ["Core Platform"],"pricing": "$100/user/month"}],
                    "market_trends": [{"trend": "AI Integration","impact": "Increased demand","opportunity": "Develop AI features.","threat": "Competitors move faster."}],
                    "recommendations": ["Invest R&D in AI.","Simplify pricing."],
                    "summary": "Market shifting towards AI."
                }
            ]
        }
    }