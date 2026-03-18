# snipp-py

A Python wrapper for the [Snipp API](https://api.snipp.gg).

## Installation

```bash
pip install snipp-py
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

# Browse public uploads
public = client.discover()
```

## Error Handling

All API errors raise `SnippError` with `status` and `message` attributes:

```python
from snipp import SnippClient, SnippError

client = SnippClient(api_key="YOUR_API_KEY")

try:
    user = client.get_user("unknown_id")
except SnippError as e:
    print(e.status)   # HTTP status code
    print(e.message)  # Error message from the API
```

## API Reference

### `SnippClient(api_key)`

Create a client. The key is sent via the `api-key` header on every request.

### `get_user(user_id="@me", include_posts=None, posts_limit=None)`

Fetch a user profile. Pass `"@me"` (default) for the authenticated user. Set `include_posts=True` and `posts_limit` (1--50) to include their posts.

### `upload(file, privacy="unlisted")`

Upload a file. `file` can be a path string, raw bytes, or an open file object. `privacy` must be `"public"`, `"unlisted"`, or `"private"`.

### `list_uploads()`

List the authenticated user's recent uploads.

### `delete_upload(filename)`

Delete an upload by its filename.

### `discover()`

Browse public uploads.

## License

MIT
