"""Download speed limiter for Sophon."""

from typing import Optional, Callable, Any
import asyncio


class SophonDownloadSpeedLimiter:
    """Limiter for controlling download speed."""

    _add_bytes_or_wait_delegate: Optional[
        Callable[[int, int, asyncio.CancelledError], Any]
    ] = None

    def __init__(self, context: int):
        """
        Initialize speed limiter with a context.

        Args:
            context: Context value for the speed limiter.
        """
        self.context = context

    @classmethod
    def create_instance(cls, service_context: int) -> "SophonDownloadSpeedLimiter":
        """
        Create an instance with the given service context.

        Args:
            service_context: The service context to use.

        Returns:
            A new SophonDownloadSpeedLimiter instance.
        """
        return cls(service_context)

    @classmethod
    def set_add_bytes_or_wait_delegate(
        cls,
        delegate: Optional[Callable[[int, int, asyncio.CancelledError], Any]],
    ) -> None:
        """
        Set the delegate for adding bytes or waiting.

        Args:
            delegate: The delegate function to set.
        """
        cls._add_bytes_or_wait_delegate = delegate

    async def add_bytes_or_wait_async(
        self, read_bytes: int, token: asyncio.CancelledError
    ) -> None:
        """
        Add bytes or wait based on speed limit.

        Args:
            read_bytes: Number of bytes read.
            token: Cancellation token.
        """
        if self._add_bytes_or_wait_delegate is not None:
            await self._add_bytes_or_wait_delegate(self.context, read_bytes, token)
