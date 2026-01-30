"""Utility helpers for comfy_api_simplified.

Keep small, well-tested, filesystem- and platform-friendly helpers here.
"""
from pathlib import PurePath
import hashlib
import re
from typing import Union

__all__ = ["make_safe_filename"]


def make_safe_filename(name: Union[str, bytes], suffix: str = ".png", max_base_len: int = 180) -> str:
    """Turn an arbitrary name (may contain path separators) into a filesystem-safe filename.

    Behavior:
    - Preserve path components by joining them with '__' instead of dropping directories.
    - Replace characters not in [A-Za-z0-9._-] with '_'.
    - Collapse repeated '_' inside components and trim leading/trailing '_'.
    - Append an 8-char hash of the original name to avoid collisions while keeping readable info.
    - Ensure the base (before suffix) doesn't exceed max_base_len; if it does, truncate and keep the hash.

    Accepts str or bytes; bytes will be decoded as utf-8 with errors replaced.
    """
    if isinstance(name, bytes):
        name = name.decode("utf-8", errors="replace")
    elif not isinstance(name, str):
        name = str(name)

    # Split path into parts in a platform-agnostic way without touching the filesystem
    parts = PurePath(name).parts
    if not parts:
        parts = (name,)

    # Sanitize each part individually so we can join with '__' and preserve separators
    sanitized_parts = []
    for part in parts:
        p = re.sub(r"[^A-Za-z0-9._-]+", "_", part)
        p = re.sub(r"_+", "_", p).strip("_")
        if not p:
            p = "_"
        sanitized_parts.append(p)

    joined = "__".join(sanitized_parts)

    # Short hash for uniqueness
    h = hashlib.sha256(name.encode("utf-8")).hexdigest()[:8]

    # Ensure we keep some readable info + the hash
    base = f"{joined}__{h}"
    if len(base) > max_base_len:
        # Truncate joined part but keep hash
        keep = max_base_len - (len(h) + 2)  # 2 for the '__'
        if keep <= 0:
            base = h
        else:
            base = f"{joined[:keep]}__{h}"

    return f"{base}{suffix}"
