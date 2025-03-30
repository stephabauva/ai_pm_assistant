# ---- File: code_summary.md ----

<!-- AI USE: This file provides a concise overview of the codebase structure. Keep it brief, focusing only on main components and their core functions. -->

# Code Summary

This application is an AI-Powered Product Management Assistant using LLMs for specialized tasks like competitive analysis, featuring structured outputs via Pydantic models.

## Core Components

-   **`main.py`**: Application entry point, sets up FastHTML/FastAPI, integrates modules. Manually configures `SessionMiddleware` with `same_site` and `https_only` options for enhanced security. Includes exception handlers for HTTP and generic exceptions using Jinja2 templates, and mounts the `static` directory for serving static files. Test routes `/trigger_error` and `/test_404` have been added to facilitate testing of error handlers. Return types have been added to the route functions. Fixed duplicate route registration issue.
-   **`config.py`**: Manages all application configuration using `pydantic-settings`, loading from `.env`.
-   **`llm_client.py`**: Contains the `AIClient` class, responsible for generic communication with different LLM provider APIs (Gemini, Ollama, LMStudio). It now uses `aiohttp` for making requests to the Ollama API. Return types and type hints have been added. URL construction has been fixed to handle trailing slashes in base URLs to prevent 404 errors.
-   **`utils.py`**: Common utility functions, including the `get_user` authentication dependency that raises HTTPException with a 307 status code for unauthenticated users.

## Web Interface & Authentication

-   **`auth.py`**: Manages Google OAuth2 authentication flow using settings from `config.py`. Return types have been added to the route functions.
-   **`dashboard.py`**: Renders the main dashboard UI (currently focused on competitive analysis). Now links to a local stylesheet (`/static/styles.css`) instead of a CDN. Includes a "Use sample" button to populate the query input. Return types have been added to the route functions.
-   **`analysis.py`**: Defines the web routes (`/analyze`, `/analyze-result`) for initiating analysis tasks. The `/analyze` route initiates the analysis and uses HTMX to poll the `/analyze-result` route. The `/analyze-result` route either returns the analysis result or keeps the poll alive. It acts as a bridge between the web request and the appropriate agent, handling loading states and formatting results/errors for the UI. It also demonstrates how to initiate background tasks for potentially long-running operations. Return types and type hints have been added. The route handlers now retrieve form data manually. Fixed to include model selection radio buttons in responses.

## Agent System

-   **`agents/`**: Directory containing logic for specific AI agents. Now includes an `__init__.py` file to make it a proper Python package.
-   **`agents/market_research_agent.py`**: Implements the competitive analysis task.
    -   Defines specific prompts (system instructions, schema guidance).
    *   Contains `analyze_competition(query, model)` function which uses `llm_client.AIClient` to interact with LLMs and `schemas.market_research.CompetitiveAnalysis` to parse the results. Return types and type hints have been added. Improved error handling for invalid JSON responses.
-   **`schemas/`**: Directory containing Pydantic models for defining structured data. Now includes an `__init__.py` file to make it a proper Python package.
    -   **`schemas/market_research.py`**: Defines `CompetitorInfo`, `MarketTrend`, and `CompetitiveAnalysis` models used by the Market Research Agent.

## Static Files and Templates

-   **`static/`**: Directory containing static files such as CSS (`styles.css`).
    -   **`static/styles.css`**: Contains basic CSS styles for the application, including placeholders for Tailwind CSS classes.
-   **`templates/`**: Directory containing Jinja2 templates for rendering HTML.
    -   **`templates/error.html`**: Template for rendering error pages (404, 500, etc.) with consistent styling. Updated to properly display error messages for test routes.

## Testing

-   **`api_tests/`**: Contains standalone scripts for direct testing of external APIs.
    -   `test_ollama.py`: Tests the Ollama API.
    -   `test_gemini.py`: Tests the Gemini API.
    -   `tests_usage.md`: Provides instructions on how to use the test files.
-   **`integration_tests/`**: Contains integration and unit tests for the main application logic.
    -   `test_main.py`: Tests web routes, authentication flow, error handling, and HTMX interactions. Updated to handle edge cases and match actual application behavior.
    -   `test_market_research_agent.py`: Tests the specific logic of the market research agent, including success cases for different LLM providers and error handling. Updated to properly test error conditions.
    -   `integration_tests_usage.md`: Provides instructions on how to use the integration test files. Updated to reflect the current test suite structure and usage.

## Type Stubs

-   `fasthtml-stubs/`: Contains type stubs for the `fasthtml` library.
    -   `__init__.pyi`
    -   `common.pyi`
    -   `components.pyi`
-   `fastapi-stubs/`: Contains type stubs for the `fastapi` library.
    -   `__init__.pyi`
    -   `form.pyi`
    -   `responses.pyi`
    -   `staticfiles.pyi`
    -   `templating.pyi`
    -   `security.pyi`
    -   `params.pyi`
-   `starlette-stubs/`: Contains type stubs for the `starlette` library.
    -   `__init__.pyi`
    -   `exceptions.pyi`
    -   `requests.pyi`
    -   `responses.pyi`
