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
                message = body.get("error") or body.get("message") or resp.text
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

    def get_post(self, code: str) -> dict[str, Any]:
        """Get a post by its share code.

        Returns:
            A dict with ``post`` containing ``code``, ``url``, ``title``,
            ``description``, ``postPrivacy``, ``created``, and optionally
            ``urls`` plus ``isAlbum`` for album posts, and ``file``
            (``size``, ``size_formatted``, ``mime_type``, and ``dimensions``
            with ``width``/``height``).
        """
        return self._request("GET", f"/posts/{code}")

    def upload(
        self,
        file: Union[str, bytes, BinaryIO],
        privacy: str = "unlisted",
        title: Optional[str] = None,
        description: Optional[str] = None,
        post_type: Optional[str] = None,
    ) -> dict[str, Any]:
        """Upload a file.

        Args:
            file: A file path (str), raw bytes, or a file-like object.
            privacy: One of ``public``, ``unlisted``, or ``private``.
            title: Optional post title (max 30 chars).
            description: Optional post description (max 200 chars).
            post_type: ``album`` (default) or ``individual``. Only applies
                when uploading two or more files.

        Returns:
            A dict with ``message``, ``url``, ``file`` (containing ``size``,
            ``size_formatted``, ``mime_type``, and optionally ``dimensions``
            with ``width``/``height``), ``processing_time`` (ms), and
            optionally ``post`` (``code``, ``url``, ``postPrivacy``).
        """
        if privacy not in ("public", "unlisted", "private"):
            raise ValueError(f"Invalid privacy setting: {privacy!r}")
        if post_type is not None and post_type not in ("album", "individual"):
            raise ValueError(f"Invalid post_type: {post_type!r}")

        headers = {"post-privacy": privacy}
        if title is not None:
            headers["post-title"] = title
        if description is not None:
            headers["post-description"] = description
        if post_type is not None:
            headers["post-type"] = post_type

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

    def list_uploads(self, limit: Optional[int] = None) -> dict[str, Any]:
        """List the authenticated user's recent uploads.

        Args:
            limit: Maximum uploads to return (1-1000).

        Returns:
            A dict with ``uploads`` list, each containing ``code``,
            ``isAlbum``, ``url``, ``size`` (bytes), ``size_formatted``,
            and ``uploaded`` (ISO 8601).
        """
        params: dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        return self._request("GET", "/uploads", params=params if params else None)

    def edit_upload(
        self,
        code: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        privacy: Optional[str] = None,
    ) -> dict[str, Any]:
        """Edit an existing upload.

        Args:
            code: The share code of the upload to edit.
            title: New title (max 30 chars). Empty string to clear.
            description: New description (max 200 chars). Empty string to clear.
            privacy: One of ``public``, ``unlisted``, or ``private``.
        """
        headers: dict[str, str] = {"code": code}
        if title is not None:
            headers["title"] = title
        if description is not None:
            headers["description"] = description
        if privacy is not None:
            if privacy not in ("public", "unlisted", "private"):
                raise ValueError(f"Invalid privacy setting: {privacy!r}")
            headers["post-privacy"] = privacy
        return self._request("PATCH", "/editUpload", headers=headers)

    def append_upload(
        self,
        code: str,
        files: list[Union[str, bytes, BinaryIO]],
    ) -> dict[str, Any]:
        """Append 1 or more files to an existing album post.

        The post's share code, privacy, title, and description are preserved.
        Albums cap at 9 files total; requests that would exceed the cap are
        rejected. New files inherit the post's privacy — returned URLs are
        signed with a 24-hour expiry for private posts.

        Args:
            code: The share code of the post to append to.
            files: A list where each item is a file path (str), raw bytes, or
                a file-like object.

        Returns:
            A dict with ``message``, ``post`` (``code``, ``url``,
            ``postPrivacy``, ``fileCount``), ``files`` (list of successfully
            added files with ``fileName``, ``url``, ``size``,
            ``size_formatted``, ``mime_type``, ``status``, optional
            ``dimensions``), and optionally ``failed``.
        """
        if not code:
            raise ValueError("code is required")
        if not files:
            raise ValueError("files must be a non-empty list")

        headers = {"post-code": code}

        # requests' `files` param accepts a list of (field_name, value) tuples
        # to send multiple parts under the same field name.
        open_handles: list[BinaryIO] = []
        try:
            parts: list[tuple[str, tuple[str, Any]]] = []
            for idx, file in enumerate(files):
                if isinstance(file, str):
                    filename = os.path.basename(file)
                    fh = open(file, "rb")
                    open_handles.append(fh)
                    parts.append(("file", (filename, fh)))
                elif isinstance(file, bytes):
                    parts.append(("file", ("upload", file)))
                else:
                    name = getattr(file, "name", "upload")
                    if isinstance(name, str):
                        name = os.path.basename(name)
                    parts.append(("file", (name, file)))

            return self._request(
                "POST", "/appendUpload", files=parts, headers=headers
            )
        finally:
            for fh in open_handles:
                try:
                    fh.close()
                except Exception:
                    pass

    def delete_upload(self, filename: str) -> dict[str, Any]:
        """Delete an upload by filename."""
        return self._request("DELETE", "/deleteUpload", headers={"file": filename})

    def report_post(self, code: str, reason: str = "") -> dict[str, Any]:
        """Report a post.

        Args:
            code: The share code of the post to report.
            reason: Optional reason for the report.
        """
        return self._request("POST", "/reports", json={"code": code, "reason": reason})
