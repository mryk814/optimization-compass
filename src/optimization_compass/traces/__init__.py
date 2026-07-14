"""Deterministic educational optimization trace generators and utilities."""

from optimization_compass.traces.base import downsample_frames, synchronize_bundle

__all__ = ["downsample_frames", "synchronize_bundle"]
from .generators import (
    generate_gradient_bundle,
    generate_gradient_trace,
    generate_nelder_mead_trace,
)

__all__ = ["generate_gradient_bundle", "generate_gradient_trace", "generate_nelder_mead_trace"]
