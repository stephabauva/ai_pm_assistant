import sys
sys.path.append(".")
import pytest
from fastapi.testclient import TestClient
import fasthtml
from main import app

# Create test client
client = TestClient(app)

def test_root_route():
    # Test GET request to root route
    response = client.get('/')
    
    # Check status code
    assert response.status_code == 200
    
    # Check if title is in response
    assert "AI-Powered Product Management Assistant" in response.text
    
    # Check if placeholder text is in response
    assert "Welcome to your PM Assistant" in response.text
    
    # Check if HTML structure is present
    assert "<h1>" in response.text
    assert "<p>" in response.text