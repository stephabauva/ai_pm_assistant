<!-- AI USE: This file provides a concise overview of the codebase structure. Keep it brief, focusing only on main components and their core functions. -->

# Code Summary

This application is an AI-Powered Product Management Assistant using LLMs for specialized tasks like competitive analysis, featuring structured outputs via Pydantic models. It utilizes FastAPI for the backend and FastHTML/HTMX for a dynamic web interface.

## Core Components

-   **`main.py`**: Application entry point. Initializes FastAPI/FastHTML, registers routes, configures middleware (sessions, static files), sets up Jinja2 templating (for errors), defines global exception handlers, and starts the Uvicorn server.
-   **`config.py`**: Manages all application configuration using `pydantic-settings`, loading variables from `.env`. Defines the main `Settings` model.
-   **`llm_client.py`**: Contains the `AIClient` class, providing a unified interface for making API calls to different LLM providers (Gemini via `httpx`, Ollama via `aiohttp`, LMStudio via `httpx`). Handles basic request/response logic and error reporting for API interactions. Includes URL normalization logic.
-   **`utils.py`**: Common utility functions, notably the `get_user` dependency for checking user authentication via session data and raising `HTTPException` for redirects.

## Web Interface & Authentication

-   **`auth.py`**: Defines routes (`/login`, `/auth/callback`) and logic for Google OAuth2 authentication, using configuration from `config.py`.
-   **`dashboard.py`**: Defines the main dashboard route (`/`) which renders the primary UI for interacting with the Competitive Analysis Agent, including model selection and the query form. Links to the static CSS file.
-   **`analysis.py`**: Defines the web routes (`/analyze`, `/analyze-result`) handling the analysis workflow.
    -   `/analyze` (POST): Receives the form submission, returns an initial loading state UI snippet containing an HTMX polling trigger.
    -   `/analyze-result` (POST): Acts as the HTMX polling target. Calls the appropriate agent function, formats the successful structured result or error message into HTML, and returns it along with OOB swaps for UI elements (like radio buttons). This response replaces the loading state, stopping the poll.

## Agent System

-   **`agents/`**: Directory containing logic for specific AI agents (`__init__.py` makes it a package).
    -   **`market_research_agent.py`**: Implements the competitive analysis task. Defines agent-specific prompts (system instruction, schema guidance with examples). Contains the `analyze_competition(query, model)` function which orchestrates the process: uses `llm_client.AIClient` to call the selected LLM, then attempts to parse and validate the JSON response using the `CompetitiveAnalysis` Pydantic schema. Returns a dictionary containing either the structured data or error details.
-   **`schemas/`**: Directory containing Pydantic models (`__init__.py` makes it a package).
    -   **`market_research.py`**: Defines `CompetitorInfo`, `MarketTrend`, and `CompetitiveAnalysis` Pydantic models, specifying the expected structured output for the market research task. Includes schema examples used in prompts.

## Static Files and Templates

-   **`static/`**: Contains static assets served directly by FastAPI (e.g., CSS, potentially JS or images later).
    -   **`static/styles.css`**: Main CSS file for the application. (Currently basic, intended for Tailwind CSS build output).
-   **`templates/`**: Contains Jinja2 HTML templates.
    -   **`templates/error.html`**: Generic template used by global exception handlers to render user-friendly error pages (404, 500, etc.).

## Testing

-   **`api_tests/`**: Contains standalone scripts for direct testing of external LLM APIs (Ollama, Gemini). Includes `tests_usage.md` guide.
-   **`integration_tests/`**: Contains automated tests (`pytest`) for the application's internal logic and integration.
    -   `test_main.py`: Tests FastAPI routes, authentication, HTMX responses, and error handling (using `TestClient`).
    -   `test_market_research_agent.py`: Tests the agent's logic, mocking the `llm_client.AIClient` to verify success and error handling paths (JSON parsing, validation).
    -   `integration_tests_usage.md`: Guide for running integration tests.

## Type Stubs

-   `fasthtml-stubs/`, `fastapi-stubs/`, `starlette-stubs/`: Contain custom type stub files (`*.pyi`) to aid `mypy` in static type checking for libraries lacking complete type information.