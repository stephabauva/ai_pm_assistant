# Integration Tests Usage Guide

This document provides instructions on how to use the integration test files in this project.

## 1. `test_main.py` and `test_market_research_agent.py`

### Description

These files contain integration and unit tests for the main application logic and the market research agent, respectively. They use the `pytest` framework.

### Prerequisites

-   `pytest` must be installed: `pip install pytest`
-   The application must be running (e.g., using `python main.py`).
-   Ollama needs to be running if tests involve the market research agent.

### Usage

1.  Navigate to the `integration_tests` directory:
    ```bash
    cd integration_tests
    ```
2.  Run the tests:
    ```bash
    pytest
    ```

### Expected Output

`pytest` will run all the tests in the directory and print a summary of the results, including the number of tests passed, failed, and skipped.

Example output:

```
============================= test session starts ==============================
platform darwin -- Python 3.9.6, pytest-7.4.0, pluggy-1.2.0
rootdir: /Users/urdoom/Developer/ai_pm_assistant/integration_tests
collected 5 items                                                              

test_main.py .....                                                        [100%]

============================== 5 passed in 1.23s ===============================
```

If any tests fail, `pytest` will provide detailed information about the failures, including tracebacks and assertion errors.