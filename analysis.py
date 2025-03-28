from fasthtml.common import *
from starlette.requests import Request
from fastapi import Depends, Form
import json
from ai_agent import AIClient

# Create AI client instance
ai_client = AIClient()

async def llm(q, model):
    """Process query using the selected model with Pydantic models."""
    # Special test query to bypass API calls for debugging
    if q.lower().startswith("test:"):
        print("[DEBUG] Test query detected, returning test response")
        return """
SUMMARY:
This is a test response to verify the UI rendering.

COMPETITORS:
Test Competitor:
- Strengths: Fast response time, No API call needed
- Weaknesses: Not real data
- Key Features: Testing functionality

MARKET TRENDS:
Test Trend:
- Impact: Helps debug the application

RECOMMENDATIONS:
- Use real queries for actual analysis
"""
    
    if model not in ["gemini", "ollama", "lmstudio"]:
        return "Error: No valid model selected"
    
    try:
        # Use the AI client to get structured analysis
        result = await ai_client.analyze_competition(q, model)
        
        if "error" in result:
            # Return the raw response for debugging
            return f"Error processing request: {result['error']}\n\nRaw response from {model}:\n\n{result['raw']}"
        
        # Check if we have a structured response
        if "structured" not in result or not result["structured"]:
            # Return the raw response if structured parsing failed
            return f"Raw response from {model}:\n\n{result['raw']}"
            
        # Format the structured response
        analysis = result["structured"]
        
        # Create a formatted plain text response
        formatted_response = f"""SUMMARY:
{analysis.get('summary', 'Competitive analysis summary not available')}

COMPETITORS:
{"".join([f'''
{comp.get('name', 'Unknown Competitor')}
- Market Share: {comp.get('market_share') or 'Unknown'}
- Pricing: {comp.get('pricing') or 'Unknown'}
- Strengths: {', '.join(comp.get('strengths', ['Information not available']))}
- Weaknesses: {', '.join(comp.get('weaknesses', ['Information not available']))}
- Key Features: {', '.join(comp.get('key_features', ['Information not available']))}
''' for comp in analysis['competitors']])}

MARKET TRENDS:
{"".join([f'''
{trend.get('trend', 'Market Trend')}
- Impact: {trend.get('impact', 'Information not available')}
{f'- Opportunity: {trend.get("opportunity")}' if trend.get('opportunity') else ''}
{f'- Threat: {trend.get("threat")}' if trend.get('threat') else ''}
''' for trend in analysis['market_trends']])}

RECOMMENDATIONS:
{"".join([f'- {r}\n' for r in analysis.get('recommendations', ['No specific recommendations available'])])}
"""
        
        return formatted_response
    except Exception as e:
        return f"Error: {str(e)}"

def add_analysis_routes(rt, get_user):
    @rt('/analyze', methods=['POST'])
    async def analyze(r: Request, q: str = Form(), model: str = Form(default="ollama"), email: str = Depends(get_user)):
        r.session['selected_llm'] = model
        print(f"[DEBUG] Analyze request received: model={model}, query={q[:30]}...")
        response = await llm(q, model)
        print(f"[DEBUG] Response received, length: {len(response)}")
        # Add debug parameter to show raw response
        debug = r.query_params.get('debug', '').lower() in ('true', '1', 'yes')
        
        # Always display as pre-formatted text
        return (
                Div(
                    H3("Analysis Results", cls="text-xl font-bold mb-3"),
                    Pre(response, cls="whitespace-pre-wrap bg-gray-50 p-4 rounded-lg border border-gray-200 text-sm"),
                    id="resp", cls="p-4 bg-white rounded-lg shadow-md"
                ),
                # Update the radio buttons with the selected model
                Div(
                    Label(
                        Input(type="radio", name="model", value="ollama", checked=model == "ollama", cls="mr-2"),
                        "Ollama (Local)", cls="text-gray-700"
                    ),
                    cls="mb-2", hx_swap_oob="true"
                ),
                Div(
                    Label(
                        Input(type="radio", name="model", value="lmstudio", checked=model == "lmstudio", cls="mr-2"),
                        "LMStudio (Local)", cls="text-gray-700"
                    ),
                    cls="mb-2", hx_swap_oob="true"
                ),
                Div(
                    Label(
                        Input(type="radio", name="model", value="gemini", checked=model == "gemini", cls="mr-2"),
                        "Gemini (Cloud)", cls="text-gray-700"
                    ),
                    cls="mb-2", hx_swap_oob="true"
                )
            )