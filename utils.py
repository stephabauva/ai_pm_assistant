# ---- File: utils.py ----

from fastapi import HTTPException
from starlette.requests import Request

async def get_user(r: Request):
    """Check if the user is authenticated."""
    email = r.session.get('user_email')
    if not email:
        # Redirect to login using a 307 Temporary Redirect
        # The browser will follow this redirect using the same method (GET/POST)
        # Note: TestClient might not follow automatically, but browsers will.
        raise HTTPException(status_code=307, detail="Not authenticated", headers={'Location': '/login'})
    return email

# SP variable removed - System prompt is now centralized in ai_agent.py