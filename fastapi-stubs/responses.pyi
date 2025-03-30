"""Type stubs for fastapi.responses module."""
from typing import Any, Dict, Optional, Union

class Response:
    """Base response class."""
    def __init__(
        self,
        content: Any = None,
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None,
        media_type: Optional[str] = None,
    ) -> None: ...

class HTMLResponse(Response):
    """HTML response class."""
    def __init__(
        self,
        content: Any = None,
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None,
        media_type: str = "text/html",
    ) -> None: ...

class RedirectResponse(Response):
    """Redirect response class."""
    def __init__(
        self,
        url: str,
        status_code: int = 307,
        headers: Optional[Dict[str, str]] = None,
    ) -> None: ...

class PlainTextResponse(Response):
    """Plain text response class."""
    def __init__(
        self,
        content: Any = None,
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None,
        media_type: str = "text/plain",
    ) -> None: ...