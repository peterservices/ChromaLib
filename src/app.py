import asyncio
import json
import logging
import threading
import time
from contextlib import suppress
from copy import deepcopy
from typing import Any, Self

import websockets

from configurations import AppConfiguration, DeviceType
from effects import EffectMethod
from models import Color, State, device_type_dict

logger = logging.getLogger(__name__)

class ChromaApp:
    """
    An application to control Razer Chroma enabled devices.
    """
    websocket_uri = "ws://localhost:13337/razer/chromasdk"

    def __init__(self: Self, config: AppConfiguration) -> None:
        self.config = config
        self.started_event = threading.Event()

        self._state: State | None = None
        self._websocket: websockets.ClientConnection | None = None
        self._effect_update_task: asyncio.Task | None = None

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
        if self._state is None:
            self._state = State()
        if self._effect_update_task is None or self._effect_update_task.done():
            self._effect_update_task = asyncio.create_task(self._update_effects())
        self._state._effects_changed = True
        logger.debug(f"Connected to the Razer Chroma SDK ({self.websocket_uri})")

    async def stop(self: Self, *, complete: bool = True) -> None:
        """
        Deinitialize the Razer Chroma App.

        Args:
            complete: Whether a complete shutdown should be performed. (Clear current effect state)
        """
        self.started_event.clear()
        if complete:
            if self._effect_update_task is not None:
                self._effect_update_task.cancel()
                with suppress(asyncio.CancelledError):
                    await self._effect_update_task
                self._effect_update_task = None
            self._state = None
        if self._websocket is not None:
            await self._websocket.close()
            self._websocket = None

            logger.debug(f"Disconnected from the Razer Chroma SDK ({self.websocket_uri})")

    async def _send(self: Self, payload: Any, *, try_reconnect: bool = True) -> bool:
        """
        Send data through the Razer Chroma SDK.

        Args:
            try_reconnect: Whether a reconnection should be attempted if the websocket is unexpectedly closed.

        Returns:
            Whether the payload was sent successfully.
        """
        if self._websocket is not None:
            try:
                await self._websocket.send(json.dumps(payload))
                return True
            except (ConnectionError, websockets.ConnectionClosed):
                if try_reconnect and self.started_event.is_set():
                    await self.stop(complete=False) # Don't clear current effects
                    await self.start()
                    return await self._send(payload, try_reconnect=False)
        return False

    async def _update_effects(self: Self) -> None:
        """
        Update the colors of devices with active effects, update any effect animations, and remove expired effects.
        """
        while True:
            await asyncio.sleep(1 / 30)

            if self._state is not None:
                decimal_colors: dict[DeviceType, list[list[int]] | None] = device_type_dict()
                for device in self.config.supported_devices:
                    effects = self._state.effects[device]
                    expiring_effects = []
                    effect_changed = False

                    for effect in effects:
                        if effect.update_rate is not None and time.time() - effect._last_update_time >= effect.update_rate:
                            if effect.expires_after_updates is not None:
                                if effect.expires_after_updates == 0:
                                    expiring_effects.append(effect)
                                    continue
                                effect.expires_after_updates -= 1
                            if effect.update is not None:
                                effect.update(deepcopy(effect.colors))
                                effect_changed = True
                            effect._last_update_time = time.time()
                    for effect in expiring_effects:
                        self._state.remove_effect(effect)
                        effect_changed = True

                    effect_changed = effect_changed or self._state._effects_changed

                    if effect_changed and len(effects) > 0:
                        device_color_columns = effects[0]._colors_columns
                        device_color_rows = effects[0]._colors_rows

                        colors = [[Color() for _ in range(device_color_columns)] for _ in range(device_color_rows)]
                        for effect in effects:
                            match effect.method:
                                case EffectMethod.ADD:
                                    # Add everything
                                    for row, row_v in enumerate(effect.colors):
                                        for column, column_v in enumerate(row_v):
                                            colors[row][column] += column_v
                                case EffectMethod.ADD_NON_ZERO:
                                    # Add everything, except to values that are already zeros
                                    for row, row_v in enumerate(effect.colors):
                                        for column, column_v in enumerate(row_v):
                                            if colors[row][column].RGB_float != (0.0, 0.0, 0.0):
                                                colors[row][column] += column_v
                                case EffectMethod.SUBTRACT:
                                    # Subtract everything
                                    for row, row_v in enumerate(effect.colors):
                                        for column, column_v in enumerate(row_v):
                                            colors[row][column] -= column_v
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
                                            colors[row][column] *= column_v
                                case EffectMethod.DIVIDE:
                                    # Divide everything
                                    for row, row_v in enumerate(effect.colors):
                                        for column, column_v in enumerate(row_v):
                                            colors[row][column] /= column_v
                        # Convert the float colors to decimal colors usable by the Chroma SDK API
                        decimals = [[0 for _ in range(device_color_columns)] for _ in range(device_color_rows)]
                        for row, row_v in enumerate(colors):
                            for column, column_v in enumerate(row_v):
                                decimals[row][column] = column_v.BGR_decimal
                        decimal_colors[device] = decimals
                    elif effect_changed and self.started_event.is_set():
                        decimal_colors[device] = None
                self._state._effects_changed = False # Reset effects chanegd flag

                if self.started_event.is_set(): # Only send data if we are connected
                    for device, colors in decimal_colors.items():
                        if colors is None:
                            await self._send({
                                "endpoint": device,
                                "effect": "CHROMA_NONE"
                            })
                        else:
                            if len(colors) == 1:
                                colors = colors[0] # Devices that have one row don't accept 2D lists
                            match device:
                                case DeviceType.KEYBOARD:
                                    await self._send({
                                        "endpoint": device,
                                        "effect": "CHROMA_CUSTOM2",
                                        "param": {
                                           "color": colors,
                                           "key": [[0 for _ in range(22)] for _ in range(6)] # Make key param all zeros because it's not needed
                                        }
                                    })
                                case DeviceType.MOUSE:
                                    await self._send({
                                        "endpoint": device,
                                        "effect": "CHROMA_CUSTOM2",
                                        "param": colors
                                    })
                                case _:
                                    await self._send({
                                        "endpoint": device,
                                        "effect": "CHROMA_CUSTOM",
                                        "param": colors
                                    })
