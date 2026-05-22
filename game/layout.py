"""Shared layout context — scale, viewport, and convenience multiplier."""
from dataclasses import dataclass


@dataclass(frozen=True)
class LayoutContext:
    """Carries scale, viewport, and convenience multiplier for all draw methods."""
    scale: float
    width: int
    height: int
    me: int  # int(scale), convenience
