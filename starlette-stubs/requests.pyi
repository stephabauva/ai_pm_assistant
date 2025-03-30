"""Type stubs for starlette.requests module."""
from typing import Any, Dict, Optional, Awaitable

class FormData:
    """Form data class."""
    def get(self, key: str, default: Any = None) -> Any: ...

class Request:
    """Request class."""
    def __init__(self, **kwargs: Any) -> None: ...
    
    @property
    def session(self) -> Dict[str, Any]: ...
    
    @property
    def headers(self) -> Dict[str, str]: ...
    
    async def form(self) -> FormData: ...