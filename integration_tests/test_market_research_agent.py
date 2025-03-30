# ---- File: tests/test_market_research_agent.py (Previously test_ai_agent.py) ----

import pytest
from unittest.mock import AsyncMock, patch
import json

# Import the function to test
from agents.market_research_agent import analyze_competition

# Import the schema for verification
from schemas.market_research import CompetitiveAnalysis

# Mock the AIClient methods directly within the test or using fixtures
@pytest.mark.asyncio
@patch('agents.market_research_agent.AIClient') # Patch the client where it's instantiated
async def test_analyze_competition_ollama_success(MockAIClient):
    """Test successful analysis using Ollama mock."""

    # Configure the mock client instance and its methods
    mock_instance = MockAIClient.return_value
    mock_instance.call_ollama = AsyncMock(return_value=json.dumps({ # Mock returns valid JSON string
        "competitors": [{"name": "MockComp", "strengths": ["s1"], "weaknesses": ["w1"], "market_share": "10%", "key_features": ["f1"], "pricing": "$10"}],
        "market_trends": [{"trend": "MockTrend", "impact": "mock impact", "opportunity": None, "threat": None}],
        "recommendations": ["rec1"],
        "summary": "Mock summary"
    }))

    query = "Analyze mock market"
    model = "ollama"

    result = await analyze_competition(query, model)

    # Assertions
    assert "structured" in result
    assert "error" not in result
    assert result["structured"]["summary"] == "Mock summary"
    assert result["structured"]["competitors"][0]["name"] == "MockComp"
    mock_instance.call_ollama.assert_called_once() # Verify the correct client method was called

# Add more tests for Gemini, LMStudio, error cases (JSONDecodeError, ValidationError, API errors)
# ...

# --- Mock Data ---
MOCK_VALID_LLM_RESPONSE = json.dumps({
    "competitors": [{"name": "ValidComp", "strengths": ["s1"], "weaknesses": ["w1"], "market_share": "10%", "key_features": ["f1"], "pricing": "$10"}],
    "market_trends": [{"trend": "ValidTrend", "impact": "impact", "opportunity": None, "threat": None}],
    "recommendations": ["rec1"],
    "summary": "Valid summary"
})

MOCK_INVALID_SCHEMA_RESPONSE = json.dumps({ # Missing 'summary'
    "competitors": [{"name": "InvalidSchemaComp", "strengths": ["s1"], "weaknesses": ["w1"], "market_share": "10%", "key_features": ["f1"], "pricing": "$10"}],
    "market_trends": [{"trend": "InvalidTrend", "impact": "impact", "opportunity": None, "threat": None}],
    "recommendations": ["rec1"]
})

MOCK_INVALID_JSON_RESPONSE = "{'this': 'is not json'"

MOCK_LLM_CLIENT_ERROR_RESPONSE = json.dumps({"error": "API Key Invalid", "details": "Authentication failed"})

# --- Success Tests for Other Providers ---
# Add tests for Gemini and LMStudio success cases

@pytest.mark.asyncio
@patch('agents.market_research_agent.AIClient')
async def test_analyze_competition_gemini_success(MockAIClient):
    """Test successful analysis using Gemini mock."""
    mock_instance = MockAIClient.return_value
    mock_instance.call_gemini = AsyncMock(return_value=MOCK_VALID_LLM_RESPONSE)
    result = await analyze_competition("Analyze valid market", "gemini")
    assert "structured" in result
    assert result["structured"]["summary"] == "Valid summary"
    mock_instance.call_gemini.assert_called_once()

@pytest.mark.asyncio
@patch('agents.market_research_agent.AIClient')
async def test_analyze_competition_lmstudio_success(MockAIClient):
    """Test successful analysis using LMStudio mock."""
    mock_instance = MockAIClient.return_value
    mock_instance.call_lmstudio = AsyncMock(return_value=MOCK_VALID_LLM_RESPONSE)
    result = await analyze_competition("Analyze valid market", "lmstudio")
    assert "structured" in result
    assert result["structured"]["summary"] == "Valid summary"
    mock_instance.call_lmstudio.assert_called_once()

# --- Error Handling Tests ---

@pytest.mark.asyncio
@patch('agents.market_research_agent.AIClient')
async def test_analyze_competition_llm_client_error(MockAIClient):
    """Test handling when the LLM client itself returns an error JSON."""
    mock_instance = MockAIClient.return_value
    mock_instance.call_gemini = AsyncMock(return_value=MOCK_LLM_CLIENT_ERROR_RESPONSE) # Simulate client error
    result = await analyze_competition("Analyze anything", "gemini")
    assert "error" in result
    assert "LLM call failed" in result["error"]
    assert "API Key Invalid" in result["error"]
    assert result.get("raw") == MOCK_LLM_CLIENT_ERROR_RESPONSE # Raw response should be preserved
    mock_instance.call_gemini.assert_called_once()

@pytest.mark.asyncio
@patch('agents.market_research_agent.AIClient')
async def test_analyze_competition_pydantic_validation_error(MockAIClient):
    """Test handling when LLM returns JSON that doesn't match the schema."""
    mock_instance = MockAIClient.return_value
    mock_instance.call_ollama = AsyncMock(return_value=MOCK_INVALID_SCHEMA_RESPONSE)
    result = await analyze_competition("Analyze invalid schema market", "ollama")
    assert "error" in result
    assert "did not match expected structure" in result["error"]
    assert "validation_errors" in result
    assert any("summary" in err["loc"] for err in result["validation_errors"]) # Check if summary missing error is listed
    assert result.get("raw") == MOCK_INVALID_SCHEMA_RESPONSE
    mock_instance.call_ollama.assert_called_once()

@pytest.mark.asyncio
@patch('agents.market_research_agent.AIClient')
async def test_analyze_competition_invalid_json_error(MockAIClient):
    """Test handling when LLM returns completely invalid JSON."""
    mock_instance = MockAIClient.return_value
    mock_instance.call_lmstudio = AsyncMock(return_value=MOCK_INVALID_JSON_RESPONSE)
    result = await analyze_competition("Analyze invalid json market", "lmstudio")
    assert "error" in result
    # The error message might be different due to how the validation is handled
    # It could be either a JSON decode error or a validation error
    assert "lmstudio" in result["error"]
    assert result.get("raw") == MOCK_INVALID_JSON_RESPONSE
    mock_instance.call_lmstudio.assert_called_once()

@pytest.mark.asyncio
@patch('agents.market_research_agent.AIClient')
async def test_analyze_competition_empty_response_error(MockAIClient):
    """Test handling when LLM returns an empty string."""
    mock_instance = MockAIClient.return_value
    mock_instance.call_ollama = AsyncMock(return_value="") # Empty string response
    result = await analyze_competition("Analyze empty market", "ollama")
    assert "error" in result
    assert "LLM ollama returned an empty response" in result["error"]
    assert result.get("raw") == ""
    mock_instance.call_ollama.assert_called_once()

# Add similar tests for Gemini and LMStudio success cases if not already present
# ...