# Code Summary

This application is an AI-Powered Product Management Assistant for competitive analysis using LLMs.

## Main Components

- **`main.py`**: Application entry point, sets up FastHTML, and integrates modules.
  - Purpose: Initializes the app and router, connects modules.

- **`auth.py`**: Manages Google OAuth2 authentication.
  - `add_auth_routes(rt)`: Registers login and callback routes.
  - Purpose: Handles user login and session setup.

- **`dashboard.py`**: Renders the main dashboard interface.
  - `add_dashboard_routes(rt, get_user)`: Adds the dashboard route with model selection UI.
  - Purpose: Displays the UI for selecting LLMs and submitting queries.

- **`analysis.py`**: Processes analysis queries with LLMs.
  - `add_analysis_routes(rt, get_user)`: Adds the analysis route.
  - `llm(q, local_llm, cloud_llm)`: Calls the selected LLM (Ollama, LMStudio, or Gemini).
  - Purpose: Handles query processing and LLM responses.

- **`utils.py`**: Utility functions and constants.
  - `get_user(r: Request)`: Dependency to verify user authentication.
  - `SP`: System prompt for the LLM.
  - Purpose: Shared utilities and configuration.

## Key Functionalities

- **Authentication**: Google OAuth2 login, managed in `auth.py`.
- **Dashboard**: UI for LLM selection and query input, in `dashboard.py`.
- **Analysis**: Query processing with local/cloud LLMs, in `analysis.py`.

## Notes

- Uses Redis for session management (configured in `main.py`).
- CSS is currently in `main.py` but could move to `static/styles.css`.
- See `prd.md` for product requirements context.