"""Type stubs for fastapi.staticfiles module."""
from typing import Any, Optional

class StaticFiles:
    """Static files class."""
    def __init__(
        self,
        directory: str,
        packages: Optional[Any] = None,
        html: bool = False,
        check_dir: bool = True,
    ) -> None: ...