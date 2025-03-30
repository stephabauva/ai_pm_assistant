from fasthtml.common import *
from fastapi import Depends
from starlette.requests import Request
from typing import Any

# Removed Tailwind CSS CDN link

# Define the path to the local CSS file
local_css = Link(rel="stylesheet", href="/static/styles.css")

def add_dashboard_routes(rt, get_user):
    @rt('/')
    async def dash(r: Request, email: str = Depends(get_user)) -> Any:
        selected_model = r.session.get('selected_llm', 'ollama')
        # Basic structure using FastHTML components and Tailwind classes
        # Assumes styles.css contains necessary Tailwind classes or custom styles
        return (
            Title("AI-PM Dashboard"),
            local_css,  # Include local CSS file link in the head
            # Optional: Add JS if needed later
            # Script(src="/static/app.js"),
            Main(
                Div( # Outer container for centering and padding
                    H3("🔍 Competitive Analysis Agent", cls="text-2xl font-bold mb-4 text-gray-800"),
                    P("Enter a query to analyze competitors and market trends.", cls="text-sm text-gray-600 mb-4"),
                    Form(
                        # Model selection
                        Div(
                            H4("Select Model", cls="text-lg font-semibold text-gray-700 mb-2"),
                            Div(
                                Div(
                                    Label(Input(type="radio", name="model", value="ollama", checked=selected_model == "ollama", cls="mr-2"), Span("Ollama (Local)", cls="text-gray-700")),
                                    id="model-radio-ollama", # Ensure IDs match for OOB swap
                                    cls="mb-2"
                                ),
                                Div(
                                    Label(Input(type="radio", name="model", value="lmstudio", checked=selected_model == "lmstudio", cls="mr-2"), Span("LMStudio (Local)", cls="text-gray-700")),
                                    id="model-radio-lmstudio",
                                    cls="mb-2"
                                ),
                                Div(
                                    Label(Input(type="radio", name="model", value="gemini", checked=selected_model == "gemini", cls="mr-2"), Span("Gemini (Cloud)", cls="text-gray-700")),
                                    id="model-radio-gemini",
                                    cls="mb-2"
                                ),
                                cls="space-y-2 bg-gray-50 p-4 rounded-lg shadow-sm border border-gray-200" # Added border
                            ),
                            cls="mb-6"
                        ),
                        # Query input
                        Div(
                            Div(
                                Label("Enter your query:", for_="q", cls="block text-sm font-medium text-gray-700 mb-1"),
                                Span(
                                    "Use sample",
                                    cls="ml-1 text-[8px] bg-gray-100 text-gray-500 py-0 px-0.5 rounded-sm border border-gray-200 hover:bg-gray-200 transition duration-200 leading-tight cursor-pointer",
                                    onclick="document.getElementById('q').value='Analyse crm market competitors'; return false;"
                                ),
                                cls="flex items-center"
                            ),
                            Textarea( # Changed to Textarea for potentially longer queries
                                id="q", name="q", placeholder="e.g., Analyze CRM market competitors focusing on AI features and pricing models...",
                                cls="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 mb-2", # Added mb-2
                                rows="3" # Set initial rows for textarea
                            ),
                            cls="mb-4"
                        ),
                        # Submit button
                        Button(
                            "Analyze", type="submit",
                            cls="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition duration-200",
                            # Use standard htmx indicator approach if preferred over button text change
                            # hx_indicator="#analyze-indicator"
                             _="on click set my innerHTML to 'Analyzing...' then add @disabled until htmx:afterRequest" # Keep simple button state change
                        ),
                        # Span(id="analyze-indicator", cls="htmx-indicator ml-2", content="⏳"), # Standard indicator
                        # --- HTMX Attributes ---
                        hx_post="/analyze",      # Endpoint to submit the form
                        hx_target="#resp",       # Target div to update with loading state/results
                        hx_swap="innerHTML",     # Replace content of the target
                        hx_include="[name='model'], [name='q']" # Include model and query
                    ),
                    # Response area
                    Div(id="resp", cls="mt-6"), # Area where loading state and results appear
                    cls="max-w-lg mx-auto p-6 bg-white rounded-xl shadow-lg border border-gray-200" # Use bg-white for card
                ),
                cls="container mx-auto mt-8" # Apply container class to Main or a wrapper Div
            )
        )