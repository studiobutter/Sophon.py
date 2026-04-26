"""Extension utilities for Sophon library."""

import hashlib

import xxhash


def hex_to_bytes(hex_string: str) -> bytes:
    """
    Convert hex string to bytes.

    Args:
        hex_string: Hex string to convert.

    Returns:
        Bytes representation of hex string.
    """
    return bytes.fromhex(hex_string)


def bytes_to_hex(data: bytes) -> str:
    """
    Convert bytes to hex string.

    Args:
        data: Bytes to convert.

    Returns:
        Hex string representation.
    """
    return data.hex()


def calculate_md5(data: bytes) -> str:
    """
    Calculate MD5 hash of data.

    Args:
        data: Data to hash.

    Returns:
        Hex string of MD5 hash.
    """
    return hashlib.md5(data).hexdigest()


def calculate_xxh64(data: bytes) -> str:
    """
    Calculate XXH64 hash of data.

    Args:
        data: Data to hash.

    Returns:
        Hex string of XXH64 hash.
    """
    return xxhash.xxh64(data).hexdigest()


def format_bytes(num_bytes: int) -> str:
    """
    Format bytes to human-readable string.

    Args:
        num_bytes: Number of bytes.

    Returns:
        Human-readable size string.
    """
    size_suffixes = ["B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]
    size = float(num_bytes)

    for suffix in size_suffixes:
        if size < 1024.0:
            return f"{size:.2f} {suffix}"
        size /= 1024.0

    return f"{size:.2f} YB"
