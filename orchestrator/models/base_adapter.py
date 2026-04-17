"""
Base adapter interface for all model adapters.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseAdapter(ABC):
    """Base class for all model adapters."""

    @abstractmethod
    def generate_response(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate a response for the given task."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Check if the model is available."""
        pass