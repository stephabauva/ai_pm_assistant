"""Type stubs for fastapi.params module."""
from typing import Any, Callable, Optional, TypeVar

T = TypeVar('T')

def Form(
    default: Any = ...,
    *,
    media_type: str = "application/x-www-form-urlencoded",
    alias: Optional[str] = None,
    title: Optional[str] = None,
    description: Optional[str] = None,
    **extra: Any
) -> Any:
    """Return a callable that can be used as a dependency for form data."""
    ...