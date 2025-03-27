from fasthtml.common import *
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from redis import Redis
import httpx
from starlette.requests import Request
from starlette.responses import RedirectResponse
import json, os

# App setup
app, rt = fast_app(with_session=True)
redis = Redis(host='localhost', port=6379, db=0)

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

# CSS
css = Style("""
    .card { border: 1px solid #ddd; padding: 1rem; border-radius: 5px; max-width: 300px; }
    .btn { padding: 0.5rem 1rem; background: #007bff; color: white; text-decoration: none; border-radius: 3px; }
""")

# User check
async def get_user(r: Request):
    email = r.session.get('user_email')
    print(f"Session: {r.session}")  # Debug output
    if not email:
        raise HTTPException(status_code=307, headers={'Location': '/login'})
    return email

# Routes
@rt('/')
async def dash(r: Request, email: str = Depends(get_user)):
    return (
        Title("AI-PM Dashboard"),
        css,
        Main(
            Div(
                H3("🔍 Competitive Analysis Agent", style="margin: 0"),
                Form(
                    Input(id="q", name="q", placeholder="e.g., Analyze CRM market competitors"),
                    Button("Analyze", type="submit"),
                    hx_post="/analyze", hx_target="#resp", hx_swap="innerHTML"
                ),
                Div(id="resp"),
                cls="card"
            ),
            cls="container"
        )
    )

@rt('/login')
async def login(r: Request):
    if r.session.get('user_email'):
        return RedirectResponse(url='/')
    url = f"{auth_url}?client_id={cid}&redirect_uri={ruri}&response_type=code&scope=openid%20email%20profile"
    return Title("Login"), css, Main(H1("Login"), A("Login with Google", href=url, cls="btn"), cls="container")

@rt('/auth/callback')
async def cb(r: Request, code: str):
    async with httpx.AsyncClient() as c:
        tok = await c.post(token_url, data={'code': code, 'client_id': cid, 'client_secret': csec, 'redirect_uri': ruri, 'grant_type': 'authorization_code'})
        acc = tok.json().get('access_token')
        usr = await c.get(userinfo_url, headers={'Authorization': f'Bearer {acc}'})
        r.session['user_email'] = usr.json()['email']
    return RedirectResponse(url='/')

@rt('/analyze', methods=['POST'])
async def analyze(r: Request, q: str = Form()):
    return Div("Analyzing competitors... (static response)", id="resp")

# Run
if __name__ == '__main__':
    serve(host='localhost', port=5001)