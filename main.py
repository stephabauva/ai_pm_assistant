from fasthtml.common import *
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2AuthorizationCodeBearer
from redis import Redis
import httpx
from starlette.requests import Request
from starlette.responses import RedirectResponse
import json

# Initialize FastHTML app
app, rt = fast_app(with_session=True)
redis_client = Redis(host='localhost', port=6379, db=0)

# Load Google OAuth2 credentials from client_secret.json or use defaults for testing
import os
try:
    with open('client_secret.json', 'r') as f:
        client_secret_data = json.load(f)
    GOOGLE_CLIENT_ID = client_secret_data['web']['client_id']
    GOOGLE_CLIENT_SECRET = client_secret_data['web']['client_secret']
except FileNotFoundError:
    # Use dummy values for testing
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', 'test-client-id')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', 'test-client-secret')
GOOGLE_REDIRECT_URI = 'http://localhost:5001/auth/callback'
GOOGLE_AUTH_URL = 'https://accounts.google.com/o/oauth2/v2/auth'
GOOGLE_TOKEN_URL = 'https://oauth2.googleapis.com/token'
GOOGLE_USERINFO_URL = 'https://www.googleapis.com/oauth2/v3/userinfo'

# OAuth2 setup - simplified for testing
from fastapi.security import OAuth2PasswordBearer

# Use a simpler OAuth2 scheme for testing
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Dependency to get current user
async def get_current_user(request: Request):
    session = request.session
    user_email = session.get('user_email')
    if not user_email:
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={'Location': '/login'}
        )
    return user_email

# Routes
@rt('/')
async def home(request: Request):
    # Check if user is authenticated
    session = request.session
    user_email = session.get('user_email')
    if not user_email:
        return RedirectResponse(url='/login', status_code=307)
    
    return (
        Title("AI-Powered Product Management Assistant"),
        Main(
            H1("AI-Powered Product Management Assistant"),
            P(f"Welcome, {user_email}"),
            cls="container"
        )
    )

@rt('/login')
async def login_page(request: Request):
    if request.session.get('user_email'):
        return RedirectResponse(url='/')
    auth_url = f"{GOOGLE_AUTH_URL}?client_id={GOOGLE_CLIENT_ID}&redirect_uri={GOOGLE_REDIRECT_URI}&response_type=code&scope=openid%20email%20profile"
    return (
        Title("Login"),
        Main(
            H1("Login"),
            A("Login with Google", href=auth_url, cls="btn"),
            cls="container"
        )
    )

@rt('/auth/callback')
async def auth_callback(request: Request, code: str):
    # Exchange code for token
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                'code': code,
                'client_id': GOOGLE_CLIENT_ID,
                'client_secret': GOOGLE_CLIENT_SECRET,
                'redirect_uri': GOOGLE_REDIRECT_URI,
                'grant_type': 'authorization_code'
            }
        )
        token_data = token_response.json()
        
        # Get user info
        access_token = token_data.get('access_token')
        user_response = await client.get(
            GOOGLE_USERINFO_URL,
            headers={'Authorization': f'Bearer {access_token}'}
        )
        user_info = user_response.json()
        
        # Store email in session
        request.session['user_email'] = user_info['email']
        
    return RedirectResponse(url='/')

# Run the app
if __name__ == '__main__':
    serve(host='localhost', port=5001)