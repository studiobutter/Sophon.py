"""Download progress tracking and formatting utilities."""

import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ProgressTracker:
    """Track download progress with speed and ETA calculations."""

    total_bytes: int
    current_file: str = ""
    current_file_size: int = 0
    current_file_downloaded: int = 0
    start_time: float = field(default_factory=time.time)
    last_update_time: float = field(default_factory=time.time)
    total_downloaded: int = 0
    smoothed_speed: Optional[float] = None
    speed_alpha: float = 0.3  # Exponential moving average factor

    @property
    def elapsed_seconds(self) -> float:
        """Get elapsed time in seconds."""
        return time.time() - self.start_time

    @property
    def average_speed(self) -> float:
        """Get average download speed in bytes/sec."""
        elapsed = self.elapsed_seconds
        if elapsed > 0:
            return self.total_downloaded / elapsed
        return 0.0

    @property
    def current_speed(self) -> float:
        """Get current smoothed download speed in bytes/sec."""
        return self.smoothed_speed or self.average_speed

    @property
    def percentage(self) -> float:
        """Get completion percentage (0-100)."""
        if self.total_bytes == 0:
            return 100.0
        return (self.total_downloaded / self.total_bytes) * 100.0

    @property
    def estimated_time_remaining(self) -> float:
        """Get estimated time remaining in seconds."""
        speed = self.current_speed
        if speed <= 0:
            return 0.0
        remaining_bytes = self.total_bytes - self.total_downloaded
        return remaining_bytes / speed

    def update(self, bytes_read: int, file_name: str = "", file_size: int = 0) -> None:
        """
        Update progress with new data.

        Args:
            bytes_read: Number of bytes read in this update.
            file_name: Optional current file name being downloaded.
            file_size: Optional total size of current file.
        """
        current_time = time.time()
        time_delta = current_time - self.last_update_time

        self.total_downloaded += bytes_read
        if file_name:
            self.current_file = file_name
        if file_size:
            self.current_file_size = file_size
        self.current_file_downloaded += bytes_read

        # Update smoothed speed (exponential moving average)
        if time_delta > 0:
            current_instant_speed = bytes_read / time_delta
            if self.smoothed_speed is None:
                self.smoothed_speed = current_instant_speed
            else:
                self.smoothed_speed = (
                    self.speed_alpha * current_instant_speed
                    + (1 - self.speed_alpha) * self.smoothed_speed
                )

        self.last_update_time = current_time

    def reset_file(self) -> None:
        """Reset current file progress."""
        self.current_file = ""
        self.current_file_size = 0
        self.current_file_downloaded = 0

    @staticmethod
    def format_bytes(bytes_value: float) -> str:
        """Format bytes as human-readable string."""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if bytes_value < 1024.0:
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.2f} PB"

    @staticmethod
    def format_time(seconds: float) -> str:
        """Format seconds as human-readable time string."""
        if seconds < 0:
            return "N/A"
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"

    def format_progress_bar(self, width: int = 30) -> str:
        """
        Format a progress bar.

        Args:
            width: Width of the progress bar in characters.

        Returns:
            Formatted progress bar string.
        """
        percentage = self.percentage
        filled = int(width * percentage / 100)
        # Use ASCII-safe characters for maximum compatibility
        bar = "=" * filled + "-" * (width - filled)
        return f"[{bar}] {percentage:.1f}%"

    def format_status(self, show_file: bool = True, bar_width: int = 25) -> str:
        """
        Format complete status line.

        Args:
            show_file: Include current file name in status.
            bar_width: Width of progress bar.

        Returns:
            Formatted status string.
        """
        parts = []

        # Progress bar
        parts.append(self.format_progress_bar(bar_width))

        # Downloaded / Total
        downloaded_str = self.format_bytes(self.total_downloaded)
        total_str = self.format_bytes(self.total_bytes)
        parts.append(f"{downloaded_str} / {total_str}")

        # Speed
        speed_str = self.format_bytes(self.current_speed)
        parts.append(f"@ {speed_str}/s")

        # ETA
        eta_str = self.format_time(self.estimated_time_remaining)
        parts.append(f"ETA: {eta_str}")

        # Current file
        if show_file and self.current_file:
            parts.append(f"({self.current_file})")

        return " | ".join(parts)


def create_progress_callback(tracker: ProgressTracker, current_file: str = ""):
    """
    Create a download progress callback for use with SophonAsset.

    Args:
        tracker: ProgressTracker instance to update.
        current_file: Optional current file name.

    Returns:
        Callback function compatible with download_info_delegate.
    """

    def callback(bytes_read: int, net_bytes: int) -> None:
        """Download progress callback."""
        tracker.update(bytes_read, file_name=current_file)
        print(f"\r{tracker.format_status()}", end="", flush=True)

    return callback
