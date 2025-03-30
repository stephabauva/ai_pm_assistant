# Test Files Usage Guide

This document provides instructions on how to use the test files in this project.

## 1. `test_ollama.py`

### Description
This script directly tests the Ollama API to ensure it is functioning correctly. It sends requests to two different API endpoints: `/api/chat` and `/v1/chat/completions`.

### Prerequisites
-   Ollama must be installed and running.
-   The `phi4` model must be available in Ollama. You can pull it using: `ollama pull phi4`

### Usage
1.  Ensure Ollama is running. Open a terminal and run:
    ```bash
    ollama serve
    ```
2.  In a separate terminal, run the script:
    ```bash
    python api_tests/test_ollama.py
    ```

### Expected Output
The script will print log messages indicating the status of each API call. A successful API call will result in a "Response status: 200" message and a snippet of the JSON response.

Example of successful output:

```
[2025-03-30 12:49:26,904] [INFO] Test 1: Direct API call to http://localhost:11434/api/chat
[2025-03-30 12:49:26,904] [INFO] Sending request to http://localhost:11434/api/chat
[2025-03-30 12:49:31,711] [INFO] Response status: 200
[2025-03-30 12:49:31,715] [INFO] Success! Response: {
  "model": "phi4",
  "created_at": "2025-03-30T10:49:31.704128Z",
  "message": {
    "role": "assistant",
    "content": "Hello! I'm here and ready to assist you. How can I help you today? \ud83d\ud...
```

If the API calls fail, the script will print error messages with the response status and error text.
## 2. `test_gemini.py`

### Description

This script directly tests the Gemini API.

### Prerequisites

-   A Gemini API key must be set in the `.env` file.
-   The `google-generativeai` library must be installed.

### Usage

1. Set the `GEMINI_API_KEY` in the `.env` file.
2. Run the script:
   ```bash
   python api_tests/test_gemini.py
   ```

### Expected Output

The script will print the response from the Gemini API if successful. If the API call fails, the script will print an error message.

## 3. `integration_tests/test_main.py` and `integration_tests/test_market_research_agent.py`

### Description

These files contain integration and unit tests for the main application logic and the market research agent, respectively. They use the `pytest` framework.

### Prerequisites

-   `pytest` must be installed: `pip install pytest`

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