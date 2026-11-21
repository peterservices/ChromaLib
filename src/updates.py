from collections.abc import Callable

from models import Color, EffectDirection


def generate_decay_update(decay: Color) -> Callable[[list[list[Color]]], list[list[Color]]]:
    """
    Return a function that decreases a Color's values by a Color `decay`.
    """
    decay = decay.model_copy()
    def _decay(colors: list[list[Color]]) -> list[list[Color]]:
        for row in colors:
            for color in row:
                color.red -= decay.red
                color.green -= decay.green
                color.blue -= color.blue
        return colors
    return _decay

def generate_wave_update(direction: EffectDirection) -> Callable[[list[list[Color]]], list[list[Color]]]:
    """
    Return a function that updates a wave effect in an EffectDirection `direction`.
    """
    def _wave(colors: list[list[Color]]) -> list[list[Color]]:
        match direction:
            case EffectDirection.UP:
                first = colors.pop(0)
                colors.append(first)
            case EffectDirection.RIGHT:
                for _, v in enumerate(colors):
                    last = v.pop()
                    v.insert(0, last)
            case EffectDirection.DOWN:
                last = colors.pop()
                colors.insert(0, last)
            case EffectDirection.LEFT:
                for _, v in enumerate(colors):
                    first = v.pop(0)
                    v.append(first)
        return colors
    return _wave

def generate_explosion_update() -> Callable[[list[list[Color]]], list[list[Color]]]:
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
