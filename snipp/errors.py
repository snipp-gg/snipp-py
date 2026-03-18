class SnippError(Exception):
    """Exception raised when the Snipp API returns a non-200 response."""

    def __init__(self, status: int, message: str) -> None:
        self.status = status
        self.message = message
        super().__init__(f"[{status}] {message}")
