# snipp

A Python wrapper for the [Snipp API](https://api.snipp.gg).

## Features

- Upload files from paths, bytes, or file objects
- Build albums and manage your posts
- Typed responses (`TypedDict`) for editor completion
- Simple error handling with `SnippError`

## Requirements

- Python 3.9 or higher
- A valid API key from the [Snipp Console](https://snipp.gg/settings/console)

Dependencies (automatically installed):
- `requests`

## Installation

```bash
pip install snipp
```

Or install from source:

```bash
pip install .
```

## Quick Start

```python
from snipp import SnippClient

client = SnippClient(api_key="YOUR_API_KEY")

# Get your own profile
me = client.get_user()["user"]

# Upload a file
result = client.upload("screenshot.png", privacy="unlisted")
print(result["url"], result["post"]["url"])

# List your posts
posts = client.list_posts()["posts"]

# Delete a post
client.delete_post(result["post"]["code"])
```

## API

Every method returns the parsed JSON response as a `dict`, typed with the `TypedDict` classes exported from `snipp` (`User`, `Post`, `PostFile`, `PostList`, and the rest).

### `SnippClient(api_key, region=None)`

Create a client. The key is sent via the `api-key` header on every request.

| Argument | Type | Description |
| --- | --- | --- |
| `api_key` | `str` | Your Snipp API key. |
| `region` | `str` | Optional. Pin requests to a regional endpoint, `"eu-west-1"` or `"us-west-1"`. Uploads run at the same speed either way; this controls which region stores your files. Omit to use `api.snipp.gg`. |

```python
client = SnippClient(api_key="YOUR_API_KEY", region="eu-west-1")
```

### `get_user(user_id="@me")`

Fetch a user profile. Pass `"@me"` (default) for the authenticated user. `api_key`, `key_has_uploads_access`, `upload_count`, and `limits` are only present on yourself.

```python
user = client.get_user("@me")["user"]
print(user["plan"], user["limits"]["usage"]["used_percent"])
```

### `get_user_posts(user_id, limit=None, cursor=None)`

List a user's public posts, newest first. Team, private, unlisted, moderated, and restricted posts are never included. Pass `"@me"` for your own public posts. `limit` is 1-100 (default 30); `cursor` is the `next_cursor` from the previous page.

```python
page = client.get_user_posts("987654321098765432", limit=10)
print(page["has_more"], page["next_cursor"])
```

### `list_posts(limit=None, cursor=None)`

List your own posts of every privacy, newest first. Team posts are not included. Takes the same `limit` and `cursor` as `get_user_posts`. Follow `next_cursor` until it is `None` to walk every page:

```python
cursor = None
while True:
    page = client.list_posts(limit=100, cursor=cursor)
    for post in page["posts"]:
        print(post["code"], post["privacy"])
    cursor = page["next_cursor"]
    if cursor is None:
        break
```

### `get_post(code)`

Get a post by its share code. Team posts are only readable by members of that team, and have `like_count` and `liked` set to `None`.

```python
post = client.get_post("AbC123")["post"]
print(post["url"], post["files"][0]["url"])
```

### `upload(file, privacy=None, title=None, description=None, post_type=None, include_metadata=None, priority=None)`

Upload a file as a new post. `file` can be a path string, raw bytes, or an open file object. `privacy` must be `"public"`, `"unlisted"`, or `"private"`; it defaults to `private` when omitted. `title` caps at 30 chars, `description` at 200. `post_type` (`"album"` or `"individual"`) is sent as the `post-type` header and has no effect through `upload()`, which sends a single file; use `add_files` to build an album. `include_metadata=True` keeps the file's metadata (EXIF, location, and the like), which the server strips when omitted. `priority` turns priority (adaptive) streaming for videos on or off; omitted, the server enables it when your plan is eligible. Returns `url` (the direct file URL) and `post`.

```python
result = client.upload("image.png", privacy="unlisted")
print(result["url"], result["post"]["url"])
```

### `update_post(code, title=None, description=None, privacy=None)`

Update a post's title, description, or privacy. Only the arguments you pass are changed; empty strings clear the title or description. A team post's privacy cannot be changed. Returns `post`.

```python
client.update_post("AbC123", title="New title", privacy="public")
```

### `add_files(code, files, include_metadata=None, priority=None)`

Add 1 or more files to an existing post, turning it into an album. Posts cap at 50 files total. New files inherit the post's privacy. `include_metadata` and `priority` work as on `upload()`. Returns `post`, plus `failed` when some files were rejected, each with its `index` and `error`.

```python
result = client.add_files("AbC123", ["extra.png"], include_metadata=True)
print(result["post"]["file_count"], result.get("failed", []))
```

### `delete_file(code, name)`

Delete one file from a post, by the `name` it has in `post["files"]`. Deleting a post's only file deletes the post.

```python
post = client.get_post("AbC123")["post"]
client.delete_file("AbC123", post["files"][1]["name"])
```

### `delete_post(code)`

Delete a post and every file in it.

```python
client.delete_post("AbC123")
```

### `report_post(code, reason=None)`

Report a post, with an optional reason (max 200 chars).

```python
client.report_post("AbC123", "Spam")
```

### `report_user(user_id, reason=None)`

Report a user, with an optional reason (max 200 chars).

```python
client.report_user("987654321098765432", "Impersonation")
```

## Error Handling

All API errors raise a `SnippError` with these attributes:

| Attribute | Type | Description |
|---|---|---|
| `status` | `int` | HTTP status code. |
| `type` | `str \| None` | Error type, such as `not_found`, `rate_limited`, or `quota_exceeded`. `None` when the response did not carry one. |
| `message` | `str` | Human-readable message, or the HTTP status text when the response did not carry one. |
| `body` | `dict \| None` | Parsed JSON response, or `None` when it was not JSON. Context fields live under `body["error"]`, such as `resets_at` on `quota_exceeded`. |

```python
from snipp import SnippClient, SnippError

try:
    client.upload("image.png")
except SnippError as err:
    if err.type == "quota_exceeded":
        print(f"Weekly quota used up, resets at {err.body['error']['resets_at']}")
    else:
        raise
```

## Migrating from 2.x

3.0 follows the reorganized Snipp API. Methods:

| 2.x | 3.0 |
|---|---|
| `list_uploads(limit)` | `list_posts(limit, cursor)`, cursor-paginated posts |
| `edit_upload(code, ...)` | `update_post(code, ...)` |
| `append_upload(code, files)` | `add_files(code, files)` |
| `delete_upload(filename)` | `delete_file(code, name)`, which now needs the post's share code |
| `get_user(user_id, include_posts, posts_limit)` | `get_user(user_id)` plus `get_user_posts(user_id, limit, cursor)` |
| `report_post(code, reason="")` | `report_post(code, reason=None)` |
| | New: `delete_post(code)`, `report_user(user_id, reason=None)` |

Responses:

- Posts use one shape everywhere: `privacy` (was `post_privacy`), `created_at` (was `created`), `view_count` (was `views`), `files[].name` (was `file_name`), and `file_count` replaces `is_album`. The top-level `urls`, `file`, and `thumbnail_url` are gone; read `files`.
- `upload()` returns `url` and `post`; `message`, `file`, and `processing_time` are gone.
- Users carry `plan` (`free`, `plus`, or `ultra`) in place of `plus`, `ultra`, and `badges`, `created_at` in place of `created`, and `blocking` in place of `blocked_by_you`.

Errors:

- The API now sends every error as an `error` object with `type`, `message`, and any context fields. `SnippError` gains `type`, `message` falls back to the HTTP status text instead of the raw response body, and context fields moved from the top of `body` into `body["error"]`. A check like `err.body.get("suspended")` becomes `err.type == "suspended"`.

## Contributing

We welcome suggestions and improvements:

- Open an issue
- Submit a pull request that adheres to our [Terms of Service](https://snipp.gg/terms) and [Privacy Policy](https://snipp.gg/privacy)

## License

MIT License © 2026 Snipp. See [LICENSE](LICENSE) for full details.
