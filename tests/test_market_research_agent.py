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