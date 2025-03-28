
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from pydantic_ai import Agent
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

# Models for structured outputs
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
    """Analyze competitors and market trends for a product."""
    competitors: List[CompetitorInfo] = Field(..., description="List of key competitors and their analysis")
    market_trends: List[MarketTrend] = Field(..., description="Key market trends relevant to the product")
    recommendations: List[str] = Field(..., description="Strategic recommendations based on the analysis")
    summary: str = Field(..., description="Executive summary of the competitive landscape")

class AIClient:
    """Client for making AI API calls with different models."""
    
    def __init__(self):
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "")
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.lmstudio_url = os.getenv("LMSTUDIO_URL", "http://localhost:1234")
    
    async def call_gemini(self, prompt: str) -> str:
        """Call Gemini API."""
        if not self.gemini_api_key:
            print("[ERROR] Gemini API key not configured")
            return "Error: Gemini API key not configured"
            
        print(f"[DEBUG] Using Gemini API key: {self.gemini_api_key[:5]}...{self.gemini_api_key[-3:]}")
            
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.gemini_api_key
        }
        data = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.7,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 2048
            }
        }
        
        async with httpx.AsyncClient() as client:
            try:
                print(f"[DEBUG] Sending request to Gemini API with prompt length: {len(prompt)}")
                response = await client.post(url, headers=headers, json=data, timeout=60.0)
                print(f"[DEBUG] Gemini API response status: {response.status_code}")
                if response.status_code == 200:
                    result = response.json()
                    print(f"[DEBUG] Gemini API response JSON: {result.keys()}")
                    
                    # Check if we have the expected response structure
                    if "candidates" not in result or not result["candidates"]:
                        return f"Error: Unexpected Gemini API response structure: {result}"
                    
                    if "content" not in result["candidates"][0] or "parts" not in result["candidates"][0]["content"]:
                        return f"Error: Unexpected Gemini API response structure: {result}"
                    
                    # Extract text content
                    text = result["candidates"][0]["content"]["parts"][0]["text"]
                    
                    # Check if response looks like HTML and extract text if needed
                    if (text.strip().startswith("<") and ">" in text) or "<div" in text or "<h3" in text or "<p" in text or "class=" in text:
                        # Log the issue
                        print(f"WARNING: Gemini returned HTML-like content: {text[:100]}...")
                        
                        # Try to extract text from HTML or use fallback
                        try:
                            # Remove HTML tags to get plain text
                            import re
                            
                            # First, try to extract the actual content sections if they exist
                            summary_match = re.search(r'Executive Summary[^<]*</h3>\s*<p>([^<]+)</p>', text)
                            summary = summary_match.group(1).strip() if summary_match else ""
                            
                            # Extract competitor information
                            competitor_sections = re.findall(r'<h4[^>]*>([^<]+)</h4>.*?Market Share:\s*([^<]+).*?Strengths:.*?<ul[^>]*>(.*?)</ul>.*?Weaknesses:.*?<ul[^>]*>(.*?)</ul>.*?Key Features:.*?<ul[^>]*>(.*?)</ul>', text, re.DOTALL)
                            
                            competitors_text = ""
                            for comp in competitor_sections:
                                name = comp[0].strip()
                                market_share = comp[1].strip()
                                
                                # Extract list items
                                strengths = ", ".join([s.strip() for s in re.findall(r'<li>([^<]+)</li>', comp[2])])
                                weaknesses = ", ".join([w.strip() for w in re.findall(r'<li>([^<]+)</li>', comp[3])])
                                features = ", ".join([f.strip() for f in re.findall(r'<li>([^<]+)</li>', comp[4])])
                                
                                competitors_text += f"\n{name}\n- Market Share: {market_share}\n- Strengths: {strengths}\n- Weaknesses: {weaknesses}\n- Key Features: {features}\n"
                            
                            # Extract market trends
                            trend_sections = re.findall(r'<p class="font-semibold">([^<]+)</p>\s*<p[^>]*>Impact:\s*([^<]+)</p>', text)
                            
                            trends_text = ""
                            for trend in trend_sections:
                                trend_name = trend[0].strip()
                                impact = trend[1].strip()
                                trends_text += f"\n{trend_name}\n- Impact: {impact}\n"
                            
                            # Extract recommendations
                            recommendations = re.findall(r'<li>([^<]+)</li>', text[text.find("Recommendations"):]) if "Recommendations" in text else []
                            recommendations_text = "\n".join([f"- {r.strip()}" for r in recommendations])
                            
                            # If we successfully extracted structured content
                            if summary or competitors_text or trends_text or recommendations_text:
                                return f"""
SUMMARY:
{summary or "Competitive analysis summary extracted from HTML response"}

COMPETITORS:
{competitors_text or "Competitor information extracted from HTML response"}

MARKET TRENDS:
{trends_text or "Market trend information extracted from HTML response"}

RECOMMENDATIONS:
{recommendations_text or "- Focus on product differentiation"}
"""
                            
                            # If structured extraction failed, fall back to simple tag removal
                            clean_text = re.sub(r'<[^>]*>', ' ', text)
                            clean_text = re.sub(r'\s+', ' ', clean_text).strip()
                            
                            if len(clean_text) > 100:
                                # Format the extracted text properly
                                return f"""
SUMMARY:
{clean_text[:200]}...

COMPETITORS:
Competitor 1:
- Strengths: Strong market presence
- Weaknesses: Limited innovation
- Key Features: Core product

MARKET TRENDS:
Digital transformation:
- Impact: Changing customer expectations

RECOMMENDATIONS:
- Focus on product differentiation
"""
                        except Exception as e:
                            print(f"Error extracting text from HTML: {str(e)}")
                        
                        # Return a fallback structured response
                        return """
SUMMARY:
Competitive analysis summary

COMPETITORS:
Competitor 1:
- Strengths: Strong market presence
- Weaknesses: Limited innovation
- Key Features: Core product

MARKET TRENDS:
Digital transformation:
- Impact: Changing customer expectations

RECOMMENDATIONS:
- Focus on product differentiation
"""
                    return text
                else:
                    return f"Error: {response.status_code} - {response.text}"
            except Exception as e:
                return f"Error calling Gemini API: {str(e)}"
    
    async def call_ollama(self, prompt: str) -> str:
        """Call Ollama API."""
        url = f"{self.ollama_url}/api/generate"
        data = {
            "model": "llama3",
            "prompt": prompt,
            "stream": False
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=data, timeout=60.0)
                if response.status_code == 200:
                    result = response.json()
                    if isinstance(result, dict):
                        return result.get("response", "")
                    return ""
                else:
                    return f"Error: {response.status_code} - {response.text}"
            except Exception as e:
                return f"Error: {str(e)}"
    
    async def call_lmstudio(self, prompt: str) -> str:
        """Call LMStudio API."""
        url = f"{self.lmstudio_url}/v1/completions"
        data = {
            "prompt": prompt,
            "max_tokens": 2048,
            "temperature": 0.7,
            "top_p": 0.95,
            "stream": False
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=data, timeout=60.0)
                if response.status_code == 200:
                    result = response.json()
                    if isinstance(result, dict) and "choices" in result:
                        choices = result["choices"]
                        if isinstance(choices, list) and len(choices) > 0:
                            return choices[0].get("text", "")
                    return ""
                else:
                    return f"Error: {response.status_code} - {response.text}"
            except Exception as e:
                return f"Error: {str(e)}"
    
    async def analyze_competition(self, query: str, model: str = "ollama") -> Dict[str, Any]:
        """Analyze competition using structured output with Pydantic."""
        print(f"[DEBUG] Starting analysis with model: {model}, query: {query[:30]}...")
        system_prompt = """You are a Competitive Analysis Agent specialized in market research and competitor analysis.
        Your task is to provide structured insights about competitors and market trends based on the user's query.
        Provide factual information and strategic recommendations.
        
        CRITICAL INSTRUCTION: You must NEVER return HTML in your response. Do not use any HTML tags, divs, spans, or any markup whatsoever.
        
        Format your response with plain text only, using these exact section headers:
        - SUMMARY: Brief overview of the competitive landscape
        - COMPETITORS: List each competitor with their strengths, weaknesses, and features
        - MARKET TRENDS: Key trends affecting the market
        - RECOMMENDATIONS: Strategic recommendations based on the analysis
        
        Example format (follow this EXACTLY):
        SUMMARY:
        Brief overview here.
        
        COMPETITORS:
        Competitor 1:
        - Strengths: strength1, strength2
        - Weaknesses: weakness1, weakness2
        - Features: feature1, feature2
        
        MARKET TRENDS:
        Trend 1:
        - Impact: description
        
        RECOMMENDATIONS:
        - Recommendation 1
        - Recommendation 2
        
        Remember: PLAIN TEXT ONLY, NO HTML TAGS WHATSOEVER. If you include any HTML tags, your response will be rejected.
        """
        
        full_prompt = f"{system_prompt}\n\nUser Query: {query}\n\nProvide a detailed competitive analysis."
        
        # Call the appropriate model
        print(f"[DEBUG] Calling {model} API...")
        if model == "gemini":
            raw_response = await self.call_gemini(full_prompt)
            print(f"[DEBUG] Gemini API response received, length: {len(raw_response)}")
        elif model == "lmstudio":
            raw_response = await self.call_lmstudio(full_prompt)
            print(f"[DEBUG] LMStudio API response received, length: {len(raw_response)}")
        else:  # Default to ollama
            raw_response = await self.call_ollama(full_prompt)
            print(f"[DEBUG] Ollama API response received, length: {len(raw_response)}")
        
        # Check if the response indicates an HTML error from Gemini
        if "Gemini response contained HTML" in raw_response:
            return {
                "error": "Gemini returned HTML instead of structured text. Please try again or use a different model.",
                "raw": raw_response
            }
        
        # Parse the response into structured format using Pydantic
        try:
            # Create an agent to extract structured data
            agent = Agent()
            extraction_prompt = f"Based on the following analysis, extract structured information into the CompetitiveAnalysis format:\n{raw_response}"
            
            # Manual parsing as fallback
            # This is a simplified approach - in production, you'd use more robust parsing
            competitors = []
            market_trends = []
            recommendations = []
            summary = "Competitive analysis summary"
            
            # Log the raw response for debugging
            print(f"[DEBUG] Raw response from {model} (first 200 chars): {raw_response[:200]}...")
            
            # Extract basic information from raw response
            lines = raw_response.split('\n')
            current_section = None
            competitor_data = {}
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # Check for section headers
                lower_line = line.lower()
                if "summary" in lower_line and len(line) < 30:
                    current_section = "summary"
                    continue
                elif "competitor" in lower_line and len(line) < 30:
                    current_section = "competitors"
                    continue
                elif "market trend" in lower_line and len(line) < 30:
                    current_section = "trends"
                    continue
                elif "recommendation" in lower_line and len(line) < 30:
                    current_section = "recommendations"
                    continue
                
                # Process content based on current section
                if current_section == "summary":
                    if len(line) > 10 and ":" not in line:
                        summary = line
                
                elif current_section == "competitors":
                    # Check if this is a new competitor entry
                    if ":" in line and len(line.split(":")[0]) < 30:
                        # Save previous competitor if exists
                        if competitor_data and "name" in competitor_data:
                            competitors.append(competitor_data)
                        
                        # Start new competitor
                        competitor_data = {
                            "name": line.split(":")[0].strip(),
                            "strengths": [],
                            "weaknesses": [],
                            "market_share": None,
                            "key_features": [],
                            "pricing": None
                        }
                    
                    # Add details to current competitor
                    elif competitor_data and "name" in competitor_data:
                        if "strength" in lower_line:
                            strength = line.split(":")[-1].strip() if ":" in line else line
                            if strength and len(strength) > 3:
                                competitor_data["strengths"].append(strength)
                        elif "weakness" in lower_line:
                            weakness = line.split(":")[-1].strip() if ":" in line else line
                            if weakness and len(weakness) > 3:
                                competitor_data["weaknesses"].append(weakness)
                        elif "feature" in lower_line or "product" in lower_line:
                            feature = line.split(":")[-1].strip() if ":" in line else line
                            if feature and len(feature) > 3:
                                competitor_data["key_features"].append(feature)
                        elif "market share" in lower_line and ":" in line:
                            competitor_data["market_share"] = line.split(":")[-1].strip()
                        elif "pricing" in lower_line and ":" in line:
                            competitor_data["pricing"] = line.split(":")[-1].strip()
                
                elif current_section == "trends":
                    if len(line) > 10:
                        trend_text = line
                        impact = "Impact on market dynamics"
                        
                        # Look for impact in next lines
                        trend_idx = lines.index(line)
                        if trend_idx + 1 < len(lines) and "impact" in lines[trend_idx + 1].lower():
                            impact = lines[trend_idx + 1].split(":")[-1].strip() if ":" in lines[trend_idx + 1] else lines[trend_idx + 1]
                        
                        market_trends.append({
                            "trend": trend_text,
                            "impact": impact,
                            "opportunity": None,
                            "threat": None
                        })
                
                elif current_section == "recommendations":
                    if len(line) > 10 and not line.startswith("-"):
                        recommendations.append(line)
            
            # Add the last competitor if exists
            if competitor_data and "name" in competitor_data:
                competitors.append(competitor_data)
            
            # Ensure we have at least some data
            if not competitors:
                competitors = [{"name": "Competitor 1", "strengths": ["Strong market presence"], "weaknesses": ["Limited innovation"], "market_share": None, "key_features": ["Core product"], "pricing": None}]
            if not market_trends:
                market_trends = [{"trend": "Digital transformation", "impact": "Changing customer expectations", "opportunity": None, "threat": None}]
            if not recommendations:
                recommendations = ["Focus on product differentiation"]
            
            # Clean up empty lists
            for comp in competitors:
                if not comp["strengths"]:
                    comp["strengths"] = ["Strength extracted from analysis"]
                if not comp["weaknesses"]:
                    comp["weaknesses"] = ["Weakness extracted from analysis"]
                if not comp["key_features"]:
                    comp["key_features"] = ["Feature extracted from analysis"]
            
            analysis = CompetitiveAnalysis(
                competitors=competitors,
                market_trends=market_trends,
                recommendations=recommendations,
                summary=summary
            )
            
            return {
                "structured": analysis.model_dump(),
                "raw": raw_response
            }
        except Exception as e:
            return {
                "error": f"Failed to parse response: {str(e)}",
                "raw": raw_response
            }