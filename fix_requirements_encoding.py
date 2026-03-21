"""Normalize requirements.txt to UTF-8 without null bytes."""

from __future__ import annotations

import pathlib


def normalize_requirements_file(path: str | pathlib.Path = "requirements.txt") -> bool:
    target = pathlib.Path(path)
    if not target.exists():
        return False

    raw = target.read_bytes()
    cleaned = raw

    if b"\x00" in raw:
        try:
            cleaned = raw.decode("utf-16").encode("utf-8")
        except UnicodeDecodeError:
            cleaned = raw.replace(b"\x00", b"")

    if cleaned != raw:
        target.write_bytes(cleaned)
        return True

    return False


if __name__ == "__main__":
    changed = normalize_requirements_file()
    if changed:
        print("Fixed requirements.txt encoding and rewrote it as UTF-8")
    else:
        print("requirements.txt encoding is already clean")
