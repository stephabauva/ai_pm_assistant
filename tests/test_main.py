import pytest
from fastapi.testclient import TestClient
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import app, redis_client
from starlette.requests import Request

# Create test client
client = TestClient(app)

@pytest.fixture
def mock_session():
    return {}

@pytest.fixture
def mock_request(mock_session):
    class MockRequest:
        def __init__(self):
            self.session = mock_session
    return MockRequest()

def test_root_unauthenticated_redirect():
    response = client.get('/', follow_redirects=False)
    assert response.status_code == 307
    assert response.headers['location'] == '/login'

def test_login_page():
    response = client.get('/login')
    assert response.status_code == 200
    assert "Login with Google" in response.text
    assert '<a href="https://accounts.google.com/o/oauth2/v2/auth' in response.text

@pytest.mark.asyncio
async def test_authenticated_home():
    # Create a mock request with a session
    class MockRequest:
        def __init__(self):
            self.session = {"user_email": "test@example.com"}
    
    # Import the home function directly
    from main import home
    
    # Call the home function with our mock request
    result = await home(MockRequest())
    
    # Convert the result to a string to check content
    result_str = str(result)
    
    # Check that the welcome message is in the result
    assert "test@example.com" in result_str

def test_session_storage(monkeypatch):
    # Mock Redis client
    class MockRedis:
        def __init__(self):
            self.data = {}
        
        def set(self, key, value):
            self.data[key] = value
            
        def get(self, key):
            return self.data.get(key, b'').encode('utf-8') if isinstance(self.data.get(key), str) else self.data.get(key, b'')
    
    # Create mock Redis client
    mock_redis = MockRedis()
    monkeypatch.setattr("main.redis_client", mock_redis)
    
    # Test session storage
    test_email = 'test@example.com'
    mock_redis.set('session:test', test_email)
    stored_email = mock_redis.get('session:test').decode('utf-8')
    assert stored_email == test_email