# snipp

A Python wrapper for the [Snipp API](https://api.snipp.gg).

## Features

- Upload files from paths, bytes, or file objects
- Upload, edit, append, and delete files and album posts
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
me = client.get_user()

# Upload a file
result = client.upload("screenshot.png", privacy="unlisted")

# List your uploads
uploads = client.list_uploads()

# Delete an upload
client.delete_upload("a3f7b2c91d4e8f0612ab34cd56ef7890.png")
```

## API

### `SnippClient(api_key, region=None)`

Create a client. The key is sent via the `api-key` header on every request.

| Argument | Type | Description |
| --- | --- | --- |
| `api_key` | `str` | Your Snipp API key. |
| `region` | `str` | Optional. Pin requests to a regional endpoint, `"eu-west-1"` or `"us-west-1"`. Uploads run at the same speed either way; this controls which region stores your files. Omit to use `api.snipp.gg`. |

```python
client = SnippClient(api_key="YOUR_API_KEY", region="eu-west-1")
```

### `get_user(user_id="@me", include_posts=None, posts_limit=None)`

Fetch a user profile. Pass `"@me"` (default) for the authenticated user. Set `include_posts=True` and `posts_limit` (1-50) to include their posts.

```python
user = client.get_user("@me", include_posts=True, posts_limit=10)
```

### `get_post(code)`

Get a post by its share code. Team posts are only readable by members of that team, and omit `like_count`.

```python
post = client.get_post("AbC123")["post"]
```

### `upload(file, privacy=None, title=None, description=None, post_type=None)`

Upload a file. `file` can be a path string, raw bytes, or an open file object. `privacy` must be `"public"`, `"unlisted"`, or `"private"`; it defaults to `private` when omitted. `title` caps at 30 chars, `description` at 200. `post_type` (`"album"` or `"individual"`) is sent as the `post-type` header and has no effect through `upload()`, which sends a single file; use `append_upload` to build an album.

```python
result = client.upload("image.png", privacy="unlisted")
print(result["url"])
```

### `list_uploads(limit=None)`

List the authenticated user's recent uploads (`limit` 1-1000). Each item includes the upload URL, size metadata, the associated post `code` when one exists, and `is_album` for uploads that belong to an album post.

```python
uploads = client.list_uploads(limit=100)
```

### `edit_upload(code, title=None, description=None, privacy=None)`

Edit an existing upload's title, description, or privacy. Empty strings clear the title or description.

```python
client.edit_upload("AbC123", title="New title", privacy="public")
```

### `append_upload(code, files)`

Append 1 or more files to an existing album post. Albums cap at 50 files total.

```python
client.append_upload("AbC123", ["extra.png"])
```

### `delete_upload(filename)`

Delete an upload by its filename.

```python
client.delete_upload("a3f7b2c91d4e8f0612ab34cd56ef7890.png")
```

### `report_post(code, reason="")`

Report a post, with an optional reason (max 200 chars).

```python
client.report_post("AbC123", "Spam")
```

## Error Handling

All API errors raise a `SnippError` with `status`, `message`, and `body` attributes. `body` is the parsed JSON error response, or `None` when the response was not JSON. It carries the fields the API sends alongside `error`, such as `suspended` on a suspended user or `moderated` on a moderated post.

```python
from snipp import SnippClient, SnippError

try:
    client.get_user("987654321098765432")
except SnippError as err:
    if err.body and err.body.get("suspended"):
        print(f"{err.body['username']} is suspended")
    else:
        print(err.status, err.message)
```

## Contributing

We welcome suggestions and improvements:

- Open an issue
- Submit a pull request that adheres to our [Terms of Service](https://snipp.gg/terms) and [Privacy Policy](https://snipp.gg/privacy)

## License

MIT License © 2026 Snipp. See [LICENSE](LICENSE) for full details.
