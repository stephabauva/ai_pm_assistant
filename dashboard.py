from fasthtml.common import *
from starlette.requests import Request
from fastapi import Depends

def add_dashboard_routes(rt, get_user):
    @rt('/')
    async def dash(r: Request, email: str = Depends(get_user)):
        selected_model = r.session.get('selected_llm', 'ollama')
        return Title("AI-PM Dashboard"), Main(Div(
            H3("🔍 Competitive Analysis Agent", style="margin: 0"),
            Form(
                Div(
                    Label("Local Models:", for_="local_llm"),
                    Select(
                        Option("Ollama", value="ollama", selected=selected_model == "ollama"),
                        Option("LMStudio", value="lmstudio", selected=selected_model == "lmstudio"),
                        name="local_llm", id="local_llm",
                        cls="selected" if selected_model in ["ollama", "lmstudio"] else "",
                        onchange="document.getElementById('cloud_llm').selectedIndex = 0; document.getElementById('cloud_llm').classList.remove('selected'); this.classList.add('selected'); this.form.requestSubmit()",
                        value="" if selected_model == "gemini" else selected_model
                    ),
                    cls="model-group"
                ),
                Div(
                    Label("Cloud Models:", for_="cloud_llm"),
                    Select(
                        Option("Select cloud model", value="", disabled=True, hidden=True),
                        Option("Gemini", value="gemini", selected=selected_model == "gemini"),
                        name="cloud_llm", id="cloud_llm",
                        cls="selected" if selected_model == "gemini" else "",
                        onchange="document.getElementById('local_llm').selectedIndex = 0; document.getElementById('local_llm').classList.remove('selected'); this.classList.add('selected'); this.form.requestSubmit()",
                        value="gemini" if selected_model == "gemini" else ""
                    ),
                    cls="model-group"
                ),
                Input(id="q", name="q", placeholder="e.g., Analyze CRM market competitors"),
                Button("Analyze", type="submit", hx_indicator=".htmx-indicator", _="on click set my innerHTML to 'Analyzing...'"),
                Span("⏳", cls="htmx-indicator", style="display:none; margin-left: 8px;"),
                hx_post="/analyze", hx_target="#resp", hx_swap="innerHTML", hx_include="#local_llm, #cloud_llm"
            ),
            Div(id="resp"),
            cls="card"
        ), cls="container")