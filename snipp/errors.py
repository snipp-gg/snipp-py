from __future__ import annotations

from typing import Any, Optional


class SnippError(Exception):
    """Exception raised when the Snipp API returns a non-2xx response.

    Attributes:
        status: HTTP status code.
        type: ``error.type`` from the response, such as ``not_found`` or
            ``quota_exceeded``, or ``None`` when the response did not carry
            one.
        message: ``error.message`` from the response, or the HTTP status
            text when the response did not carry one.
        body: Parsed JSON response body, or ``None`` when the response was
            not JSON.
    """

    def __init__(
        self,
        status: int,
        message: str,
        body: Optional[Any] = None,
        type: Optional[str] = None,
    ) -> None:
        self.status = status
        self.type = type
        self.message = message
        self.body = body
        super().__init__(f"[{status}] {message}")
