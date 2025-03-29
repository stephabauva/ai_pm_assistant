from fasthtml.common import *
# Removed Redis import, as it's unused globally
from auth import add_auth_routes
from dashboard import add_dashboard_routes
from analysis import add_analysis_routes
from utils import get_user
import uvicorn # Import uvicorn directly for serve function
import logging
# Import the global settings instance
from config import settings

# Setup basic logging configuration if not already set elsewhere
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Initialize FastHTML app with session middleware
# Use the SESSION_SECRET_KEY from settings
app, rt = fast_app(
    with_session=True,
    secret_key=settings.session_secret_key.get_secret_value()
)

# Removed global Redis instance initialization
# Removed embedded CSS - should be moved to a static file

# Register routes from other modules
add_auth_routes(rt)
add_dashboard_routes(rt, get_user)
add_analysis_routes(rt, get_user)

# --- Serve the application ---
# Define the serve function to use settings
def serve():
    logger.info(f"Starting server on {settings.app_host}:{settings.app_port}")
    uvicorn.run(
        app,
        host=settings.app_host,
        port=settings.app_port,
        # Consider adding reload=True based on an environment flag for development
        # reload=(os.getenv("APP_ENV", "production") == "development")
    )

if __name__ == '__main__':
    serve()