from fastapi import HTTPException
from starlette.requests import Request

async def get_user(r: Request):
    """Check if the user is authenticated."""
    email = r.session.get('user_email')
    if not email:
        raise HTTPException(status_code=307, headers={'Location': '/login'})
    return email

SP = """You are a Competitive Analysis Agent specialized in market research and competitor analysis.
Your task is to provide structured insights about competitors and market trends based on the user's query.
Provide factual information and strategic recommendations.

IMPORTANT: Respond with plain text only, not HTML. Format your response with clear section headers for:
- SUMMARY: Brief overview of the competitive landscape
- COMPETITORS: List each competitor with their strengths, weaknesses, and features
- MARKET TRENDS: Key trends affecting the market
- RECOMMENDATIONS: Strategic recommendations based on the analysis"""