# Integration Tests Usage Guide

This document provides instructions on how to use the integration test files in this project.

## 1. `test_main.py` and `test_market_research_agent.py`

### Description

These files contain integration and unit tests for the main application logic and the market research agent, respectively. They use the `pytest` framework with `pytest-asyncio` for testing asynchronous code.

### Prerequisites

-   `pytest` and `pytest-asyncio` must be installed: `pip install pytest pytest-asyncio pytest-mock`
-   The tests are designed to run without the application running, as they use FastAPI's TestClient
-   No external services (like Ollama) are required as all external calls are mocked

### Usage

1.  From the project root directory:
    ```bash
    python -m pytest integration_tests
    ```
    
    Or navigate to the `integration_tests` directory and run:
    ```bash
    cd integration_tests
    pytest
    ```

2.  To run specific test files:
    ```bash
    pytest test_main.py
    pytest test_market_research_agent.py
    ```

3.  To run a specific test:
    ```bash
    pytest test_main.py::test_dash_unauth
    pytest test_market_research_agent.py::test_analyze_competition_ollama_success
    ```

4.  To run with verbose output:
    ```bash
    pytest -v
    ```

### Test Coverage

- **test_main.py**: Tests web routes, authentication flow, error handling, and HTMX interactions
  - Authentication tests (authenticated/unauthenticated access)
  - Analysis route tests (form submission, loading states)
  - Analysis result tests (success and error cases)
  - Error handling tests (404, 500 errors)

- **test_market_research_agent.py**: Tests the market research agent functionality
  - Success cases for different LLM providers (Ollama, Gemini, LMStudio)
  - Error handling (invalid JSON, validation errors, API errors)

### Expected Output

`pytest` will run all the tests in the directory and print a summary of the results, including the number of tests passed, failed, and skipped.

Example output:

```
============================= test session starts ==============================
platform darwin -- Python 3.13.2, pytest-8.3.5, pluggy-1.5.0
rootdir: /Users/urdoom/Developer/ai_pm_assistant
collected 18 items                                  

integration_tests/test_main.py ...........    [ 61%]
integration_tests/test_market_research_agent.py .......    [100%]

========== 18 passed in 0.73s ===========
```

If any tests fail, `pytest` will provide detailed information about the failures, including tracebacks and assertion errors.