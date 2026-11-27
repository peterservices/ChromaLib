from collections.abc import Callable
from copy import deepcopy
from enum import Enum

from .colors import Color
from .configurations import DeviceType


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

def create_explosion_colors(device: DeviceType, color: Color) -> list[list[Color]]:
    """
    Create a matrix of float colors to be used for an explosion effect using the supplied color.

    Args:
        device: The device type the colors will be created for.

        color: The color of the explosion.

    Returns:
        The generated matrix of explosion colors.
    """
    columns = device.columns
    rows = device.rows
    if columns == 1 or rows == 1:
        raise ValueError(f"Expected the effect to be sized at least 2x2, got {columns}x{rows}")
    if columns % 2 != 0 or rows % 2 != 0:
        raise ValueError(f"Expected the number of columns and rows to be even, got {columns}x{rows}")

    # Make a blank background
    pattern = [[Color() for _ in range(columns)] for _ in range(rows)]

    top_index = int(rows / 2) - 1
    left_index = int(columns / 2) - 1
    colors = color.RGB_float

    # Create a 2x2 colored square in the center of the matrix
    pattern[top_index][left_index].RGB_float = colors
    pattern[top_index][left_index + 1].RGB_float = colors
    pattern[top_index + 1][left_index].RGB_float = colors
    pattern[top_index + 1][left_index + 1].RGB_float = colors

    return pattern

def create_static_colors(device: DeviceType, color: Color) -> list[list[Color]]:
    """
    Create a matrix of the same color.

    Args:
        device: The device type the colors will be created for.

        color: The static color.

    Returns:
        The generated matrix of static colors.
    """
    return [[color.model_copy() for _ in range(device.columns)] for _ in range(device.rows)]

def create_wave_colors(device: DeviceType, colors: list[Color], line_orientation: WaveLineOrientation, mode: WaveMode) -> list[list[Color]]:
    """
    Create a matrix of colors to be used for a wave effect using the supplied colors.

    Args:
        device: The device type the colors will be created for.

        colors: List of colors of the waves.

        line_orientation:
            `WaveLineOrientation.VERTICAL`: Number of effect columns limits colors length.
            `WaveLineOrientation.HORIZONTAL`: Number of effect rows limits colors length.

        mode:
            `WaveMode.ALTERNATING`: Colors repeat seperated in the given order. (Looks best when the number of colors is a factor of the number of columns.)
            `WaveMode.CLUSTER`: Colors expand to fill the space without repeating seperately.

    Returns:
        The generated matrix of wave colors.
    """
    columns = device.columns
    rows = device.rows
    if len(colors) < 2:
        raise ValueError(f"Expected `colors` to have a length no less than 2, got {len(colors)}")
    if line_orientation == WaveLineOrientation.VERTICAL and len(colors) > columns:
        raise ValueError(f"Expected `colors` to have a length no greater than {columns}, got {len(colors)}")
    if line_orientation == WaveLineOrientation.HORIZONTAL and len(colors) > rows:
        raise ValueError(f"Expected `colors` to have a length no greater than {rows}, got {len(colors)}")
    if columns == 1 and rows == 1:
        raise ValueError(f"Expected the effect to be sized at least 2x1 or 1x2, got {columns}x{rows}")

    match line_orientation:
        case WaveLineOrientation.VERTICAL:
            row_pattern = colors.copy()
            color = 0
            match mode:
                case WaveMode.ALTERNATING:
                    while len(row_pattern) < columns:
                        row_pattern.append(colors[color].model_copy())
                        color += 1
                        if color >= len(colors):
                            color = 0
                case WaveMode.CLUSTER:
                    while len(row_pattern) < columns:
                        index = row_pattern.index(colors[color])
                        row_pattern.insert(index, colors[color].model_copy())
                        color += 1
                        if color >= len(colors):
                            color = 0
            pattern = [deepcopy(row_pattern) for _ in range(rows)] # Ensure every Color object in the pattern is unique
        case WaveLineOrientation.HORIZONTAL:
            column_pattern = colors.copy()
            color = 0
            match mode:
                case WaveMode.ALTERNATING:
                    while len(column_pattern) < rows:
                        column_pattern.append(colors[color].model_copy())
                        color += 1
                        if color >= len(colors):
                            color = 0
                case WaveMode.CLUSTER:
                    while len(column_pattern) < rows:
                        index = column_pattern.index(colors[color].model_copy())
                        column_pattern.insert(index, colors[color])
                        color += 1
                        if color >= len(colors):
                            color = 0
            pattern = [[color.model_copy() for _ in range(columns)] for color in column_pattern] # Ensure every Color object in the pattern is unique
    return pattern

def generate_decay_updater(decay: Color) -> Callable[[list[list[Color]]], list[list[Color]]]:
    """
    Return a function that decreases an effect's colors' values by a Color `decay`.
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
    Return a function that updates an explosion effect's colors.
    """
    def _explosion(colors: list[list[Color]]) -> list[list[Color]]:
        columns = len(colors[0])
        rows = len(colors)

        if columns == 1 or rows == 1:
            raise ValueError(f"Expected the effect to be sized at least 2x2, got {columns}x{rows}")
        if columns % 2 != 0 or rows % 2 != 0:
            raise ValueError(f"Expected the number of columns and rows to be even, got {columns}x{rows}")

        half_columns = int(columns / 2)
        half_rows = int(rows / 2)
        top_index = half_rows - 1
        left_index = half_columns - 1

        # Expand left half
        for i in range(top_index, top_index + 2):
            explosion_color = colors[i][left_index]
            index = colors[i].index(explosion_color, 0, half_columns)
            if index != 0:
                colors[i][index - 1] = explosion_color.model_copy()

            if i == top_index:
                row_indices = list(range(top_index - 1, -1, -1))
            else:
                row_indices = list(range(half_rows + 1, rows))

            for row_index in row_indices:
                try:
                    index = colors[row_index].index(explosion_color, 0, half_columns)
                    if index != 0:
                        colors[row_index][index - 1] = explosion_color.model_copy()
                except ValueError:
                    colors[row_index][left_index] = explosion_color.model_copy()
                    break

        # Expand right half
        for i in range(top_index, top_index + 2):
            explosion_color = colors[i][12]
            index = (columns - 1) - colors[i][::-1].index(explosion_color, 0, half_columns)
            if index != columns - 1:
                colors[i][index + 1] = explosion_color.model_copy()

            if i == top_index:
                row_indices = list(range(top_index - 1, -1, -1))
            else:
                row_indices = list(range(half_rows + 1, rows))

            for row_index in row_indices:
                try:
                    index = (columns - 1) - colors[row_index][::-1].index(explosion_color, 0, half_columns)
                    if index != columns - 1:
                        colors[row_index][index + 1] = explosion_color.model_copy()
                except ValueError:
                    colors[row_index][half_columns] = explosion_color.model_copy()
                    break
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
