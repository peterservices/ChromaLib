# IMPORTS
from copy import deepcopy
from enum import Enum

from models import Color


class WaveLineOrientation(Enum):
    VERTICAL = 1
    HORIZONTAL = 2

class WaveMode(Enum):
    ALTERNATING = 1
    CLUSTER = 2

def create_wave_colors(colors: list[Color], line_orientation: WaveLineOrientation, mode: WaveMode) -> list[list[Color]]:
    """
    Create a matrix of colors to be used for a wave effect using the supplied colors.

    Args:
        colors: List of colors to be used to create the colors.
        line_orientation:
            `WaveMode.VERTICAL`: Max 24 colors.
            `WaveModeHORIZONTAL`: Max 8 colors.
        mode:
            `WaveMode.ALTERNATING`: Colors repeat seperated. (Looks best when the number of colors is a factor of the number of colors.)
            `WaveMode.CLUSTER`: Colors repeat clumped with themselves.

    Returns:
        The generated matrix of wave colors.
    """
    if len(colors) < 2:
        raise ValueError(f"Expected `colors` to have a length no less than 2, got {len(colors)}")
    if line_orientation == WaveLineOrientation.VERTICAL and len(colors) > 24:
        raise ValueError(f"Expected `colors` to have a length no greater than 24, got {len(colors)}")
    if line_orientation == WaveLineOrientation.HORIZONTAL and len(colors) > 8:
        raise ValueError(f"Expected `colors` to have a length no greater than 8, got {len(colors)}")

    match line_orientation:
        case WaveLineOrientation.VERTICAL:
            row_pattern = colors.copy()
            color = 0
            match mode:
                case WaveMode.ALTERNATING:
                    while len(row_pattern) < 24:
                        row_pattern.append(colors[color].model_copy())
                        color += 1
                        if color >= len(colors):
                            color = 0
                case WaveMode.CLUSTER:
                    while len(row_pattern) < 24:
                        index = row_pattern.index(colors[color])
                        row_pattern.insert(index, colors[color].model_copy())
                        color += 1
                        if color >= len(colors):
                            color = 0
            pattern = [deepcopy(row_pattern) for _ in range(8)] # Ensure every Color object in the pattern is unique
        case WaveLineOrientation.HORIZONTAL:
            column_pattern = colors.copy()
            color = 0
            match mode:
                case WaveMode.ALTERNATING:
                    while len(column_pattern) < 8:
                        column_pattern.append(colors[color].model_copy())
                        color += 1
                        if color >= len(colors):
                            color = 0
                case WaveMode.CLUSTER:
                    while len(column_pattern) < 8:
                        index = column_pattern.index(colors[color].model_copy())
                        column_pattern.insert(index, colors[color])
                        color += 1
                        if color >= len(colors):
                            color = 0
            pattern = [[color.model_copy() for _ in range(24)] for color in column_pattern] # Ensure every Color object in the pattern is unique
    return pattern

def create_explosion_effect(color: Color) -> list[list[Color]]:
    """
    Create a matrix of float colors to be used for an explosion effect using the supplied color in RGB format.

    Args:
        color: The RGB color to be used for the effect.

    Returns:
        The generated explosion effect.
    """
    # Make a blank background
    pattern = [[Color() for _ in range(24)] for _ in range(8)]

    # Create a 2x2 colored square in the center of the matrix
    pattern[3][11] = color.model_copy()
    pattern[3][12] = color.model_copy()
    pattern[4][11] = color.model_copy()
    pattern[4][12] = color.model_copy()

    return pattern
