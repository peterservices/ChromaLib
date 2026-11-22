import asyncio
from collections.abc import Callable
from enum import Enum
from typing import Self

from pydantic import (
    Field,
    NonNegativeFloat,
    NonNegativeInt,
    PositiveFloat,
    PositiveInt,
    PrivateAttr,
    model_validator,
)

from .basemodel import ValidateBaseModel
from .colors import Color
from .configurations import DeviceType


def device_type_dict() -> dict[DeviceType, list]:
    """
    Return a dict with the values of `DeviceType` as keys.
    """
    return {key: [] for key in list(DeviceType)}

class EffectMethod(Enum):
    """
    Method of combining with lower hierarchy effects.
    """
    ADD = 1
    ADD_NON_ZERO = 2
    SUBTRACT = 3
    MULTIPLY = 4
    DIVIDE = 5
    FILL = 6
    FILL_NON_ZERO = 7
    FILL_ZERO = 8

class Effect(ValidateBaseModel):
    """
    BaseModel for effects.
    """
    colors: list[list[Color]]
    method: EffectMethod
    expires_after_updates: NonNegativeInt | None = None
    id: str | None = None
    update: Callable[[list[list[Color]]], list[list[Color]]] | None = None
    update_rate_seconds: PositiveFloat | None = None

    _colors_rows: PositiveInt
    _colors_columns: PositiveInt
    _device_type: DeviceType
    _last_update_time: NonNegativeFloat = 0

    @model_validator(mode="after")
    def validate_colors_dimensions(self: Self) -> Self:
        if len(self.colors) != self._colors_rows:
            raise ValueError(f"Expected outer list to have a length of {self._colors_rows}, got {len(self.colors)}")
        for inner_list in self.colors:
            if len(inner_list) != self._colors_columns:
                raise ValueError(f"Expected inner lists to have a length of {self._colors_columns}, got {len(inner_list)}")
        return self

    @model_validator(mode="after")
    def validate_update_fields(self: Self) -> Self:
        if self.update_rate_seconds is None and (self.update is not None or self.expires_after_updates is not None):
            raise ValueError("update_rate must be specified if update or expires_after_updates is specified.")
        return self

class KeyboardEffect(Effect):
    """
    Keyboard effect.

    colors: 8 x 24 list
    """
    _colors_rows = 8
    _colors_columns = 24
    _device_type = DeviceType.KEYBOARD

class MouseEffect(Effect):
    """
    Mouse effect.

    colors: 9 x 7 list
    """
    _colors_rows = 9
    _colors_columns = 7
    _device_type = DeviceType.MOUSE

class MousepadEffect(Effect):
    """
    Mousepad effect.

    colors: 1 x 20 list
    """
    _colors_rows = 1
    _colors_columns = 20
    _device_type = DeviceType.MOUSEPAD

class HeadsetEffect(Effect):
    """
    Headset effect.

    colors: 1 x 5 list
    """
    _colors_rows = 1
    _colors_columns = 5
    _device_type = DeviceType.HEADSET

class KeypadEffect(Effect):
    """
    Keypad effect.

    colors: 4 x 5 list
    """
    _colors_rows = 4
    _colors_columns = 5
    _device_type = DeviceType.KEYPAD

class ChromaLinkEffect(Effect):
    """
    Chroma Link effect.

    colors: 1 x 5 list
    """
    _colors_rows = 1
    _colors_columns = 5
    _device_type = DeviceType.CHROMALINK

class EffectState(ValidateBaseModel):
    """
    A state object that tracks a list of effects and whether the list has changed since last update.
    """
    effects: dict[DeviceType, list[Effect]] = Field(default_factory=device_type_dict)

    _effects_changed: asyncio.Event = PrivateAttr(default_factory=asyncio.Event)
