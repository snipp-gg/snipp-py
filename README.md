# snipp

A Python wrapper for the [Snipp API](https://api.snipp.gg).

## Features

- Upload files from paths, bytes, or file objects
- Manage uploads and browse public content
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

# Browse public uploads
public = client.discover()
```

## API

### `SnippClient(api_key)`

Create a client. The key is sent via the `api-key` header on every request.

### `get_user(user_id="@me", include_posts=None, posts_limit=None)`

Fetch a user profile. Pass `"@me"` (default) for the authenticated user. Set `include_posts=True` and `posts_limit` (1--50) to include their posts.

```python
user = client.get_user("@me", include_posts=True, posts_limit=10)
```

### `upload(file, privacy="unlisted")`

Upload a file. `file` can be a path string, raw bytes, or an open file object. `privacy` must be `"public"`, `"unlisted"`, or `"private"`.

```python
result = client.upload("image.png", privacy="unlisted")
print(result["url"])
```

### `list_uploads()`

List the authenticated user's recent uploads. Each item includes the upload URL, size metadata, the associated post `code` when one exists, and `isAlbum` for uploads that belong to an album post.

```python
uploads = client.list_uploads()
```

### `delete_upload(filename)`

Delete an upload by its filename.

```python
client.delete_upload("a3f7b2c91d4e8f0612ab34cd56ef7890.png")
```

### `discover()`

Browse public uploads.

```python
feed = client.discover()
```

## Error Handling

All API errors raise a `SnippError` with `status` and `message` attributes.

```python
from snipp import SnippClient, SnippError

try:
    client.get_user("nonexistent")
except SnippError as err:
    print(err.status, err.message)
```

## Contributing

We welcome suggestions and improvements:

- Open an issue
- Submit a pull request that adheres to our [Terms of Service](https://snipp.gg/terms) and [Privacy Policy](https://snipp.gg/privacy)

## License

MIT License © 2026 Snipp. See [LICENSE](LICENSE) for full details.
