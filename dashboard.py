from fasthtml.common import *
from fastapi import Depends
from starlette.requests import Request

# Tailwind CSS CDN (for development; consider a local build for production)
tailwind_cdn = Link(rel="stylesheet", href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css")

def add_dashboard_routes(rt, get_user):
    @rt('/')
    async def dash(r: Request, email: str = Depends(get_user)):
        selected_model = r.session.get('selected_llm', 'ollama')
        return (
            Title("AI-PM Dashboard"),
            tailwind_cdn,  # Include Tailwind CSS
            Main(
                Div(
                    H3("🔍 Competitive Analysis Agent", cls="text-2xl font-bold mb-4 text-gray-800"),
                    P("Powered by Pydantic AI for structured insights", cls="text-sm text-gray-600 mb-4"),
                    Form(
                        # Model selection with radio buttons
                        Div(
                            H4("Select Model", cls="text-lg font-semibold text-gray-700 mb-2"),
                            Div(
                                # Local Models
                                Div(
                                    Label(
                                        Input(type="radio", name="model", value="ollama", checked=selected_model == "ollama", cls="mr-2"),
                                        "Ollama (Local)", cls="text-gray-700"
                                    ),
                                    cls="mb-2"
                                ),
                                Div(
                                    Label(
                                        Input(type="radio", name="model", value="lmstudio", checked=selected_model == "lmstudio", cls="mr-2"),
                                        "LMStudio (Local)", cls="text-gray-700"
                                    ),
                                    cls="mb-2"
                                ),
                                # Cloud Models
                                Div(
                                    Label(
                                        Input(type="radio", name="model", value="gemini", checked=selected_model == "gemini", cls="mr-2"),
                                        "Gemini (Cloud)", cls="text-gray-700"
                                    ),
                                    cls="mb-2"
                                ),
                                cls="space-y-2 bg-gray-50 p-4 rounded-lg shadow-sm"
                            ),
                            cls="mb-6"
                        ),
                        # Query input and submit button
                        Div(
                            Div(
                                Label("Enter your competitive analysis query:", for_="q", cls="block text-sm font-medium text-gray-700 mb-1"),
                                Span(
                                    "Use sample",
                                    cls="ml-1 text-[8px] bg-gray-100 text-gray-500 py-0 px-0.5 rounded-sm border border-gray-200 hover:bg-gray-200 transition duration-200 leading-tight cursor-pointer",
                                    onclick="document.getElementById('q').value='Analyse crm market competitors'; return false;"
                                ),
                                cls="flex items-center"
                            ),
                            Input(
                                id="q", name="q", placeholder="e.g., Analyze CRM market competitors",
                                cls="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 mb-4"
                            ),
                            cls="mb-4"
                        ),
                        P("The response will be structured using Pydantic AI models for better organization", cls="text-xs text-gray-500 mb-4"),
                        Button(
                            "Analyze", type="submit",
                            cls="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition duration-200",
                            hx_indicator=".htmx-indicator",
                            _="on click set my innerHTML to 'Analyzing...'"
                        ),
                        Span("⏳", cls="htmx-indicator text-gray-500 ml-2", style="display:none;"),
                        hx_post="/analyze", hx_target="#resp", hx_swap="innerHTML", hx_include="[name='model']"
                    ),
                    Div(id="resp", cls="mt-6 p-4 bg-white rounded-lg shadow-md"),
                    cls="max-w-lg mx-auto p-6 bg-gray-100 rounded-xl shadow-lg"
                ),
                cls="container mx-auto mt-8"
            )
        )