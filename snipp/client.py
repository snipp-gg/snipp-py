from __future__ import annotations

import os
from contextlib import ExitStack
from typing import Any, BinaryIO, Optional, Union
from urllib.parse import quote

import requests

from .errors import SnippError
from .models import (
    AddFilesResponse,
    DeletedFile,
    DeletedPost,
    PostList,
    PostResponse,
    ReportResponse,
    UploadResponse,
    UserResponse,
)

BASE_URL = "https://api.snipp.gg"
REGIONS = ("eu-west-1", "us-west-1")
PRIVACY_VALUES = ("public", "unlisted", "private")
POST_TYPES = ("album", "individual")

FileInput = Union[str, bytes, BinaryIO]


def _segment(value: str) -> str:
    return quote(value, safe="")


def _check_privacy(privacy: Optional[str]) -> None:
    if privacy is not None and privacy not in PRIVACY_VALUES:
        raise ValueError(f"Invalid privacy setting: {privacy!r}")


def _page_params(limit: Optional[int], cursor: Optional[str]) -> dict[str, Any]:
    params: dict[str, Any] = {}
    if limit is not None:
        params["limit"] = limit
    if cursor is not None:
        params["cursor"] = cursor
    return params


def _upload_headers(include_metadata: Optional[bool], priority: Optional[bool]) -> dict[str, str]:
    headers = {}
    if include_metadata is not None:
        headers["include-metadata"] = "true" if include_metadata else "false"
    if priority is not None:
        headers["priority"] = "true" if priority else "false"
    return headers


def _file_part(file: FileInput, stack: ExitStack) -> tuple[str, Any]:
    if isinstance(file, str):
        return (os.path.basename(file), stack.enter_context(open(file, "rb")))
    if isinstance(file, bytes):
        return ("upload", file)
    name = getattr(file, "name", "upload")
    return (os.path.basename(name) if isinstance(name, str) else "upload", file)


class SnippClient:
    """Python client for the Snipp API."""

    def __init__(self, api_key: str, region: Optional[str] = None) -> None:
        """Create a new Snipp API client.

        Args:
            api_key: Your Snipp API key.
            region: Optional regional endpoint to pin requests to, one of
                ``eu-west-1`` or ``us-west-1``. Uploads run at the same speed
                either way; this controls which region stores your files.
                Omit to use ``api.snipp.gg``.
        """
        if not api_key:
            raise ValueError("api_key is required")
        if region is not None and region not in REGIONS:
            raise ValueError(f"Unknown region. Expected one of: {', '.join(REGIONS)}")
        self._base_url = f"https://{region}.api.snipp.gg" if region else BASE_URL
        self._session = requests.Session()
        self._session.headers["api-key"] = api_key

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        resp = self._session.request(method, f"{self._base_url}{path}", **kwargs)
        if not 200 <= resp.status_code < 300:
            try:
                body = resp.json()
            except ValueError:
                body = None
            error = body.get("error") if isinstance(body, dict) else None
            if not isinstance(error, dict):
                error = {}
            message = error.get("message")
            error_type = error.get("type")
            raise SnippError(
                resp.status_code,
                message if isinstance(message, str) else resp.reason,
                body,
                error_type if isinstance(error_type, str) else None,
            )
        return resp.json()

    def get_user(self, user_id: str = "@me") -> UserResponse:
        """Get a user by ID.

        Args:
            user_id: User ID, or ``@me`` (the default) for the authenticated
                user.

        Returns:
            A dict with ``user``. ``api_key``, ``key_has_uploads_access``,
            ``upload_count`` and ``limits`` are only present on yourself.
        """
        return self._request("GET", f"/users/{_segment(user_id)}")

    def get_user_posts(
        self,
        user_id: str,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> PostList:
        """List a user's public posts, newest first.

        Team, private, unlisted, moderated, and restricted posts are never
        included.

        Args:
            user_id: User ID, or ``@me`` for the authenticated user.
            limit: Posts per page (1-100, default 30).
            cursor: ``next_cursor`` from the previous page.

        Returns:
            A dict with ``posts``, ``has_more``, and ``next_cursor``.
        """
        return self._request(
            "GET", f"/users/{_segment(user_id)}/posts", params=_page_params(limit, cursor)
        )

    def list_posts(
        self,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> PostList:
        """List the authenticated user's own posts of every privacy, newest first.

        Team posts are not included.

        Args:
            limit: Posts per page (1-100, default 30).
            cursor: ``next_cursor`` from the previous page.

        Returns:
            A dict with ``posts``, ``has_more``, and ``next_cursor``.
        """
        return self._request("GET", "/posts", params=_page_params(limit, cursor))

    def get_post(self, code: str) -> PostResponse:
        """Get a post by its share code.

        Team posts are only readable by members of that team.

        Args:
            code: Share code of the post.

        Returns:
            A dict with ``post``.
        """
        return self._request("GET", f"/posts/{_segment(code)}")

    def upload(
        self,
        file: FileInput,
        privacy: Optional[str] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        post_type: Optional[str] = None,
        include_metadata: Optional[bool] = None,
        priority: Optional[bool] = None,
    ) -> UploadResponse:
        """Upload a file as a new post.

        Args:
            file: A file path (str), raw bytes, or a file-like object.
            privacy: One of ``public``, ``unlisted``, or ``private``. Omitted,
                the server uploads as ``private``.
            title: Post title (max 30 chars).
            description: Post description (max 200 chars).
            post_type: Sent as the ``post-type`` header. Has no effect
                through ``upload()``, which sends a single file; use
                ``add_files`` to build an album.
            include_metadata: Keep the file's metadata (EXIF, location, and
                the like). Omitted, the server strips it.
            priority: Use priority (adaptive) streaming for videos. Omitted,
                the server enables it when your plan is eligible.

        Returns:
            A dict with ``url`` (the direct file URL) and ``post``.
        """
        _check_privacy(privacy)
        if post_type is not None and post_type not in POST_TYPES:
            raise ValueError(f"Invalid post_type: {post_type!r}")

        headers = _upload_headers(include_metadata, priority)
        if privacy is not None:
            headers["post-privacy"] = privacy
        if post_type is not None:
            headers["post-type"] = post_type

        data = {}
        if title is not None:
            data["title"] = title
        if description is not None:
            data["description"] = description

        with ExitStack() as stack:
            return self._request(
                "POST",
                "/upload",
                files={"file": _file_part(file, stack)},
                data=data,
                headers=headers,
            )

    def update_post(
        self,
        code: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        privacy: Optional[str] = None,
    ) -> PostResponse:
        """Update a post's title, description, or privacy.

        Only the fields you pass are changed. A team post's privacy cannot be
        changed.

        Args:
            code: Share code of the post.
            title: New title (max 30 chars). Empty string to clear.
            description: New description (max 200 chars). Empty string to clear.
            privacy: One of ``public``, ``unlisted``, or ``private``.

        Returns:
            A dict with the updated ``post``.
        """
        _check_privacy(privacy)
        fields = {"title": title, "description": description, "privacy": privacy}
        return self._request(
            "PATCH",
            f"/posts/{_segment(code)}",
            json={k: v for k, v in fields.items() if v is not None},
        )

    def add_files(
        self,
        code: str,
        files: list[FileInput],
        include_metadata: Optional[bool] = None,
        priority: Optional[bool] = None,
    ) -> AddFilesResponse:
        """Add 1 or more files to an existing post, turning it into an album.

        The post's share code, privacy, title, and description are preserved.
        Posts cap at 50 files total; requests that would exceed the cap are
        rejected. New files inherit the post's privacy.

        Args:
            code: Share code of the post.
            files: A list where each item is a file path (str), raw bytes, or
                a file-like object.
            include_metadata: Keep the files' metadata (EXIF, location, and
                the like). Omitted, the server strips it.
            priority: Use priority (adaptive) streaming for videos. Omitted,
                the server enables it when your plan is eligible.

        Returns:
            A dict with the updated ``post``, and ``failed`` when some files
            were rejected.
        """
        if not code:
            raise ValueError("code is required")
        if not files:
            raise ValueError("files must be a non-empty list")

        with ExitStack() as stack:
            parts = [("file", _file_part(file, stack)) for file in files]
            return self._request(
                "POST",
                f"/posts/{_segment(code)}/files",
                files=parts,
                headers=_upload_headers(include_metadata, priority),
            )

    def delete_file(self, code: str, name: str) -> DeletedFile:
        """Delete one file from a post.

        Deleting a post's only file deletes the post.

        Args:
            code: Share code of the post.
            name: Stored filename, as in ``post["files"][i]["name"]``.

        Returns:
            A dict with ``name`` and ``deleted``.
        """
        return self._request("DELETE", f"/posts/{_segment(code)}/files/{_segment(name)}")

    def delete_post(self, code: str) -> DeletedPost:
        """Delete a post and every file in it.

        Args:
            code: Share code of the post.

        Returns:
            A dict with ``code`` and ``deleted``.
        """
        return self._request("DELETE", f"/posts/{_segment(code)}")

    def report_post(self, code: str, reason: Optional[str] = None) -> ReportResponse:
        """Report a post to Snipp moderation.

        Args:
            code: Share code of the post.
            reason: Optional reason for the report (max 200 chars).

        Returns:
            A dict with ``reported``.
        """
        body = {} if reason is None else {"reason": reason}
        return self._request("POST", f"/posts/{_segment(code)}/report", json=body)

    def report_user(self, user_id: str, reason: Optional[str] = None) -> ReportResponse:
        """Report a user to Snipp moderation.

        Args:
            user_id: User ID.
            reason: Optional reason for the report (max 200 chars).

        Returns:
            A dict with ``reported``.
        """
        body = {} if reason is None else {"reason": reason}
        return self._request("POST", f"/users/{_segment(user_id)}/report", json=body)
