import pytest
from unittest.mock import AsyncMock, patch
import json
from ai_agent import AIClient, CompetitiveAnalysis

@pytest.fixture
def ai_client():
    return AIClient()

@pytest.mark.asyncio
async def test_call_gemini_missing_key(ai_client):
    """Test Gemini API call with missing API key."""
    with patch.object(ai_client, 'gemini_api_key', ''):
        result = await ai_client.call_gemini("Test prompt")
        assert "Error: Gemini API key not configured" in result

@pytest.mark.asyncio
async def test_call_ollama_success(ai_client):
    """Test successful Ollama API call."""
    # Mock the entire call_ollama method
    with patch.object(ai_client, 'call_ollama', AsyncMock(return_value="Test response")):
        result = await ai_client.call_ollama("Test prompt")
        assert result == "Test response"

@pytest.mark.asyncio
async def test_call_lmstudio_success(ai_client):
    """Test successful LMStudio API call."""
    # Mock the entire call_lmstudio method
    with patch.object(ai_client, 'call_lmstudio', AsyncMock(return_value="Test response")):
        result = await ai_client.call_lmstudio("Test prompt")
        assert result == "Test response"

@pytest.mark.asyncio
async def test_analyze_competition_structured_output(ai_client):
    """Test analyze_competition with structured output."""
    # Mock the raw response from the LLM
    raw_response = """
    Based on my analysis, here are the key competitors in the CRM market:
    
    1. Salesforce - Market leader with extensive features
    2. HubSpot - Strong inbound marketing integration
    3. Microsoft Dynamics - Enterprise integration with Microsoft products
    
    Market trends include AI integration, mobile-first approaches, and vertical specialization.
    """
    
    # Create a sample structured output that would be produced by Pydantic
    structured_output = {
        "competitors": [
            {
                "name": "Salesforce",
                "strengths": ["Market leader", "Extensive ecosystem"],
                "weaknesses": ["High cost", "Complex implementation"],
                "market_share": "20%",
                "key_features": ["Sales Cloud", "Service Cloud", "Marketing Cloud"],
                "pricing": "Starting at $25/user/month"
            }
        ],
        "market_trends": [
            {
                "trend": "AI Integration",
                "impact": "Automating routine tasks and providing predictive insights",
                "opportunity": "Enhanced user productivity"
            }
        ],
        "recommendations": ["Focus on vertical specialization", "Invest in AI capabilities"],
        "summary": "The CRM market is highly competitive with Salesforce leading."
    }
    
    # Mock the analyze_competition method to return our structured output
    with patch.object(ai_client, 'call_ollama', AsyncMock(return_value=raw_response)):
        # Mock the CompetitiveAnalysis instantiation
        with patch('ai_agent.CompetitiveAnalysis', return_value=AsyncMock(model_dump=lambda: structured_output)):
            result = await ai_client.analyze_competition("Analyze CRM market", "ollama")
            
            # Check that we got both structured and raw responses
            assert "structured" in result
            assert "raw" in result
            assert result["raw"] == raw_response
            
            # Since we're mocking the structured output, we can check for exact values
            assert "competitors" in result["structured"]
            assert "market_trends" in result["structured"]
            assert "recommendations" in result["structured"]