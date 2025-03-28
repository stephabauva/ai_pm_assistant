# Code Summary

This application is an AI-Powered Product Management Assistant for competitive analysis using LLMs with structured outputs via Pydantic models.

## Main Components

- **`main.py`**: Application entry point, sets up FastHTML, and integrates modules.
  - Purpose: Initializes the app and router, connects modules.

- **`auth.py`**: Manages Google OAuth2 authentication.
  - `add_auth_routes(rt)`: Registers login and callback routes.
  - Purpose: Handles user login and session setup.

- **`dashboard.py`**: Renders the main dashboard interface.
  - `add_dashboard_routes(rt, get_user)`: Adds the dashboard route with model selection UI.
  - Features:
    * Tailwind CSS styling
    * Radio button model selection (Ollama, LMStudio, Gemini)
    * Modern UI components
    * Information about Pydantic AI integration
  - Purpose: Displays the UI for selecting LLMs and submitting queries.

- **`analysis.py`**: Processes analysis queries with LLMs.
  - `add_analysis_routes(rt, get_user)`: Adds the analysis route.
  - `llm(q, model)`: Calls the selected LLM with structured output processing.
  - Features:
    * Structured plain text output from Pydantic models with safe data access
    * Async API calls to LLM providers
    * HTMX-powered UI updates
    * Enhanced debug mode for troubleshooting API responses
    * Improved error handling for missing or malformed data
    * HTML-free response formatting for consistent display
  - Purpose: Handles query processing and structured LLM responses.

- **`ai_agent.py`**: Implements Pydantic models and API clients.
  - `AIClient`: Client for making API calls to different LLM providers.
  - `CompetitiveAnalysis`: Pydantic model for structured competitive analysis.
  - Features:
    * Structured data models (CompetitorInfo, MarketTrend)
    * Async API clients for Ollama, LMStudio, and Gemini (updated to use Gemini 1.5 Flash)
    * Pydantic integration for structured outputs
    * Enhanced parsing of LLM responses into structured data
    * Advanced HTML detection and intelligent content extraction from HTML responses
    * Strict enforcement of plain text output format with explicit anti-HTML instructions
    * Robust error handling and fallback mechanisms for API errors
    * Safe dictionary access for structured data rendering
  - Purpose: Provides structured AI capabilities and API integrations.

- **`utils.py`**: Utility functions and constants.
  - `get_user(r: Request)`: Dependency to verify user authentication.
  - `SP`: System prompt for the LLM with explicit instructions to avoid HTML output.
  - Purpose: Shared utilities and configuration.

## Key Functionalities

- **Authentication**: Google OAuth2 login, managed in `auth.py`.
- **Dashboard**: Modern UI with Tailwind CSS and radio button model selection.
- **Analysis**: Query processing with local/cloud LLMs via structured interface.
- **Structured AI**: Pydantic models for consistent, structured outputs with manual parsing of LLM responses.
- **Multi-Model Support**: Support for Ollama, LMStudio, and Gemini.

## Notes

- Uses Redis for session management (configured in `main.py`).
- Tailwind CSS included via CDN (could be built locally for production).
- Environment variables for API keys and endpoints (.env file).
- Comprehensive test suite for AI agent functionality.
- Added `test_gemini.py` for direct testing of Gemini API connectivity.
- See `prd.md` for product requirements context.