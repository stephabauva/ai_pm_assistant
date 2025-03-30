"""Type stubs for fastapi package."""
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union, overload

class FastAPI:
    """FastAPI application class."""
    def __init__(self, **kwargs: Any) -> None: ...
    def mount(self, path: str, app: Any, name: Optional[str] = None) -> None: ...
    def exception_handler(self, exc_class_or_status_code: Union[Type[Exception], int]) -> Callable: ...

class HTTPException(Exception):
    """HTTP Exception class."""
    def __init__(self, status_code: int, detail: Any = None, headers: Optional[Dict[str, str]] = None) -> None: ...
    status_code: int
    detail: Any
    headers: Optional[Dict[str, str]]

class Request:
    """Request class."""
    def __init__(self, **kwargs: Any) -> None: ...
    @property
    def session(self) -> Dict[str, Any]: ...
    @property
    def headers(self) -> Dict[str, str]: ...

T = TypeVar('T')

def Depends(dependency: Optional[Callable[..., T]] = None, *, use_cache: bool = True) -> T: ...

from .form import Form