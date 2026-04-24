"""Base types and data structures for Sophon library."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class IdentifiableProperty:
    """Base class for identifiable properties with category and matching field."""

    matching_field: Optional[str] = None
    category_id: int = 0
    category_name: Optional[str] = None

    def __hash__(self) -> int:
        """Make the object hashable."""
        return hash((self.matching_field, self.category_id, self.category_name))
