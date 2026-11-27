from collections.abc import Sequence
from enum import Enum, StrEnum
from typing import Self

from pydantic import Field

from .basemodel import ValidateBaseModel


class AppCategory(StrEnum):
    APPLICATION = "application"
    GAME = "game"

class DeviceType(Enum):
    KEYBOARD = ("keyboard", 24, 8)
    MOUSE = ("mouse", 7, 9)
    MOUSEPAD = ("mousepad", 20, 1)
    HEADSET = ("headset", 5, 1)
    KEYPAD = ("keypad", 5, 4)
    CHROMALINK = ("chromalink", 5, 1)

    def __init__(self: Self, endpoint: str, columns: int, rows: int):
        self.endpoint = endpoint
        self.columns = columns
        self.rows = rows

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
