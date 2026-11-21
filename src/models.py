# IMPORTS
from collections.abc import Callable
from enum import Enum
from threading import Lock
from typing import Any, Self

from pydantic import (
    Field,
    NonNegativeFloat,
    NonNegativeInt,
    PositiveFloat,
    PrivateAttr,
    field_validator,
    model_validator,
)

from basemodel import ValidateBaseModel
from configuration import DeviceType


class Color(ValidateBaseModel):
    """
    An RGB float color with added support for RGB integer and BGR decimal colors.

    Please note that float color values are clamped between 0 and 1.
    """
    red: float = 0.0
    green: float = 0.0
    blue: float = 0.0

    def __add__(self: Self, other: "Color") -> "Color":
        try:
            return Color(red=self.red + other.red, green=self.green + other.green, blue=self.blue + other.blue)
        except AttributeError:
            raise NotImplementedError from None

    def __sub__(self: Self, other: "Color") -> "Color":
        try:
            return Color(red=self.red - other.red, green=self.green - other.green, blue=self.blue - other.blue)
        except AttributeError:
            raise NotImplementedError from None

    def __mul__(self: Self, other: "Color") -> "Color":
        try:
            return Color(red=self.red * other.red, green=self.green * other.green, blue=self.blue * other.blue)
        except AttributeError:
            raise NotImplementedError from None

    def __rmul__(self: Self, other: "Color") -> "Color":
        return self.__mul__(other)

    def __truediv__(self: Self, other: "Color") -> "Color":
        try:
            return Color(red=self.red / other.red, green=self.green / other.green, blue=self.blue / other.blue)
        except AttributeError:
            raise NotImplementedError from None

    @property
    def RGB_int(self: Self) -> tuple[int, int, int]:
        """
        The color as RGB integers between 0 and 255.
        """
        return (round(self.red * 255), round(self.green * 255), round(self.blue * 255))

    @property
    def RGB_float(self: Self) -> tuple[float, float, float]:
        """
        The color as RGB floats between 0 and 1.
        """
        return (self.red, self.green, self.blue)

    @property
    def BGR_decimal(self: Self) -> int:
        """
        The color as a BGR decimal between 0 and 16777215.
        """
        int_color = self.RGB_int
        return int_color[2] * 256 ** 2 + int_color[1] * 256 + int_color[0]

    @RGB_int.setter
    def RGB_int(self: Self, values: tuple[int, int, int]) -> None:
        self.red = values[0] / 255
        self.green = values[1] / 255
        self.blue = values[2] / 255

    @RGB_float.setter
    def RGB_float(self: Self, values: tuple[float, float, float]) -> None:
        self.red = values[0]
        self.green = values[1]
        self.blue = values[2]

    @BGR_decimal.setter
    def BGR_decimal(self: Self, value: int) -> None:
        self.RGB_int = (value % 256, (value // 256) % 256, (value // 256 ** 2) % 256)

    @field_validator("red", "blue", "green", mode="after")
    @classmethod
    def validate_colors(cls, value: float) -> float:
        return max(0.0, min(value, 1.0)) # Clamp color values between 0 and 1

class EffectMethod(Enum):
    ADD = 1
    ADD_NON_ZERO = 2
    SUBTRACT = 3
    MULTIPLY = 4
    FILL = 5
    FILL_NON_ZERO = 6
    FILL_ZERO = 7

class EffectDirection(Enum):
    UP = 1
    DOWN = 2
    LEFT = 3
    RIGHT = 4

class Effect(ValidateBaseModel):
    """
    Base effect.
    """
    method: EffectMethod
    colors: list[list[Color]]
    update_rate: PositiveFloat | None = None
    update: Callable[[list[list[Color]]], list[list[Color]]] | None = None
    _last_update_time: NonNegativeFloat = 0
    expires_after_updates: NonNegativeInt | None = None
    id: str | None = None

    @model_validator(mode="after")
    def validate_update_fields(self: Self) -> Self:
        if self.update_rate is None and self.update is not None:
            raise ValueError("update_rate must be specified if update is specified.")
        return self

class KeyboardEffect(Effect):
    """
    Keyboard effect.

    colors: 8 x 24 list
    """
    direction: EffectDirection | None = None

    @field_validator("colors", mode="after")
    @classmethod
    def validate_colors_dimensions(cls, value: list[list[Color]]) -> list[list[Color]]:
        if len(value) != 8:
            raise ValueError(f"Expected outer list to have a length of 8, got {len(value)}")
        for inner_list in value:
            if len(inner_list) != 24:
                raise ValueError(f"Expected inner list to have a length of 24, got {len(inner_list)}")

        return value

class MouseEffect(Effect):
    """
    Mouse effect.

    colors: 9 x 7 list
    """
    @field_validator("colors", mode="after")
    @classmethod
    def validate_colors_dimensions(cls, value: list[list[Color]]) -> list[list[Color]]:
        if len(value) != 1:
            raise ValueError(f"Expected outer list to have a length of 9, got {len(value)}")
        for inner_list in value:
            if len(inner_list) != 1:
                raise ValueError(f"Expected inner list to have a length of 7, got {len(inner_list)}")

        return value

class MousepadEffect(Effect):
    """
    Mousepad effect.

    colors: 1 x 20 list
    """
    @field_validator("colors", mode="after")
    @classmethod
    def validate_colors_dimensions(cls, value: list[list[Color]]) -> list[list[Color]]:
        if len(value) != 1:
            raise ValueError(f"Expected outer list to have a length of 1, got {len(value)}")
        for inner_list in value:
            if len(inner_list) != 1:
                raise ValueError(f"Expected inner list to have a length of 20, got {len(inner_list)}")

        return value

class HeadsetEffect(Effect):
    """
    Headset effect.

    colors: 1 x 5 list
    """
    @field_validator("colors", mode="after")
    @classmethod
    def validate_colors_dimensions(cls, value: list[list[Color]]) -> list[list[Color]]:
        if len(value) != 1:
            raise ValueError(f"Expected outer list to have a length of 1, got {len(value)}")
        for inner_list in value:
            if len(inner_list) != 1:
                raise ValueError(f"Expected inner list to have a length of 5, got {len(inner_list)}")

        return value

class KeypadEffect(Effect):
    """
    Keypad effect.

    colors: 4 x 5 list
    """
    @field_validator("colors", mode="after")
    @classmethod
    def validate_colors_dimensions(cls, value: list[list[Color]]) -> list[list[Color]]:
        if len(value) != 1:
            raise ValueError(f"Expected outer list to have a length of 4, got {len(value)}")
        for inner_list in value:
            if len(inner_list) != 1:
                raise ValueError(f"Expected inner list to have a length of 5, got {len(inner_list)}")

        return value

class ChromaLinkEffect(Effect):
    """
    Chroma Link effect.

    colors: 1 x 5 list
    """
    @field_validator("colors", mode="after")
    @classmethod
    def validate_colors_dimensions(cls, value: list[list[Color]]) -> list[list[Color]]:
        if len(value) != 1:
            raise ValueError(f"Expected outer list to have a length of 1, got {len(value)}")
        for inner_list in value:
            if len(inner_list) != 1:
                raise ValueError(f"Expected inner list to have a length of 5, got {len(inner_list)}")

        return value

def device_type_dict() -> dict[DeviceType, Any]:
    return dict.fromkeys(list(DeviceType))

class State(ValidateBaseModel):
    """
    A model to manage Chroma effects.
    """
    effects: dict[DeviceType, list[Effect]] = Field(default_factory=device_type_dict)

    # Lowest to highest
    effect_id_hierarchy: list[str] = Field(default_factory=list)

    _lock: Lock = PrivateAttr(default_factory=Lock)

    _effects_changed: bool = PrivateAttr(default=False) # TODO: actually set this variable

    # TODO: should we move the functions below to ChromaApp? Do we need a State object (include it in ChromaApp or rename and/or refactor this object)?

    def find_effect_by_id(self: Self, id: str, device: DeviceType) -> Effect | None:
        """
        Find an effect in the specified effects list by its id.

        Args:
            id: The effect id to look for.
            device: The device type of the effect to look for.

        Returns:
            The effect if found or None.
        """
        effects = self.effects[device]

        if isinstance(id, str):
            for effect in effects:
                if effect.id == id:
                    return effect
        return None

    def add_effect(self: Self, effect: Effect) -> None:
        """
        Add an effect to it's device's effects list, respecting `self.effect_id_hierarchy`. If an effect does not have a valid id, it will be treated as highest hierarchy.

        Args:
            effect: The effect to be added.
        """
        effects, device = self.get_effects_list_from_effect_type(effect)

        if effect.id is not None and len(effects) > 0 and effect.id in self.effect_id_hierarchy:
            highest_available_index = 0
            for id in self.effect_id_hierarchy:
                if id == effect.id:
                    effects.insert(highest_available_index, effect)
                    return

                found_effect = self.find_effect_by_id(id, device)
                if found_effect is not None:
                    highest_available_index = effects.index(found_effect) + 1

                    # There is no point in checking the rest of the hierarchy if no other effects are in the list
                    if highest_available_index == len(effects):
                        effects.append(effect)
                        return
        else:
            effects.append(effect)

    def remove_effect(self: Self, effect: Effect) -> None:
        """
        Remove an effect from it's device's effects list.

        Args:
            effect: The effect to be removed.
        """
        effects, _ = self.get_effects_list_from_effect_type(effect)

        if effect in effects:
            effects.remove(effect)

    def remove_effects_by_ids(self: Self, ids: list[str], devices: list[DeviceType]) -> None:
        """
        Remove effects by their ids from the specified effects lists by their ids.

        Args:
            ids: The effect ids to look for.
            devices: The device types of the effects to remove.
        """
        for id in ids:
            for device_type in devices:
                effect = self.find_effect_by_id(id, device_type)
                if effect is not None:
                    self.remove_effect(effect)

    def get_effects_list_from_effect_type(self: Self, effect: Effect) -> tuple[list[Effect], DeviceType]:
        """
        Get the corresponding effects list and device type from the effect type.
        """
        if isinstance(effect, KeyboardEffect):
            device_type = DeviceType.KEYBOARD
        elif isinstance(effect, MouseEffect):
            device_type = DeviceType.MOUSE
        elif isinstance(effect, MousepadEffect):
            device_type = DeviceType.MOUSEPAD
        elif isinstance(effect, HeadsetEffect):
            device_type = DeviceType.HEADSET
        elif isinstance(effect, KeypadEffect):
            device_type = DeviceType.KEYPAD
        elif isinstance(effect, ChromaLinkEffect):
            device_type = DeviceType.CHROMALINK
        else:
            raise TypeError(f"Unimplemented effect type of {type(effect)}.")
        return (self.effects[device_type], device_type)

