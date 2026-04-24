"""Custom exceptions for Sophon library."""


class SophonException(Exception):
    """Base exception for Sophon library."""

    pass


class ManifestNotFoundError(SophonException):
    """Raised when manifest cannot be found or fetched."""

    pass


class ChunkVerificationError(SophonException):
    """Raised when chunk verification (hash check) fails."""

    pass


class DownloadError(SophonException):
    """Raised when download operation fails."""

    pass


class PatchError(SophonException):
    """Raised when patch operation fails."""

    pass


class InvalidManifestError(SophonException):
    """Raised when manifest format is invalid."""

    pass
