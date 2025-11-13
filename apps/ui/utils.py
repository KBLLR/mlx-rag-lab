"""Utility functions for UI components."""


def truncate_source_path(path: str, max_len: int = 50) -> str:
    """Smart path truncation keeping important parts.

    Args:
        path: The file path to truncate
        max_len: Maximum length of the output string

    Returns:
        Truncated path string

    Examples:
        >>> truncate_source_path("/very/long/path/to/important/file.txt", 30)
        "/very/l.../file.txt"
    """
    if len(path) <= max_len:
        return path

    parts = path.split("/")
    filename = parts[-1]

    # If filename itself is too long, truncate it
    if len(filename) > max_len - 10:
        return f".../{filename[: max_len - 13]}..."

    # Otherwise, truncate the directory path
    remaining = max_len - len(filename) - 4  # Account for ".../" and filename
    prefix = path[: remaining // 2]
    return f"{prefix}.../{filename}"


def get_confidence_color(score: float) -> str:
    """Get Rich color string based on confidence score.

    Args:
        score: Confidence score between 0.0 and 1.0

    Returns:
        Rich color string (e.g., "bold green", "yellow", "red")
    """
    if score >= 0.7:
        return "confidence.high"
    elif score >= 0.4:
        return "confidence.medium"
    else:
        return "confidence.low"


def format_percentage(value: float) -> str:
    """Format a float as a percentage string.

    Args:
        value: Float value between 0.0 and 1.0

    Returns:
        Formatted percentage string (e.g., "75.3%")
    """
    return f"{value * 100:.1f}%"


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human-readable string.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string (e.g., "2m 30s", "45s")
    """
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"
