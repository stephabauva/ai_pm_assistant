# ---- File: analysis.py ----

from fasthtml.common import *
from starlette.requests import Request
from fastapi import Depends, Form
import json
from ai_agent import AIClient # Assuming AIClient is importable
import logging # Add logging

logger = logging.getLogger(__name__)

# Removed module-level AI client instance

async def llm(q, model):
    """Process query using the selected model, expecting structured JSON."""
    logger.info(f"LLM function called with query: '{q[:50]}...' and model: {model}")
    # Special test query to bypass API calls for debugging
    if q.lower().startswith("test:"):
        logger.info("Test query detected, returning static test response")
        # Return a structure similar to what CompetitiveAnalysis.model_dump() would produce
        return {
            "structured": {
                "summary": "This is a test response to verify the UI rendering.",
                "competitors": [
                    {
                        "name": "Test Competitor",
                        "strengths": ["Fast response time", "No API call needed"],
                        "weaknesses": ["Not real data"],
                        "market_share": "N/A",
                        "key_features": ["Testing functionality"],
                        "pricing": "Free"
                    }
                ],
                "market_trends": [
                    {
                        "trend": "Test Trend",
                        "impact": "Helps debug the application",
                        "opportunity": "Faster debugging",
                        "threat": None
                    }
                ],
                "recommendations": ["Use real queries for actual analysis"]
            },
            "raw": "Static test response"
        }


    if model not in ["gemini", "ollama", "lmstudio"]:
        logger.warning(f"Invalid model selected: {model}")
        return {"error": "Invalid model selected"} # Return error structure

    # Instantiate AIClient inside the function
    ai_client = AIClient()

    try:
        # Use the AI client to get structured analysis (expects JSON)
        result = await ai_client.analyze_competition(q, model)
        logger.info(f"Result from ai_client.analyze_competition: keys={result.keys()}")

        # Check if the analysis itself returned an error
        if "error" in result:
            logger.error(f"Error received from analyze_competition: {result['error']}")
            # Format the error nicely for the frontend
            error_message = f"Error processing request: {result['error']}\n"
            if "raw" in result and result["raw"]:
                 error_message += f"\nRaw response from {model} (if available):\n{result['raw'][:500]}..." # Show snippet of raw response
            if "validation_errors" in result:
                 error_message += f"\nValidation Details: {json.dumps(result['validation_errors'], indent=2)}"

            # Return the error in a way the frontend can display
            # We'll wrap it slightly differently so the calling route knows it's an error display request
            return {"display_error": error_message}

        # If successful, return the structured data and raw response
        return result # Contains {"structured": {...}, "raw": "..."}

    except Exception as e:
        logger.exception(f"Unexpected error in llm function for model {model}: {e}")
        # Return error structure
        return {"display_error": f"An unexpected error occurred in the application: {str(e)}"}

# --- Routes ---

def add_analysis_routes(rt, get_user):
    @rt('/analyze', methods=['POST'])
    async def analyze(r: Request, q: str = Form(), model: str = Form(default="ollama"), email: str = Depends(get_user)):
        # Save selected model for next page load
        r.session['selected_llm'] = model
        logger.info(f"Analyze POST request received: model={model}, query='{q[:50]}...' by user {email}")

        # Always return the loading state immediately via HTMX
        # The actual result will be fetched by '/analyze-result' triggered by the script
        loading_html = Div(
            H3("Analysis in Progress...", cls="text-xl font-bold mb-3 text-blue-600"), # Changed color
            Div(
                Div(cls="animate-pulse h-2 bg-blue-200 rounded w-full mb-4"), # Changed color
                Div(
                    # Removed detailed steps for simplicity, just show pulsing bar and message
                    P(f"Contacting {model} model and processing your query...", cls="text-gray-700 font-medium mb-3"),
                    P("Please wait, this may take 10-60 seconds depending on the model and query complexity.",
                      cls="text-sm text-gray-500 mt-4"),
                    cls="p-4 bg-white rounded-lg border border-blue-200" # Changed color
                ),
                # Script to trigger the actual analysis result fetch
                Script(f"""
                console.log("Triggering result fetch for model={model} q={q.replace('"', '"')}");
                setTimeout(function() {{
                    htmx.ajax('POST', '/analyze-result', {{
                        target:'#resp',
                        values: {{ q: '{q.replace("'", "\\'")}', model: '{model}' }} // Pass data as values
                    }});
                }}, 500); // Small delay before fetching results
                """),
                id="resp", # Target for HTMX result swap
                cls="p-4 bg-white rounded-lg shadow-md"
            )
        )
        return loading_html

    @rt('/analyze-result', methods=['POST']) # Changed to POST to easily send query/model
    async def analyze_result(r: Request, q: str = Form(), model: str = Form(), email: str = Depends(get_user)):
        logger.info(f"Analyze-Result POST request received: model={model}, query='{q[:50]}...' by user {email}")

        # Process the actual query using the refactored llm function
        result_data = await llm(q, model)
        logger.info(f"LLM result processing complete for model {model}")

        # Check if the llm function returned an error to display
        if "display_error" in result_data:
            logger.warning(f"Displaying error to user: {result_data['display_error'][:100]}...")
            return Div(
                H3("Analysis Error", cls="text-xl font-bold mb-3 text-red-600"),
                Pre(result_data["display_error"], cls="whitespace-pre-wrap bg-red-50 p-4 rounded-lg border border-red-200 text-sm text-red-800"),
                # Include OOB swap for radio buttons even on error, so selection persists
                render_model_selection_oob(model),
                 id="resp", # Ensure the target div ID is included
                cls="p-4 bg-white rounded-lg shadow-md"
            )

        # --- Format successful structured response ---
        analysis = result_data.get("structured", {}) # Default to empty dict if missing
        formatted_response = f"""SUMMARY:
{analysis.get('summary', 'Summary not available')}

COMPETITORS:
{"".join([f'''
{comp.get('name', 'Unknown Competitor')}
- Market Share: {comp.get('market_share') or 'Not provided'}
- Pricing: {comp.get('pricing') or 'Not provided'}
- Strengths: {', '.join(comp.get('strengths', ['Not provided']))}
- Weaknesses: {', '.join(comp.get('weaknesses', ['Not provided']))}
- Key Features: {', '.join(comp.get('key_features', ['Not provided']))}
''' for comp in analysis.get('competitors', [])])}

MARKET TRENDS:
{"".join([f'''
{trend.get('trend', 'Market Trend')}
- Impact: {trend.get('impact', 'Not provided')}
{f'- Opportunity: {trend.get("opportunity")}' if trend.get('opportunity') else ''}
{f'- Threat: {trend.get("threat")}' if trend.get('threat') else ''}
''' for trend in analysis.get('market_trends', [])])}

RECOMMENDATIONS:
{"".join([f'- {r}\n' for r in analysis.get('recommendations', ['No specific recommendations provided'])])}
"""
        # --- Return the results content and OOB updates for radio buttons ---
        return Group( # Use Group to return multiple top-level elements for HTMX
            # 1. Main results content for the #resp div
            Div(
                H3("Analysis Results", cls="text-xl font-bold mb-3"),
                Pre(formatted_response, cls="whitespace-pre-wrap bg-gray-50 p-4 rounded-lg border border-gray-200 text-sm"),
                 id="resp", # Target ID
                cls="p-4 bg-white rounded-lg shadow-md"
            ),
            # 2. OOB swap to update the radio buttons state
            render_model_selection_oob(model)
        )

def render_model_selection_oob(selected_model: str):
     """Helper function to render model selection radio buttons with OOB swap attributes."""
     models = [("ollama", "Ollama (Local)"), ("lmstudio", "LMStudio (Local)"), ("gemini", "Gemini (Cloud)")]
     buttons = []
     for value, label in models:
         is_checked = selected_model == value
         buttons.append(
             Div(
                 Label(
                     Input(type="radio", name="model", value=value, checked=is_checked, cls="mr-2"),
                     Span(label, cls="text-gray-700") # Wrap label text in Span
                 ),
                 # Critical: Add hx_swap_oob="true" and unique ID for each radio button group
                 id=f"model-radio-{value}",
                 hx_swap_oob="true",
                 cls="mb-2" # Keep existing class if needed
             )
         )
     # Return a Group of Divs
     return Group(*buttons)