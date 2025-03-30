"""Type stubs for starlette.exceptions module."""
from typing import Any, Dict, Optional

class HTTPException(Exception):
    """HTTP Exception class."""
    def __init__(
        self,
        status_code: int,
        detail: Any = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> None: ...
    
    status_code: int
    detail: Any
    headers: Optional[Dict[str, str]]