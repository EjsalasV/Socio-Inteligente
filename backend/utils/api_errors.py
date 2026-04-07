from __future__ import annotations

from fastapi import HTTPException


def raise_api_error(
    *,
    status_code: int,
    code: str,
    message: str,
    action_hint: str,
    retryable: bool = False,
    details: dict | None = None,
) -> None:
    raise HTTPException(
        status_code=status_code,
        detail={
            "code": code,
            "message": message,
            "action_hint": action_hint,
            "retryable": bool(retryable),
            "details": details or {},
        },
    )

