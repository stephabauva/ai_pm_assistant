from fastapi import HTTPException
from starlette.requests import Request

async def get_user(r: Request):
    """Check if the user is authenticated."""
    email = r.session.get('user_email')
    if not email:
        raise HTTPException(status_code=307, headers={'Location': '/login'})
    return email

SP = """You are a Competitive Analysis Agent..."""  # Full prompt as in original