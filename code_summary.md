<!-- AI USE: This file provides a concise overview of the codebase structure. Keep it brief, focusing only on main components and their core functions. -->

# Code Summary

This application is an AI-Powered Product Management Assistant for competitive analysis using LLMs with structured outputs via Pydantic models.

## Main Components

- **`main.py`**: Application entry point, sets up FastHTML, and integrates modules.

- **`auth.py`**: Manages Google OAuth2 authentication.
  - `add_auth_routes(rt)`: Registers login and callback routes.

- **`dashboard.py`**: Renders the main dashboard interface.

  - `add_dashboard_routes(rt, get_user)`: Adds the dashboard route with model selection UI.

- **`analysis.py`**: Processes analysis queries with LLMs.
  - `add_analysis_routes(rt, get_user)`: Adds the analysis route.
  - `llm(q, model)`: Calls the selected LLM with structured output processing.

- **`ai_agent.py`**: Implements Pydantic models and API clients.
  - `AIClient`: Client for making API calls to different LLM providers.
  - `CompetitiveAnalysis`: Pydantic model for structured competitive analysis.

- **`utils.py`**: Utility functions.
  - `get_user(r: Request)`: Dependency to verify user authentication.
