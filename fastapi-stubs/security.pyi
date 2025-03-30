"""Type stubs for fastapi.security module."""
from typing import Any, Dict, Optional

class OAuth2PasswordBearer:
    """OAuth2 password bearer class."""
    def __init__(
        self,
        tokenUrl: str,
        scheme_name: Optional[str] = None,
        scopes: Optional[Dict[str, str]] = None,
        description: Optional[str] = None,
        auto_error: bool = True,
    ) -> None: ...