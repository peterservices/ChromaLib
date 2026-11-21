# IMPORTS
import asyncio
import json
import logging
import threading
import time
from copy import deepcopy
from typing import Any, Self

import websockets

from configuration import AppConfiguration, DeviceType
from models import Color, EffectMethod, State

logger = logging.getLogger(__name__)

class ChromaApp:
    """
    An application to control Razer Chroma enabled devices.
    """
    websocket_uri = "ws://localhost:13337/razer/chromasdk"

    def __init__(self: Self, config: AppConfiguration) -> None:
        self.config = config
        self.started_event = threading.Event()

        self._state: State = State()
        self._websocket: websockets.ClientConnection | None = None
        self._effect_update_thread = threading.Thread(target=self._update_effects, daemon=True)
        self._effect_update_thread.start()

    async def start(self: Self) -> None:
        """
        Intialize the Razer Chroma App.
        """
        self._websocket = await websockets.connect(self.websocket_uri)
        await self._send({
            "title": self.config.title,
            "description": self.config.description,
            "author": {
                "name": self.config.author.name,
                "contact": self.config.author.contact
            },
            "device_supported": self.config.supported_devices,
            "category": self.config.category
        })

        await asyncio.sleep(2) # Give the Chroma SDK time to intialize the app before resetting device RGB
        for device in self.config.supported_devices:
            await self._send({
                "endpoint": device,
                "effect": "CHROMA_NONE"
            }) # Clear Chroma effects for all active devices

        self.started_event.set()
        self._state._effects_changed = True
        logger.debug(f"Connected to the Razer Chroma SDK ({self.websocket_uri})")

    async def stop(self: Self) -> None:
        """
        Deinitialize the Razer Chroma App.
        """
        self.started_event.clear()
        if self._websocket is not None:
            await self._websocket.close()
            self._websocket = None

            logger.debug(f"Disconnected from the Razer Chroma SDK ({self.websocket_uri})")

    async def _send(self: Self, payload: Any, *, try_reconnect: bool = True) -> bool:
        """
        Send data through the Razer Chroma SDK.

        Args:
            try_reconnect: Whether a reconnection should be attempted if the websocket is closed unexpectedly.

        Returns:
            Whether the payload was sent successfully.
        """
        if self._websocket is not None:
            try:
                await self._websocket.send(json.dumps(payload))
                return True
            except (ConnectionError, websockets.ConnectionClosed):
                if try_reconnect and self.started_event.is_set():
                    await self.stop()
                    await self.start()
                    return await self._send(payload, try_reconnect=False)
        return False

    async def _update_effects(self: Self) -> None:
        """
        Update the devices' color with active effects, and update any effect animations.
        """
        while True:
            for device in self.config.supported_devices:
                effects = self._state.effects[device]
                match device:
                    case DeviceType.KEYBOARD:
                        device_color_columns = 24
                        device_color_rows = 8
                    case DeviceType.MOUSE:
                        device_color_columns = 7
                        device_color_rows = 9
                    case DeviceType.MOUSEPAD:
                        device_color_columns = 20
                        device_color_rows = 1
                    case DeviceType.HEADSET:
                        device_color_columns = 5
                        device_color_rows = 1
                    case DeviceType.KEYPAD:
                        device_color_columns = 5
                        device_color_rows = 4
                    case DeviceType.CHROMALINK:
                        device_color_columns = 4
                        device_color_rows = 1

                expiring_effects = []
                with self._state._lock:
                    for effect in effects:
                        if effect.update_rate is not None and time.time() - effect._last_update_time >= effect.update_rate:
                            if effect.expires_after_updates is not None:
                                if effect.expires_after_updates == 0:
                                    expiring_effects.append(effect)
                                    continue
                                effect.expires_after_updates -= 1
                            if effect.update is not None:
                                effect.update(deepcopy(effect.colors))
                                self._state._effects_changed = True
                            effect._last_update_time = time.time()
                    for effect in expiring_effects:
                        self._state.remove_effect(effect)
                        self._state._effects_changed = True

                    effect_changed = self._state._effects_changed
                    if effect_changed:
                        self._state._effects_changed = False

                    if effect_changed and len(effects) > 0:
                        colors = [[Color() for _ in range(device_color_columns)] for _ in range(device_color_rows)]
                        for effect in effects:
                            match effect.method:
                                case EffectMethod.ADD:
                                    # Add everything
                                    for row, row_v in enumerate(effect.colors):
                                        for column, column_v in enumerate(row_v):
                                            colors[row][column] = colors[row][column] + column_v
                                case EffectMethod.ADD_NON_ZERO:
                                    # Add everything, except to values that are already zeros
                                    for row, row_v in enumerate(effect.colors):
                                        for column, column_v in enumerate(row_v):
                                            if colors[row][column].RGB_float != (0.0, 0.0, 0.0):
                                                colors[row][column] = colors[row][column] + column_v
                                case EffectMethod.SUBTRACT:
                                    # Subtract everything
                                    for row, row_v in enumerate(effect.colors):
                                        for column, column_v in enumerate(row_v):
                                            colors[row][column] = colors[row][column] - column_v
                                case EffectMethod.FILL:
                                    # Fill everything
                                    colors = deepcopy(effect.colors)
                                case EffectMethod.FILL_ZERO:
                                    # Fill only remaining zero values
                                    for row, row_v in enumerate(effect.colors):
                                        for column, column_v in enumerate(row_v):
                                            if colors[row][column].RGB_float == (0.0, 0.0, 0.0):
                                                colors[row][column] = column_v.model_copy()
                                case EffectMethod.FILL_NON_ZERO:
                                    # Fill everything, except with zeros
                                    for row, row_v in enumerate(effect.colors):
                                        for column, column_v in enumerate(row_v):
                                            if column_v.RGB_float != (0.0, 0.0, 0.0):
                                                colors[row][column] = column_v.model_copy()
                                case EffectMethod.MULTIPLY:
                                    # Multiply everything
                                    for row, row_v in enumerate(effect.colors):
                                        for column, column_v in enumerate(row_v):
                                            colors[row][column] = colors[row][column] * column_v
                        # Convert the float colors to decimal colors usable by the Chroma SDK API
                        decimal_colors = [[0 for _ in range(device_color_columns)] for _ in range(device_color_rows)]
                        for row, row_v in enumerate(colors):
                            for column, column_v in enumerate(row_v):
                                decimal_colors[row][column] = column_v.BGR_decimal

                        if self.started_event.is_set(): # Only send data if we are connected
                            if device_color_rows == 1:
                                decimal_colors = decimal_colors[0] # Devices that have one row don't accept 2D lists
                            match device:
                                case DeviceType.KEYBOARD:
                                    await self._send({
                                        "endpoint": device,
                                        "effect": "CHROMA_CUSTOM2",
                                        "param": {
                                           "color": decimal_colors,
                                           "key": [[0 for _ in range(22)] for _ in range(6)] # Make key param all zeros because it's not needed
                                        }
                                    })
                                case DeviceType.MOUSE:
                                    await self._send({
                                        "endpoint": device,
                                        "effect": "CHROMA_CUSTOM2",
                                        "param": decimal_colors
                                    })
                                case _:
                                    await self._send({
                                        "endpoint": device,
                                        "effect": "CHROMA_CUSTOM",
                                        "param": decimal_colors
                                    })
                    elif effect_changed and self.started_event.is_set(): # Only send data if we are connected
                            await self._send({
                                "endpoint": device,
                                "effect": "CHROMA_NONE"
                            })
