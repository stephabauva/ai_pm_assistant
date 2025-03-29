# ---- File: analysis.py ----

from fasthtml.common import *
from starlette.requests import Request
from fastapi import Depends, Form
import json
import logging

from agents.market_research_agent import analyze_competition as analyze_market_competition
from utils import get_user

logger = logging.getLogger(__name__)

# --- Routes ---

def add_analysis_routes(rt, get_user):
    @rt('/analyze', methods=['POST'])
    async def analyze(r: Request, q: str = Form(), model: str = Form(default="ollama"), email: str = Depends(get_user)):
        # ... (analyze route remains the same) ...
        r.session['selected_llm'] = model
        logger.info(f"Analyze POST request received: model={model}, query='{q[:50]}...' by user {email}")
        valid_models = ["gemini", "ollama", "lmstudio"]
        if model not in valid_models:
             logger.warning(f"Invalid model '{model}' selected in form.")
             # Let the analyze_result endpoint handle displaying the error via agent call failure
             pass

        loading_html = Div(
            H3("Analysis in Progress...", cls="text-xl font-bold mb-3 text-blue-600"),
            Div(
                Div(cls="animate-pulse h-2 bg-blue-200 rounded w-full mb-4"),
                Div(
                    P(f"Contacting {model} model and processing your query...", cls="text-gray-700 font-medium mb-3"),
                    P("Please wait, this may take 10-60 seconds...", cls="text-sm text-gray-500 mt-4"),
                    cls="p-4 bg-white rounded-lg border border-blue-200"
                ),
                Script(f"""
                console.log("Triggering result fetch for model={model} q={q.replace('"', '"')}...");
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

        # Default display_content to an error state in case agent call fails unexpectedly
        display_content: Html = Div(
                 H3("Application Error", cls="text-xl font-bold mb-3 text-red-600"),
                 P("An unexpected error occurred before processing the response."),
                 id="resp",
                 cls="p-4 bg-white rounded-lg shadow-md text-red-800"
             )
        result_data = None # Initialize result_data

        # --- Call the specific agent ---
        if q.lower().startswith("test:"):
            logger.info("Test query detected in analyze_result, returning static response")
            result_data = {
                 "structured": {"summary": "Static test response.", "competitors": [], "market_trends": [], "recommendations": ["Use real queries."]},
                 "raw": "Test Query Processed"
            }
        else:
            try:
                result_data = await analyze_market_competition(query=q, model=model)
                logger.info(f"Agent result processing complete for model {model}. Keys: {result_data.keys()}")
            except Exception as e:
                 logger.exception(f"Unexpected error calling agent for model {model}: {e}")
                 # Use the error result structure the rest of the code expects
                 result_data = {"error": f"An unexpected error occurred calling the agent: {str(e)}"}

        # --- Format response based on agent result ---
        if result_data and "error" in result_data:
            error_message = f"Error processing request: {result_data['error']}\n"
            if "details" in result_data and result_data["details"]:
                 error_message += f"\nDetails: {json.dumps(result_data['details'], indent=2)}"
            elif "raw" in result_data and result_data["raw"]:
                 error_message += f"\nRaw response snippet:\n{result_data['raw'][:500]}..."
            if "validation_errors" in result_data:
                 error_message += f"\nValidation Details: {json.dumps(result_data['validation_errors'], indent=2)}"

            logger.warning(f"Displaying error to user: {error_message[:150]}...")
            display_content = Div(
                H3("Analysis Error", cls="text-xl font-bold mb-3 text-red-600"),
                Pre(error_message, cls="whitespace-pre-wrap bg-red-50 p-4 rounded-lg border border-red-200 text-sm text-red-800"),
                id="resp",
                cls="p-4 bg-white rounded-lg shadow-md"
            )
        elif result_data and "structured" in result_data:
            # ... (formatting logic remains the same) ...
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
"""
            display_content = Div(
                H3("Analysis Results", cls="text-xl font-bold mb-3"),
                Pre(formatted_response, cls="whitespace-pre-wrap bg-gray-50 p-4 rounded-lg border border-gray-200 text-sm"),
                id="resp",
                cls="p-4 bg-white rounded-lg shadow-md"
            )
        # else case is covered by the initial assignment to display_content


        # --- Return the results content and OOB updates for radio buttons ---
        return Group(
            display_content,
            render_model_selection_oob(model)
        )


# Helper function remains the same
def render_model_selection_oob(selected_model: str):
     # ... (render_model_selection_oob remains the same) ...
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