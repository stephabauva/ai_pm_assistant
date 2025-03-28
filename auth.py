from fasthtml.common import *
from fastapi.security import OAuth2PasswordBearer
import httpx
import json
import os

# OAuth2 config
try:
    with open('client_secret.json', 'r') as f:
        creds = json.load(f)
    cid = creds['web']['client_id']
    csec = creds['web']['client_secret']
except FileNotFoundError:
    cid = os.environ.get('GOOGLE_CLIENT_ID', 'test-client-id')
    csec = os.environ.get('GOOGLE_CLIENT_SECRET', 'test-client-secret')
ruri = 'http://localhost:5001/auth/callback'
auth_url = 'https://accounts.google.com/o/oauth2/v2/auth'
token_url = 'https://oauth2.googleapis.com/token'
userinfo_url = 'https://www.googleapis.com/oauth2/v3/userinfo'
oauth2 = OAuth2PasswordBearer(tokenUrl="token")

def add_auth_routes(rt):
    @rt('/login')
    async def login(r: Request):
        if r.session.get('user_email'):
            return RedirectResponse(url='/')
        url = f"{auth_url}?client_id={cid}&redirect_uri={ruri}&response_type=code&scope=openid%20email%20profile"
        return Title("Login"), Main(H1("Login"), A("Login with Google", href=url, cls="btn"), cls="container")

    @rt('/auth/callback')
    async def cb(r: Request, code: str):
        async with httpx.AsyncClient() as c:
            tok = await c.post(token_url, data={'code': code, 'client_id': cid, 'client_secret': csec, 'redirect_uri': ruri, 'grant_type': 'authorization_code'})
            acc = tok.json().get('access_token')
            usr = await c.get(userinfo_url, headers={'Authorization': f'Bearer {acc}'})
            r.session['user_email'] = usr.json()['email']
        return RedirectResponse(url='/')