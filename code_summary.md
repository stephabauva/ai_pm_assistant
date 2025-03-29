# ---- File: code_summary.md ----

<!-- AI USE: This file provides a concise overview of the codebase structure. Keep it brief, focusing only on main components and their core functions. -->

# Code Summary

This application is an AI-Powered Product Management Assistant using LLMs for specialized tasks like competitive analysis, featuring structured outputs via Pydantic models.

## Core Components

-   **`main.py`**: Application entry point, sets up FastHTML/FastAPI, integrates modules.
-   **`config.py`**: Manages all application configuration using `pydantic-settings`, loading from `.env`.
-   **`llm_client.py`**: Contains the `AIClient` class, responsible for generic communication with different LLM provider APIs (Gemini, Ollama, LMStudio).
-   **`utils.py`**: Common utility functions, including the `get_user` authentication dependency.

## Web Interface & Authentication

-   **`auth.py`**: Manages Google OAuth2 authentication flow using settings from `config.py`.
-   **`dashboard.py`**: Renders the main dashboard UI (currently focused on competitive analysis).
-   **`analysis.py`**: Defines the web routes (`/analyze`, `/analyze-result`) for initiating analysis tasks. It acts as a bridge between the web request and the appropriate agent, handling loading states and formatting results/errors for the UI.

## Agent System

-   **`agents/`**: Directory containing logic for specific AI agents.
    -   **`agents/market_research_agent.py`**: Implements the competitive analysis task.
        -   Defines specific prompts (system instructions, schema guidance).
        *   Contains `analyze_competition(query, model)` function which uses `llm_client.AIClient` to interact with LLMs and `schemas.market_research.CompetitiveAnalysis` to parse the results.
-   **`schemas/`**: Directory containing Pydantic models for defining structured data.
    -   **`schemas/market_research.py`**: Defines `CompetitorInfo`, `MarketTrend`, and `CompetitiveAnalysis` models used by the Market Research Agent.

## Testing

-   **`tests/`**: Contains unit and integration tests.
    -   `test_main.py`: Tests web routes and basic application flow.
    -   `test_market_research_agent.py` (previously `test_ai_agent.py`): Tests the specific logic of the market research agent, likely mocking the `llm_client.AIClient`.
-   **`test_gemini.py`**: Standalone script for direct testing of the Gemini API.
