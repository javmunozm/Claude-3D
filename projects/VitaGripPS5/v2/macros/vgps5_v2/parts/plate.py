"""Simplified floor plate between the grip ends (right half, x >= 0). No window or camera hole in the spike."""
from ..shapes import box


def build_plate_half(x1, y0, y1, z0, z1):
    return box(0.0, x1, y0, y1, z0, z1)
