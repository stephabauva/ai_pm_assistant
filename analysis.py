# ---- File: analysis.py ----

from fasthtml.common import *
from starlette.requests import Request
from fastapi import Depends, Form
import json
import logging

# Import the specific agent function
from agents.market_research_agent import analyze_competition as analyze_market_competition # Alias for clarity

# Import utilities if needed (e.g., get_user)
from utils import get_user

logger = logging.getLogger(__name__)

# Removed the old llm function and AIClient instantiation here


# --- Routes ---

def add_analysis_routes(rt, get_user):
    @rt('/analyze', methods=['POST'])
    async def analyze(r: Request, q: str = Form(), model: str = Form(default="ollama"), email: str = Depends(get_user)):
        # Save selected model for next page load
        r.session['selected_llm'] = model
        logger.info(f"Analyze POST request received: model={model}, query='{q[:50]}...' by user {email}")

        # Validate model choice before proceeding (optional but good practice)
        valid_models = ["gemini", "ollama", "lmstudio"]
        if model not in valid_models:
             # Handle invalid model selection gracefully - maybe return an error directly
             logger.warning(f"Invalid model '{model}' selected in form.")
             # This part needs careful handling with HTMX response structure
             # For now, we let the agent handle it, but could return an error UI here.
             pass # Allow agent to handle for now


        # Return the loading state immediately via HTMX
        loading_html = Div(
            H3("Analysis in Progress...", cls="text-xl font-bold mb-3 text-blue-600"),
            Div(
                Div(cls="animate-pulse h-2 bg-blue-200 rounded w-full mb-4"),
                Div(
                    P(f"Contacting {model} model and processing your query...", cls="text-gray-700 font-medium mb-3"),
                    P("Please wait, this may take 10-60 seconds...", cls="text-sm text-gray-500 mt-4"),
                    cls="p-4 bg-white rounded-lg border border-blue-200"
                ),
                # Script to trigger the actual analysis result fetch via POST
                Script(f"""
                console.log("Triggering result fetch for model={model} q={q.replace('"', '"')}..."); // Use " for HTML attribute
                setTimeout(function() {{
                    htmx.ajax('POST', '/analyze-result', {{
                        target:'#resp',
                        values: {{ q: '{q.replace("'", "\\'")}', model: '{model}' }}
                    }});
                }}, 500);
                """),
                id="resp",
                cls="p-4 bg-white rounded-lg shadow-md"
            )
        )
        return loading_html

    @rt('/analyze-result', methods=['POST'])
    async def analyze_result(r: Request, q: str = Form(), model: str = Form(), email: str = Depends(get_user)):
        logger.info(f"Analyze-Result POST received: model={model}, query='{q[:50]}...' by user {email}")

        # --- Call the specific agent ---
        # Handle "test:" prefix here before calling the agent
        if q.lower().startswith("test:"):
            logger.info("Test query detected in analyze_result, returning static response")
            result_data = {
                 "structured": {"summary": "Static test response.", "competitors": [], "market_trends": [], "recommendations": ["Use real queries."]},
                 "raw": "Test Query Processed"
            }
        else:
            try:
                # Call the market research agent function directly
                result_data = await analyze_market_competition(query=q, model=model)
                logger.info(f"Agent result processing complete for model {model}. Keys: {result_data.keys()}")
            except Exception as e:
                 # Catch unexpected errors during agent execution
                 logger.exception(f"Unexpected error calling agent for model {model}: {e}")
                 result_data = {"error": f"An unexpected error occurred in the application: {str(e)}"}

        # --- Format response based on agent result ---
        display_content: Html = None
        if "error" in result_data:
            error_message = f"Error processing request: {result_data['error']}\n"
            # Add details/raw snippet if available
            if "details" in result_data and result_data["details"]:
                 error_message += f"\nDetails: {json.dumps(result_data['details'], indent=2)}" # Assuming details are JSON serializable
            elif "raw" in result_data and result_data["raw"]:
                 error_message += f"\nRaw response snippet:\n{result_data['raw'][:500]}..."
            if "validation_errors" in result_data:
                 error_message += f"\nValidation Details: {json.dumps(result_data['validation_errors'], indent=2)}"

            logger.warning(f"Displaying error to user: {error_message[:150]}...")
            display_content = Div(
                H3("Analysis Error", cls="text-xl font-bold mb-3 text-red-600"),
                Pre(error_message, cls="whitespace-pre-wrap bg-red-50 p-4 rounded-lg border border-red-200 text-sm text-red-800"),
                id="resp", # Ensure the target div ID is included for replacement
                cls="p-4 bg-white rounded-lg shadow-md"
            )
        elif "structured" in result_data:
            analysis = result_data["structured"]
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
{"".join([f'- {r}' for r in analysis.get('recommendations', ['No specific recommendations provided'])])}
""" # Removed extra newline in recommendations join
            display_content = Div(
                H3("Analysis Results", cls="text-xl font-bold mb-3"),
                Pre(formatted_response, cls="whitespace-pre-wrap bg-gray-50 p-4 rounded-lg border border-gray-200 text-sm"),
                id="resp", # Target ID for replacement
                cls="p-4 bg-white rounded-lg shadow-md"
            )
        else:
             # Should not happen if agent returns correctly, but handle defensively
             logger.error("Agent returned unexpected data structure.")
             display_content = Div(
                 H3("Application Error", cls="text-xl font-bold mb-3 text-red-600"),
                 P("An unexpected error occurred processing the response."),
                 id="resp",
                 cls="p-4 bg-white rounded-lg shadow-md"
             )


        # --- Return the results content and OOB updates for radio buttons ---
        # Use Group to return multiple top-level elements for HTMX
        return Group(
            display_content, # The main content for #resp
            render_model_selection_oob(model) # OOB swap for radio buttons
        )


# Helper function remains the same
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
                     Span(label, cls="text-gray-700")
                 ),
                 id=f"model-radio-{value}",
                 hx_swap_oob="true",
                 cls="mb-2"
             )
         )
     return Group(*buttons)