"""API error utilities"""

from typing import Any, Optional
from fastapi import HTTPException, status as http_status


def raise_api_error(
    status_code: int = http_status.HTTP_400_BAD_REQUEST,
    code: str = "ERROR",
    message: str = "Error processing request",
    details: Optional[Any] = None,
    action_hint: str = "",
    retryable: bool = False,
) -> None:
    """
    Lanza una excepción API con formato consistente.
    
    Args:
        status_code: HTTP status code
        code: Error code (e.g., "VALIDATION_ERROR")
        message: Error message in Spanish
        details: Additional error details
        action_hint: Hint for what user should do
        retryable: Whether the request can be retried
    """
    raise HTTPException(
        status_code=status_code,
        detail={
            "code": code,
            "message": message,
            "action_hint": action_hint,
            "retryable": retryable,
            "details": details or {},
        },
    )
