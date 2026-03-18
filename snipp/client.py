from __future__ import annotations

import os
from io import BufferedIOBase, RawIOBase
from typing import Any, BinaryIO, Optional, Union

import requests

from .errors import SnippError

BASE_URL = "https://api.snipp.gg"


class SnippClient:
    """Python client for the Snipp API."""

    def __init__(self, api_key: str) -> None:
        if not api_key:
            raise ValueError("api_key is required")
        self._session = requests.Session()
        self._session.headers["api-key"] = api_key

    def _request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> Any:
        resp = self._session.request(method, f"{BASE_URL}{path}", **kwargs)
        if resp.status_code != 200:
            try:
                body = resp.json()
                message = body.get("message", resp.text)
            except Exception:
                message = resp.text
            raise SnippError(resp.status_code, message)
        return resp.json()

    def get_user(
        self,
        user_id: str = "@me",
        include_posts: Optional[bool] = None,
        posts_limit: Optional[int] = None,
    ) -> dict[str, Any]:
        """Get a user by ID. Use ``@me`` for the authenticated user."""
        params: dict[str, Any] = {}
        if include_posts is not None:
            params["includePosts"] = str(include_posts).lower()
        if posts_limit is not None:
            params["postsLimit"] = posts_limit
        return self._request("GET", f"/users/{user_id}", params=params)

    def upload(
        self,
        file: Union[str, bytes, BinaryIO],
        privacy: str = "unlisted",
    ) -> dict[str, Any]:
        """Upload a file.

        Args:
            file: A file path (str), raw bytes, or a file-like object.
            privacy: One of ``public``, ``unlisted``, or ``private``.
        """
        if privacy not in ("public", "unlisted", "private"):
            raise ValueError(f"Invalid privacy setting: {privacy!r}")

        headers = {"postprivacy": privacy}

        if isinstance(file, str):
            filename = os.path.basename(file)
            with open(file, "rb") as fh:
                files = {"file": (filename, fh)}
                return self._request("POST", "/upload", files=files, headers=headers)
        elif isinstance(file, bytes):
            files = {"file": ("upload", file)}
            return self._request("POST", "/upload", files=files, headers=headers)
        else:
            name = getattr(file, "name", "upload")
            if isinstance(name, str):
                name = os.path.basename(name)
            files = {"file": (name, file)}
            return self._request("POST", "/upload", files=files, headers=headers)

    def list_uploads(self) -> dict[str, Any]:
        """List the authenticated user's recent uploads."""
        return self._request("GET", "/uploads")

    def delete_upload(self, filename: str) -> dict[str, Any]:
        """Delete an upload by filename."""
        return self._request("DELETE", "/deleteUpload", headers={"file": filename})

    def discover(self) -> dict[str, Any]:
        """Browse public uploads."""
        return self._request("GET", "/discover")
