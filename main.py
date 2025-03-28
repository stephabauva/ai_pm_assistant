from fasthtml.common import *
from redis import Redis
from auth import add_auth_routes
from dashboard import add_dashboard_routes
from analysis import add_analysis_routes
from utils import get_user, SP

app, rt = fast_app(with_session=True)
redis = Redis(host='localhost', port=6379, db=0)

# Add CSS (could move to static/styles.css)
css = Style("""
    .card {border: 1px solid #ddd; padding: 1.5rem; border-radius: 8px; max-width: 450px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);}
    .btn {padding: 0.6rem 1.2rem; background: #007bff; color: white; text-decoration: none; border-radius: 4px; border: none; cursor: pointer; font-weight: 500; transition: background 0.2s;}
    .btn:hover {background: #0069d9;}
    .model-group {margin-bottom: 1.2rem;}
    .model-group > label {display: block; margin-bottom: 0.4rem; font-weight: 500; color: #444;}
    .model-group > select {
        padding: 0.6rem;
        margin: 0.3rem 0;
        width: 100%;
        border: 2px solid #ddd;
        border-radius: 4px;
        background: #f8f9fa;
        color: #333;
        cursor: pointer;
        transition: all 0.2s;
    }
    .model-group > select:hover {
        border-color: #aaa;
    }
    .selected {
        background-color: #f0f8ff;
        border-color: #007bff !important;
        box-shadow: 0 0 0 2px rgba(0,123,255,0.25);
    }
    input[type="text"] {
        padding: 0.6rem;
        margin: 0.5rem 0 1rem;
        width: 100%;
        border: 2px solid #ddd;
        border-radius: 4px;
    }
    input[type="text"]:focus {
        border-color: #007bff;
        outline: none;
        box-shadow: 0 0 0 2px rgba(0,123,255,0.25);
    }
""")  # Same as original

# Register routes
add_auth_routes(rt)
add_dashboard_routes(rt, get_user)
add_analysis_routes(rt, get_user)

if __name__ == '__main__':
    serve(host='localhost', port=5001)