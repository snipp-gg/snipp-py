from __future__ import annotations

from typing import Any, Optional


class SnippError(Exception):
    """Exception raised when the Snipp API returns a non-2xx response.

    Attributes:
        status: HTTP status code.
        message: Error message from the API, or the raw response body.
        body: Parsed JSON error body, or ``None`` when the response was not
            JSON. Carries fields the API sends alongside ``error``, such as
            ``suspended`` on a suspended user or ``moderated`` on a moderated
            post.
    """

    def __init__(self, status: int, message: str, body: Optional[Any] = None) -> None:
        self.status = status
        self.message = message
        self.body = body
        super().__init__(f"[{status}] {message}")
