import time
from dataclasses import dataclass


@dataclass
class DownloadProgress:
    asset_name: str
    total_bytes: int
    downloaded_bytes: int
    chunk_name: str
    timestamp: float = 0.0

    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()

    @property
    def percentage(self) -> float:
        if self.total_bytes == 0:
            return 100.0
        return (self.downloaded_bytes / self.total_bytes) * 100.0
