class DevError(Exception):
    """A failure the CLI reports on its last line and exits non-zero (CLI-14)."""

    def __init__(self, message: str, code: int = 1):
        super().__init__(message)
        self.code = code
