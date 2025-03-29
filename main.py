# ---- File: main.py ----

from fasthtml.common import *
# Import necessary types for exception handlers
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse # For returning HTML in error handlers
from starlette.exceptions import HTTPException as StarletteHTTPException # Import specific type

from auth import add_auth_routes
from dashboard import add_dashboard_routes
from analysis import add_analysis_routes, render_model_selection_oob # Import helper
from utils import get_user
import uvicorn
import logging
import traceback # For logging stack traces
import json

# Import the global settings instance
from config import settings

# Setup basic logging configuration
# Consider using FastAPI's logging integration for more advanced setups later
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s')
logger = logging.getLogger(__name__)

# Initialize FastHTML app with session middleware
app, rt = fast_app(
    with_session=True,
    secret_key=settings.session_secret_key.get_secret_value()
)

# --- Global Exception Handlers ---

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handles FastAPI's built-in HTTPExceptions (like redirects or 404s)."""
    logger.warning(f"Handling HTTPException: Status={exc.status_code}, Detail={exc.detail}")
    # For redirects (like in get_user), let the browser handle it
    if 300 <= exc.status_code < 400 and 'Location' in exc.headers:
        # Re-create the redirect response FastHTML understands
        return RedirectResponse(url=exc.headers['Location'], status_code=exc.status_code)

    # For other HTTP errors (e.g., 404 Not Found), return a user-friendly HTML page
    # You might want specific handlers for 404, 403, etc.
    error_content = f"HTTP Error {exc.status_code}: {exc.detail}"
    # Use Fasthtml components to render the error page
    page = Title(f"Error {exc.status_code}"), Main(
        H1(f"Error {exc.status_code}", cls="text-2xl text-red-600"),
        P(str(exc.detail) or "An error occurred."),
        A("Go back to Dashboard", href="/", cls="btn mt-4"), # Add a link back home
        cls="container mx-auto p-8 text-center"
    )
    return HTMLResponse(content=str(page), status_code=exc.status_code)

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Handles unexpected non-HTTP exceptions."""
    # Log the full traceback for unexpected errors
    tb_str = traceback.format_exc()
    logger.error(f"Unhandled exception caught: {exc.__class__.__name__}: {exc}")
    logger.error(f"Traceback:\n{tb_str}")

    # Inform the user generically without exposing internal details
    error_message = "An unexpected internal server error occurred. Please try again later or contact support if the issue persists."

    # Check if the request was likely an HTMX request (check headers)
    is_htmx = request.headers.get("hx-request") == "true"

    if is_htmx:
        # For HTMX requests, try to return an error within the target div
        # Determine the likely target (this is heuristic)
        target_id = request.headers.get("hx-target", "#resp") # Default to analysis response
        if not target_id.startswith("#"): target_id = f"#{target_id}" # Ensure it's an ID selector

        # Try to also update radio buttons if the target is #resp
        oob_content = ""
        if target_id == "#resp":
             selected_model = request.session.get('selected_llm', 'ollama') # Get last known model
             oob_content = str(render_model_selection_oob(selected_model))

        # Render error content for HTMX swap
        error_html = Div(
            H3("Application Error", cls="text-xl font-bold mb-3 text-red-600"),
            P(error_message, cls="text-red-800"),
            # Optionally add more debug info if in a specific DEV mode
            # Pre(f"Error type: {exc.__class__.__name__}", cls="text-xs text-gray-500") if settings.debug else "",
            id=target_id.lstrip('#'), # Set the ID for the swap target
            cls="p-4 bg-red-50 border border-red-200 rounded-lg shadow-md"
        )
        # Return the main error content plus any OOB swaps
        full_response_content = str(error_html) + oob_content
        return HTMLResponse(content=full_response_content, status_code=500)
    else:
        # For regular page loads, return a full error page
        page = Title("Internal Server Error"), Main(
            H1("Internal Server Error", cls="text-2xl text-red-600"),
            P(error_message),
            # Optionally add more debug info here too based on environment
            A("Go back to Dashboard", href="/", cls="btn mt-4"),
            cls="container mx-auto p-8 text-center"
        )
        return HTMLResponse(content=str(page), status_code=500)


# --- Route Registration ---
add_auth_routes(rt)
add_dashboard_routes(rt, get_user)
add_analysis_routes(rt, get_user)

# --- Serve the application ---
def serve():
    logger.info(f"Starting server on {settings.app_host}:{settings.app_port}")
    # Check for session key warning again just before serving
    if settings.session_secret_key.get_secret_value() == "default-insecure-secret-key-replace-me":
        logger.warning("SECURITY WARNING: Using default SESSION_SECRET_KEY. Server started but sessions are insecure.")
    uvicorn.run(
        "main:app", # Use string syntax for reload compatibility
        host=settings.app_host,
        port=settings.app_port,
        reload=True # Enable reload for development - TODO: Make conditional based on env
        # log_config=uvicorn.config.LOGGING_CONFIG # Can customize logging further if needed
    )

if __name__ == '__main__':
    serve()