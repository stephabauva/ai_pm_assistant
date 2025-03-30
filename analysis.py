# ---- File: analysis.py ----

from fasthtml.common import *
# Import specific components from fasthtml.components
from fasthtml.components import Script, Group, Pre

from starlette.requests import Request
from starlette.responses import HTMLResponse # Import directly if needed, though Group handles it
from fastapi import Depends
import json
import logging
import asyncio
from typing import Any, Dict, List, Optional # Import needed types

from agents.market_research_agent import analyze_competition as analyze_market_competition
from utils import get_user

logger = logging.getLogger(__name__)

# --- Routes ---

# Type hint: Route functions in FastAPI/Starlette often return Response types
# FastHTML components render to Response implicitly, so 'Any' or 'HTMLResponse' could work.
# Using 'Any' for flexibility with FastHTML components.
def add_analysis_routes(rt, get_user):
    @rt('/analyze', methods=['POST'])
    async def analyze(r: Request, email: str = Depends(get_user)) -> Any:
        # Get form data manually
        form_data = await r.form()
        q = form_data.get("q", "")
        model = form_data.get("model", "ollama")
        
        r.session['selected_llm'] = model
        logger.info(f"Analyze POST request received: model={model}, query='{q[:50]}...' by user {email}")
        valid_models = ["gemini", "ollama", "lmstudio"]
        if model not in valid_models:
             logger.warning(f"Invalid model '{model}' selected in form.")
             pass # Allow agent to handle for now

        loading_html = Div(
            H3("Analysis in Progress...", cls="text-xl font-bold mb-3 text-blue-600"),
            Div(
                Div(cls="animate-pulse h-2 bg-blue-200 rounded w-full mb-4"),
                P(f"Contacting {model} model and processing query. Please wait...", cls="text-gray-700 font-medium mb-3"),
                P("Results will appear below automatically.", cls="text-sm text-gray-500 mt-4"),
                Div(
                    hx_post="/analyze-result",
                    hx_trigger="load delay:200ms, every 2s",
                    hx_target="#resp",
                    hx_swap="outerHTML",
                    hx_vals=json.dumps({"q": q, "model": model}),
                ),
                cls="p-4 bg-white rounded-lg border border-blue-200"
            ),
            id="resp",
            cls="p-4 bg-white rounded-lg shadow-md"
        )
        # Return both the loading HTML and the model selection radio buttons
        return Group(
            loading_html,
            render_model_selection_oob(model)
        )

    @rt('/analyze-result', methods=['POST'])
    async def analyze_result(r: Request, email: str = Depends(get_user)) -> Any:
        # Get form data manually
        form_data = await r.form()
        q = form_data.get("q", "")
        model = form_data.get("model", "ollama")
        display_content = Div(
                 H3("Application Error", cls="text-xl font-bold mb-3 text-red-600"),
                 P("An unexpected error occurred before processing the response."),
                 id="resp",
                 cls="p-4 bg-white rounded-lg shadow-md text-red-800"
             )
        result_data: Optional[Dict[str, Any]] = None # Add type hint

        if q.lower().startswith("test:"):
            logger.info("Test query detected in analyze_result, returning static response")
            await asyncio.sleep(1)
            result_data = {
                 "structured": {"summary": "Static test response.", "competitors": [], "market_trends": [], "recommendations": ["Use real queries."]},
                 "raw": "Test Query Processed"
            }
        else:
            try:
                logger.info(f"Analyze-Result POST executing analysis: model={model}, query='{q[:50]}...'")
                result_data = await analyze_market_competition(query=q, model=model)
                logger.info(f"Agent result processing complete for model {model}. Keys: {result_data.keys()}")
            except Exception as e:
                 logger.exception(f"Unexpected error calling agent for model {model}: {e}")
                 result_data = {"error": f"An unexpected error occurred calling the agent: {str(e)}"}

        # Add type hint for analysis dictionary
        analysis: Optional[Dict[str, Any]] = None
        if result_data and "structured" in result_data:
            analysis = result_data["structured"]

        if result_data and "error" in result_data:
            error_message = f"Error processing request: {result_data['error']}\n"
            if "details" in result_data and result_data["details"]: error_message += f"\nDetails: {json.dumps(result_data['details'], indent=2)}"
            elif "raw" in result_data and result_data["raw"]: error_message += f"\nRaw response snippet:\n{result_data['raw'][:500]}..."
            if "validation_errors" in result_data: error_message += f"\nValidation Details: {json.dumps(result_data['validation_errors'], indent=2)}"

            logger.warning(f"Displaying error to user: {error_message[:150]}...")
            display_content = Div(
                H3("Analysis Error", cls="text-xl font-bold mb-3 text-red-600"),
                Pre(error_message, cls="whitespace-pre-wrap bg-red-50 p-4 rounded-lg border border-red-200 text-sm text-red-800"),
                id="resp",
                cls="p-4 bg-white rounded-lg shadow-md"
            )
        elif analysis is not None: # Check if analysis dict exists
            # --- Formatting Logic ---
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
"""
            display_content = Div(
                H3("Analysis Results", cls="text-xl font-bold mb-3"),
                Pre(formatted_response, cls="whitespace-pre-wrap bg-gray-50 p-4 rounded-lg border border-gray-200 text-sm"),
                id="resp",
                cls="p-4 bg-white rounded-lg shadow-md"
            )
        # else case (result_data exists but no 'error' or 'structured') covered by initial assignment

        return Group(
            display_content,
            render_model_selection_oob(model)
        )


# Type hint: This helper returns a FastHTML Group component
def render_model_selection_oob(selected_model: str) -> Group:
     """Helper function to render model selection radio buttons with OOB swap attributes."""
     models = [("ollama", "Ollama (Local)"), ("lmstudio", "LMStudio (Local)"), ("gemini", "Gemini (Cloud)")]
     buttons: List[Any] = [] # List to hold Div components
     for value, label in models:
         is_checked = (selected_model == value)
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
     # Use tuple unpacking for Group arguments
     return Group(*buttons)