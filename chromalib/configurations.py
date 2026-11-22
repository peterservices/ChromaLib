from collections.abc import Sequence
from enum import StrEnum

from pydantic import Field

from .basemodel import ValidateBaseModel


class AppCategory(StrEnum):
    APPLICATION = "application"
    GAME = "game"

class DeviceType(StrEnum):
    KEYBOARD = "keyboard"
    MOUSE = "mouse"
    MOUSEPAD = "mousepad"
    HEADSET = "headset"
    KEYPAD = "keypad"
    CHROMALINK = "chromalink"

class AuthorConfiguration(ValidateBaseModel):
    name: str = Field(max_length=64)
    contact: str = Field(max_length=64)

class AppConfiguration(ValidateBaseModel):
    title: str = Field(max_length=64)
    description: str = Field(max_length=256)
    author: AuthorConfiguration
    supported_devices: Sequence[DeviceType]
    category: AppCategory
    effect_id_hierarchy: Sequence[str] = Field(default_factory=list)
