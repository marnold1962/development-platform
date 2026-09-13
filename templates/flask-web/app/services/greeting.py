def greeting(name: str = "__PROJECT_NAME__") -> str:
    """Pure function; testable without Flask."""
    return f"{name} is running."
