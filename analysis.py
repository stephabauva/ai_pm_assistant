from fasthtml.common import *  # For FastHTML components like Div
from starlette.requests import Request  # For Request type
from fastapi import Depends, Form  # For Depends and Form
import requests

def llm(q, local_llm, cloud_llm):
    """Process query using the selected model."""
    if cloud_llm == "gemini":
        selected = "gemini"
    elif local_llm in ["ollama", "lmstudio"]:
        selected = local_llm
    else:
        return "Error: No valid model selected"
    # Implementation details omitted for brevity (same as original)
    return "Sample response"

def add_analysis_routes(rt, get_user):
    @rt('/analyze', methods=['POST'])
    async def analyze(r: Request, q: str = Form(), local_llm: str = Form(default=""), cloud_llm: str = Form(default=""), email: str = Depends(get_user)):
        selected = local_llm if local_llm in ["ollama", "lmstudio"] else cloud_llm if cloud_llm == "gemini" else "ollama"
        r.session['selected_llm'] = selected
        response = llm(q, local_llm, cloud_llm)
        return Div(
            Div(
                Label("Local Models:", for_="local_llm"),
                Select(
                    Option("Ollama", value="ollama", selected=local_llm == "ollama"),
                    Option("LMStudio", value="lmstudio", selected=local_llm == "lmstudio"),
                    name="local_llm", id="local_llm",
                    cls="selected" if local_llm in ["ollama", "lmstudio"] else "",
                    onchange="document.getElementById('cloud_llm').selectedIndex = 0; document.getElementById('cloud_llm').classList.remove('selected'); this.classList.add('selected'); this.form.requestSubmit()",
                    value="" if cloud_llm == "gemini" else local_llm
                ),
                cls="model-group"
            ),
            Div(
                Label("Cloud Models:", for_="cloud_llm"),
                Select(
                    Option("Select cloud model", value="", disabled=True, hidden=True),
                    Option("Gemini", value="gemini", selected=cloud_llm == "gemini"),
                    name="cloud_llm", id="cloud_llm",
                    cls="selected" if cloud_llm == "gemini" else "",
                    onchange="document.getElementById('local_llm').selectedIndex = 0; document.getElementById('local_llm').classList.remove('selected'); this.classList.add('selected'); this.form.requestSubmit()",
                    value="gemini" if cloud_llm == "gemini" else ""
                ),
                cls="model-group"
            ),
            Input(id="q", name="q", value=q),
            Button("Analyze", type="submit"),
            Div(response, id="resp"),
            hx_post="/analyze", hx_target="#resp", hx_swap="innerHTML", hx_include="#local_llm, #cloud_llm"
        )