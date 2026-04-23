from __future__ import annotations


def format_duration_short(total_seconds: int) -> str:
    """Render a compact duration string (e.g., 45s, 12min, 1h 05min)."""
    seconds = max(0, int(total_seconds))
    if seconds < 60:
        return f"{seconds}s"
    if seconds < 3600:
        return f"{seconds // 60}min"
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return f"{hours}h {minutes:02d}min"
