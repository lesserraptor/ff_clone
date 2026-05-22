"""Abstract base for all scene renderers."""
from abc import ABC, abstractmethod


class SceneRenderer(ABC):
    """All scene renderers must implement this."""
    @abstractmethod
    def draw(self, model, scale: float, width: int, height: int, **kwargs):
        ...
