from __future__ import annotations

import os
from typing import Any, BinaryIO, Optional, Union

import requests

from .errors import SnippError

BASE_URL = "https://api.snipp.gg"
REGIONS = ("eu-west-1", "us-west-1")


class SnippClient:
    """Python client for the Snipp API."""

    def __init__(self, api_key: str, region: Optional[str] = None) -> None:
        """Create a new Snipp API client.

        Args:
            api_key: Your Snipp API key.
            region: Optional regional endpoint to pin requests to, one of
                ``eu-west-1`` or ``us-west-1``. Uploads run at the same speed
                either way; this controls which region stores your files.
        """
        if not api_key:
            raise ValueError("api_key is required")
        if region is not None and region not in REGIONS:
            raise ValueError(f"Unknown region. Expected one of: {', '.join(REGIONS)}")
        self._base_url = f"https://{region}.api.snipp.gg" if region else BASE_URL
        self._session = requests.Session()
        self._session.headers["api-key"] = api_key

    def _request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> Any:
        resp = self._session.request(method, f"{self._base_url}{path}", **kwargs)
        if not 200 <= resp.status_code < 300:
            body = None
            try:
                body = resp.json()
                message = body.get("error") or body.get("message") or resp.text
            except Exception:
                message = resp.text
            raise SnippError(resp.status_code, message, body)
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
            params["include_posts"] = str(include_posts).lower()
        if posts_limit is not None:
            params["posts_limit"] = posts_limit
        return self._request("GET", f"/users/{user_id}", params=params)

    def get_post(self, code: str) -> dict[str, Any]:
        """Get a post by its share code.

        Team posts are only readable by members of that team.

        Returns:
            A dict with ``post`` containing ``code``, ``url``, ``title``,
            ``description``, ``post_privacy``, ``created``, ``views``,
            ``comment_count``, ``priority``, ``files`` (each with ``index``,
            ``file_name``, ``url``, and when known ``width``, ``height``,
            ``mime_type``, ``size``, ``size_formatted``), and optionally
            ``urls`` plus ``is_album`` for album posts, ``thumbnail_url`` for
            videos, ``file`` (``size``, ``size_formatted``, ``mime_type``, and
            ``dimensions`` with ``width``/``height``), and ``moderated`` or
            ``restricted`` for the owner.
            ``like_count`` is present on every post except team posts, which
            cannot be liked.
        """
        return self._request("GET", f"/posts/{code}")

    def upload(
        self,
        file: Union[str, bytes, BinaryIO],
        privacy: Optional[str] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        post_type: Optional[str] = None,
    ) -> dict[str, Any]:
        """Upload a file.

        Args:
            file: A file path (str), raw bytes, or a file-like object.
            privacy: One of ``public``, ``unlisted``, or ``private``.
                Defaults to the server default (``private``) when omitted.
            title: Optional post title (max 30 chars).
            description: Optional post description (max 200 chars).
            post_type: Sent as the ``post-type`` header. Has no effect
                through ``upload()``, which sends a single file; use
                ``append_upload`` to build an album.

        Returns:
            A dict with ``message``, ``url``, ``file`` (containing ``size``,
            ``size_formatted``, ``mime_type``, and optionally ``dimensions``
            with ``width``/``height``), ``processing_time`` (ms), and
            optionally ``post`` (``code``, ``url``, ``post_privacy``,
            ``priority``, plus ``is_album`` and ``file_count`` on albums).
        """
        if privacy is not None and privacy not in ("public", "unlisted", "private"):
            raise ValueError(f"Invalid privacy setting: {privacy!r}")
        if post_type is not None and post_type not in ("album", "individual"):
            raise ValueError(f"Invalid post_type: {post_type!r}")

        headers = {}
        if privacy is not None:
            headers["post-privacy"] = privacy
        if post_type is not None:
            headers["post-type"] = post_type

        data = {}
        if title is not None:
            data["title"] = title
        if description is not None:
            data["description"] = description

        if isinstance(file, str):
            filename = os.path.basename(file)
            with open(file, "rb") as fh:
                files = {"file": (filename, fh)}
                return self._request("POST", "/upload", files=files, data=data, headers=headers)
        elif isinstance(file, bytes):
            files = {"file": ("upload", file)}
            return self._request("POST", "/upload", files=files, data=data, headers=headers)
        else:
            name = getattr(file, "name", "upload")
            if isinstance(name, str):
                name = os.path.basename(name)
            files = {"file": (name, file)}
            return self._request("POST", "/upload", files=files, data=data, headers=headers)

    def list_uploads(self, limit: Optional[int] = None) -> dict[str, Any]:
        """List the authenticated user's recent uploads.

        Args:
            limit: Maximum uploads to return (1-1000).

        Returns:
            A dict with ``uploads`` list, each containing ``code``,
            ``is_album``, ``url``, ``title``, ``size`` (bytes),
            ``size_formatted``, ``uploaded`` (ISO 8601), ``priority``, and
            ``thumbnail_url`` for videos.
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
        fields: dict[str, Any] = {}
        if title is not None:
            fields["title"] = (None, title)
        if description is not None:
            fields["description"] = (None, description)
        if privacy is not None:
            if privacy not in ("public", "unlisted", "private"):
                raise ValueError(f"Invalid privacy setting: {privacy!r}")
            headers["post-privacy"] = privacy
        return self._request("PATCH", "/editUpload", headers=headers, files=fields or None)

    def append_upload(
        self,
        code: str,
        files: list[Union[str, bytes, BinaryIO]],
    ) -> dict[str, Any]:
        """Append 1 or more files to an existing album post.

        The post's share code, privacy, title, and description are preserved.
        Albums cap at 50 files total; requests that would exceed the cap are
        rejected. New files inherit the post's privacy; returned URLs are
        signed with a 24-hour expiry for private posts.

        Args:
            code: The share code of the post to append to.
            files: A list where each item is a file path (str), raw bytes, or
                a file-like object.

        Returns:
            A dict with ``message``, ``post`` (``code``, ``url``,
            ``post_privacy``, ``file_count``, ``priority``), ``files`` (list of successfully
            added files with ``file_name``, ``url``, ``size``,
            ``size_formatted``, ``mime_type``, ``status``, optional
            ``dimensions``), and optionally ``failed``.
        """
        if not code:
            raise ValueError("code is required")
        if not files:
            raise ValueError("files must be a non-empty list")

        headers = {"post-code": code}

        open_handles: list[BinaryIO] = []
        try:
            parts: list[tuple[str, tuple[str, Any]]] = []
            for file in files:
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
            reason: Optional reason for the report (max 200 chars).
        """
        return self._request("POST", "/report-post", json={"code": code, "reason": reason})
