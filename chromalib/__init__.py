import logging

from .app import ChromaApp
from .colors import Color
from .configurations import (
    AppCategory,
    AppConfiguration,
    AuthorConfiguration,
    DeviceType,
)
from .default_effects import (
    WaveDirection,
    WaveLineOrientation,
    WaveMode,
    create_explosion_colors,
    create_wave_colors,
    generate_decay_updater,
    generate_explosion_updater,
    generate_wave_updater,
)
from .effects import (
    ChromaLinkEffect,
    Effect,
    EffectMethod,
    HeadsetEffect,
    KeyboardEffect,
    KeypadEffect,
    MouseEffect,
    MousepadEffect,
)
from .exceptions import InitializedError, UninitializedError

logging.getLogger(__name__).addHandler(logging.NullHandler())

__all__ = [
    "AppCategory",
    "AppConfiguration",
    "AuthorConfiguration",
    "ChromaApp",
    "ChromaLinkEffect",
    "Color",
    "DeviceType",
    "Effect",
    "EffectMethod",
    "HeadsetEffect",
    "InitializedError",
    "KeyboardEffect",
    "KeypadEffect",
    "MouseEffect",
    "MousepadEffect",
    "UninitializedError",
    "WaveDirection",
    "WaveLineOrientation",
    "WaveMode",
    "create_explosion_colors",
    "create_wave_colors",
    "generate_decay_updater",
    "generate_explosion_updater",
    "generate_wave_updater",
]
