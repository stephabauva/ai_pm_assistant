"""Type stubs for fastapi.templating module."""
from typing import Any, Dict, Optional

class Jinja2Templates:
    """Jinja2 templates class."""
    def __init__(
        self,
        directory: str,
        **kwargs: Any,
    ) -> None: ...
    
    def TemplateResponse(
        self,
        name: str,
        context: Dict[str, Any],
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None,
        media_type: str = "text/html",
    ) -> Any: ...