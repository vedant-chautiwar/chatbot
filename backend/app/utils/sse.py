import json
from typing import Any


def format_sse(event: str, data: Any) -> str:
    """Format Server-Sent Event frame with JSON-encoded data payload."""
    if isinstance(data, (dict, list)):
        payload = json.dumps(data)
    elif isinstance(data, str):
        payload = data
    else:
        payload = json.dumps(data, default=str)

    return f"event: {event}\ndata: {payload}\n\n"
