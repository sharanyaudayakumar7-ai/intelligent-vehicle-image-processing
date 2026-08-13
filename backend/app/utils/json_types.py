"""Convert analysis output to values accepted by PostgreSQL JSON/JSONB."""

from __future__ import annotations

from typing import Any

import numpy as np


def to_json_compatible(value: Any) -> Any:
    """Recursively replace NumPy scalar/array values with native JSON types.

    This intentionally preserves the shape and values of detector output instead
    of serialising it to a string.
    """
    if isinstance(value, np.ndarray):
        return [to_json_compatible(item) for item in value.tolist()]
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    if isinstance(value, dict):
        return {str(key): to_json_compatible(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_json_compatible(item) for item in value]
    return value
