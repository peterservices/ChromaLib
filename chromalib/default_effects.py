from collections.abc import Callable
from copy import deepcopy
from enum import Enum

from .colors import Color


class WaveDirection(Enum):
    UP = 1
    DOWN = 2
    LEFT = 3
    RIGHT = 4

class WaveLineOrientation(Enum):
    VERTICAL = 1
    HORIZONTAL = 2

class WaveMode(Enum):
    ALTERNATING = 1
    CLUSTER = 2

def create_explosion_colors(color: Color) -> list[list[Color]]:
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

def create_wave_colors(colors: list[Color], line_orientation: WaveLineOrientation, mode: WaveMode) -> list[list[Color]]:
    """
    Create a matrix of colors to be used for a wave effect using the supplied colors.

    Args:
        colors: List of colors to be used to create the colors.
        line_orientation:
            `WaveMode.VERTICAL`: Max 24 colors.
            `WaveMode.HORIZONTAL`: Max 8 colors.
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

def generate_decay_updater(decay: Color) -> Callable[[list[list[Color]]], list[list[Color]]]:
    """
    Return a function that decreases a Color's values by a Color `decay`.
    """
    decay = decay.model_copy()
    def _decay(colors: list[list[Color]]) -> list[list[Color]]:
        for row in colors:
            for color in row:
                color.red -= decay.red
                color.green -= decay.green
                color.blue -= decay.blue
        return colors
    return _decay

def generate_explosion_updater() -> Callable[[list[list[Color]]], list[list[Color]]]:
    """
    Return a function that updates an explosion effect.
    """
    def _explosion(colors: list[list[Color]]) -> list[list[Color]]:
        # Expand left half
        for i in range(3, 5):
            explosion_color = colors[i][11]
            index = colors[i].index(explosion_color, 0, 12)
            if index != 0:
                colors[i][index - 1] = explosion_color.model_copy()

            if i == 3:
                first = 2
                second = 1
                third = 0
            else:
                first = 5
                second = 6
                third = 7
            try:
                index = colors[first].index(explosion_color, 0, 12)
                if index != 0:
                    colors[first][index - 1] = explosion_color.model_copy()

                try:
                    index = colors[second].index(explosion_color, 0, 12)
                    if index != 0:
                        colors[second][index - 1] = explosion_color.model_copy()

                    try:
                        index = colors[third].index(explosion_color, 0, 12)
                        if index != 0:
                            colors[third][index - 1] = explosion_color.model_copy()
                    except ValueError:
                        colors[third][11] = explosion_color.model_copy()
                except ValueError:
                    colors[second][11] = explosion_color.model_copy()
            except ValueError:
                colors[first][11] = explosion_color.model_copy()

        # Expand right half
        for i in range(3, 5):
            explosion_color = colors[i][12]
            index = 23 - colors[i][::-1].index(explosion_color, 0, 12)
            if index != 23:
                colors[i][index + 1] = explosion_color.model_copy()

            if i == 3:
                first = 2
                second = 1
                third = 0
            else:
                first = 5
                second = 6
                third = 7
            try:
                index = 23 - colors[first][::-1].index(explosion_color, 0, 12)
                if index != 23:
                    colors[first][index + 1] = explosion_color.model_copy()

                try:
                    index = 23 - colors[second][::-1].index(explosion_color, 0, 12)
                    if index != 23:
                        colors[second][index + 1] = explosion_color.model_copy()

                    try:
                        index = 23 - colors[third][::-1].index(explosion_color, 0, 12)
                        if index != 23:
                            colors[third][index + 1] = explosion_color.model_copy()
                    except ValueError:
                        colors[third][12] = explosion_color.model_copy()
                except ValueError:
                    colors[second][12] = explosion_color.model_copy()
            except ValueError:
                colors[first][12] = explosion_color.model_copy()
        return colors
    return _explosion

def generate_wave_updater(direction: WaveDirection) -> Callable[[list[list[Color]]], list[list[Color]]]:
    """
    Return a function that updates a wave effect in an direction `WaveDirection`.
    """
    def _wave(colors: list[list[Color]]) -> list[list[Color]]:
        match direction:
            case WaveDirection.UP:
                first = colors.pop(0)
                colors.append(first)
            case WaveDirection.RIGHT:
                for _, v in enumerate(colors):
                    last = v.pop()
                    v.insert(0, last)
            case WaveDirection.DOWN:
                last = colors.pop()
                colors.insert(0, last)
            case WaveDirection.LEFT:
                for _, v in enumerate(colors):
                    first = v.pop(0)
                    v.append(first)
        return colors
    return _wave

