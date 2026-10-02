from __future__ import annotations

from typing import Any, Literal, Optional, TypedDict

Privacy = Literal["public", "unlisted", "private"]
"""Post privacy."""

Plan = Literal["free", "plus", "ultra"]
"""A user's plan."""


class UserRef(TypedDict):
    """A user embedded in another resource, such as a post's ``author``.

    ``username`` is ``None`` when the user has none. ``avatar`` is always a
    URL; users without one get the default avatar URL.
    """

    id: str
    username: Optional[str]
    nickname: Optional[str]
    avatar: str
    verified: bool
    plan: Plan


class UsageWindow(TypedDict):
    """Usage within one limit window.

    ``used`` and ``limit`` are bytes for ``usage`` and minutes for
    ``priority_minutes``. ``resets_at`` is the ISO 8601 time the window
    resets, or ``None`` when no window is open.
    """

    used: int
    limit: int
    used_percent: float
    resets_at: Optional[str]


class Limits(TypedDict):
    """Your plan limits. ``max_file_size`` is the largest single file you can
    upload, in bytes; ``usage`` is the weekly upload quota and
    ``priority_minutes`` the priority (adaptive) streaming allowance."""

    max_file_size: int
    usage: UsageWindow
    priority_minutes: UsageWindow


class _UserFields(TypedDict):
    id: str
    username: Optional[str]
    nickname: Optional[str]
    avatar: str
    banner: Optional[str]
    bio: Optional[str]
    socials: Optional[dict[str, Any]]
    plan: Plan
    verified: bool
    staff: bool
    partner: bool
    translator: bool
    bug_hunter_tier: int
    suspended: bool
    created_at: Optional[str]
    custom_embed: Optional[dict[str, Any]]
    follower_count: int
    following_count: int
    following: bool
    blocking: bool


class User(_UserFields, total=False):
    """A user profile.

    ``username`` is ``None`` when the user has none, ``banner`` when unset,
    and ``created_at`` when unknown. ``following`` and ``blocking`` describe
    your relationship to the user and are ``False`` on yourself. ``api_key``,
    ``key_has_uploads_access``, ``upload_count`` and ``limits`` are only
    present on yourself.
    """

    api_key: str
    key_has_uploads_access: bool
    upload_count: int
    limits: Limits


class PostFile(TypedDict):
    """One file in a post.

    ``name`` is the stored filename (``<32 hex>.<ext>``) used by
    ``delete_file``. ``url`` is signed with a 24-hour expiry when the post is
    private. ``size``, ``mime_type``, ``width`` and ``height`` are ``None``
    when unknown; ``thumbnail_url`` is ``None`` unless the file is a video
    with a thumbnail.
    """

    name: str
    url: str
    size: Optional[int]
    mime_type: Optional[str]
    width: Optional[int]
    height: Optional[int]
    thumbnail_url: Optional[str]


class _PostFields(TypedDict):
    code: str
    url: str
    title: Optional[str]
    description: Optional[str]
    privacy: Privacy
    created_at: str
    view_count: int
    like_count: Optional[int]
    comment_count: int
    priority: bool
    file_count: int
    files: list[PostFile]
    team_id: Optional[str]
    author: Optional[UserRef]
    liked: Optional[bool]


class Post(_PostFields, total=False):
    """A post.

    ``url`` is the share page (``https://snipp.gg/p/<code>``). ``team_id`` is
    ``None`` on personal posts. ``like_count`` and ``liked`` are ``None`` on
    team posts, which cannot be liked. ``author`` is ``None`` when the author
    could not be resolved. ``moderated`` and ``restricted`` are
    only present for the owner.
    """

    moderated: bool
    restricted: bool


class UserResponse(TypedDict):
    """Response of ``get_user``."""

    user: User


class PostResponse(TypedDict):
    """Response of ``get_post`` and ``update_post``."""

    post: Post


class PostList(TypedDict):
    """One page of posts. Pass ``next_cursor`` as ``cursor`` to fetch the
    next page; it is ``None`` on the last page."""

    posts: list[Post]
    has_more: bool
    next_cursor: Optional[str]


class FailedFile(TypedDict):
    """A file that was rejected. ``index`` is its position in the request;
    ``error`` has the same shape as a failed request's ``error`` object,
    context fields included."""

    index: int
    error: dict[str, Any]


class UploadResponse(TypedDict):
    """Response of ``upload``. ``url`` is the direct URL of the uploaded
    file."""

    url: str
    post: Post


class _AddFilesFields(TypedDict):
    post: Post


class AddFilesResponse(_AddFilesFields, total=False):
    """Response of ``add_files``. ``failed`` is present only when some files
    were rejected."""

    failed: list[FailedFile]


class DeletedFile(TypedDict):
    """Response of ``delete_file``."""

    name: str
    deleted: bool


class DeletedPost(TypedDict):
    """Response of ``delete_post``."""

    code: str
    deleted: bool


class ReportResponse(TypedDict):
    """Response of ``report_post`` and ``report_user``."""

    reported: bool
