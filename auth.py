from fasthtml.common import *
from fastapi.security import OAuth2PasswordBearer # Keep for potential future use? Currently unused.
import httpx
import json
import os # Keep os for potential other uses, but not getenv here
import logging
# Import the global settings instance
from config import settings

logger = logging.getLogger(__name__)

# Validate required OAuth settings are present
if not settings.google_client_id or not settings.google_client_secret:
    logger.critical("Google OAuth credentials (GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET) are missing in config/env!")
    # Optionally raise an exception here to prevent startup without OAuth configured
    # raise RuntimeError("Google OAuth configuration is incomplete.")

# Construct the redirect URI based on the app's base URL
# Ensure it matches EXACTLY what's configured in Google Cloud Console
REDIRECT_URI = f"{str(settings.app_base_url).rstrip('/')}/auth/callback"

# Not using FastAPI's OAuth2PasswordBearer flow directly here, but define for clarity
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token") # Example if needed later

def add_auth_routes(rt):
    @rt('/login')
    async def login(r: Request):
        # Redirect to main page if already logged in
        if r.session.get('user_email'):
            return RedirectResponse(url='/')

        # Ensure OAuth is configured before attempting login
        if not settings.google_client_id or not settings.google_client_secret:
             return PlainTextResponse("OAuth is not configured correctly on the server.", status_code=500)

        # Construct Google OAuth URL using settings
        auth_endpoint = str(settings.google_auth_uri)
        client_id = settings.google_client_id

        # URL encode parameters properly (FastHTML's A() doesn't do this automatically)
        from urllib.parse import urlencode
        params = urlencode({
            'client_id': client_id,
            'redirect_uri': REDIRECT_URI,
            'response_type': 'code',
            'scope': 'openid email profile' # Standard scopes
        })
        login_url = f"{auth_endpoint}?{params}"
        logger.info(f"Redirecting user to Google login: {login_url}")

        # Basic login page
        return Title("Login"), Main(
            H1("AI PM Assistant Login"),
            P("Please log in using your Google account."),
            A("Login with Google", href=login_url, cls="btn", style="display: inline-block; margin-top: 1rem;"),
            cls="container text-center p-8" # Added some basic styling
        )

    @rt('/auth/callback')
    async def cb(r: Request, code: str | None = None, error: str | None = None):
        # Handle potential errors returned from Google
        if error:
            logger.error(f"OAuth callback error from Google: {error}")
            # Redirect to login with an error message (consider query param or flash message)
            return RedirectResponse(url='/login?error=oauth_failed') # Simple example
        if not code:
             logger.error("OAuth callback called without 'code' parameter.")
             return RedirectResponse(url='/login?error=missing_code')

        # Ensure OAuth is configured before proceeding
        if not settings.google_client_id or not settings.google_client_secret:
             logger.error("OAuth callback received but server OAuth is not configured.")
             return PlainTextResponse("OAuth is not configured correctly on the server.", status_code=500)

        # Exchange code for token
        token_endpoint = str(settings.google_token_uri)
        client_id = settings.google_client_id
        client_secret = settings.google_client_secret.get_secret_value() # Use secret value

        token_data = {
            'code': code,
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': REDIRECT_URI,
            'grant_type': 'authorization_code'
        }

        async with httpx.AsyncClient() as c:
            try:
                logger.info(f"Exchanging code for token at: {token_endpoint}")
                token_response = await c.post(token_endpoint, data=token_data)
                token_response.raise_for_status() # Raise exception for 4xx/5xx errors
                token_json = token_response.json()
                access_token = token_json.get('access_token')

                if not access_token:
                    logger.error(f"Access token not found in Google's response: {token_json}")
                    return RedirectResponse(url='/login?error=token_exchange_failed')

                # Get user info
                userinfo_endpoint = str(settings.google_userinfo_uri)
                logger.info(f"Fetching user info from: {userinfo_endpoint}")
                userinfo_response = await c.get(userinfo_endpoint, headers={'Authorization': f'Bearer {access_token}'})
                userinfo_response.raise_for_status()
                userinfo_json = userinfo_response.json()
                user_email = userinfo_json.get('email')

                if not user_email:
                    logger.error(f"Email not found in userinfo response: {userinfo_json}")
                    return RedirectResponse(url='/login?error=userinfo_failed')

                # Store email in session and redirect to dashboard
                r.session['user_email'] = user_email
                logger.info(f"User logged in successfully: {user_email}")
                return RedirectResponse(url='/', status_code=303) # Use 303 See Other after POST-like action

            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error during OAuth flow: {e.response.status_code} - {e.response.text}")
                return RedirectResponse(url='/login?error=oauth_http_error')
            except Exception as e:
                logger.exception(f"Unexpected error during OAuth callback: {e}")
                return RedirectResponse(url='/login?error=internal_error')