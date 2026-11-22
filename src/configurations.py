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
    name: str
    contact: str

class AppConfiguration(ValidateBaseModel):
    title: str
    description: str
    author: AuthorConfiguration
    supported_devices: list[DeviceType]
    category: AppCategory
    effect_id_hierarchy: list[str] = Field(default_factory=list)
