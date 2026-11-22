import asyncio
import json
import logging
import time
from contextlib import suppress
from copy import deepcopy
from typing import Any, Self

import websockets

from .colors import Color
from .configurations import AppConfiguration, DeviceType
from .effects import Effect, EffectMethod, EffectState
from .exceptions import InitializedError, UninitializedError

logger = logging.getLogger(__name__)

class ChromaApp:
    """
    An application to control Razer Chroma enabled devices.
    """
    update_tolerance_seconds = 1 / 100 # (0.01s) How many seconds early effect updates can fire
    websocket_uri = "ws://localhost:13337/razer/chromasdk"

    def __init__(self: Self, config: AppConfiguration) -> None:
        self.config = config
        self.started_event = asyncio.Event()

        self._state: EffectState | None = None
        self._websocket: websockets.ClientConnection | None = None
        self._effect_update_task: asyncio.Task | None = None

    async def start(self: Self) -> None:
        """
        Intialize the Razer Chroma App.
        """
        if self.started_event.is_set():
            raise InitializedError("The app has already been initialized.")
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
        }, try_reconnect=False)

        await asyncio.sleep(2) # Give the Chroma SDK time to intialize the app before resetting device RGB
        for device in self.config.supported_devices:
            await self._send({
                "endpoint": device,
                "effect": "CHROMA_NONE"
            }, try_reconnect=False) # Clear Chroma effects for all active devices

        if self._state is None:
            self._state = EffectState()
        if self._effect_update_task is None or self._effect_update_task.done():
            self._effect_update_task = asyncio.create_task(self._update_effects())
        self.started_event.set()
        self._state._effects_changed.set()
        logger.debug("Connected to the Razer Chroma SDK (%s)", self.websocket_uri)

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

            logger.debug("Disconnected from the Razer Chroma SDK (%s)", self.websocket_uri)

    def find_effects_by_id(self: Self, id: str, device: DeviceType) -> list[Effect]:
        """
        Find an effect in the specified effects list by its id.

        Args:
            id: The effect id to look for.
            device: The device type of the effect to look for.

        Returns:
            The effects matching the provided id. (Lowest to highest hierarchy)
        """
        if self._state is None:
            raise UninitializedError("The app must be initialized before interacting with this method.")

        effects = self._state.effects[device]

        found_effects: list[Effect] = []
        if id is not None:
            for effect in effects:
                if effect.id == id:
                    found_effects.append(effect)
        return found_effects

    def add_effect(self: Self, effect: Effect) -> None:
        """
        Add an effect to it's device's effects list, respecting ids in `self.effect_id_hierarchy`.

        If an effect does not have a valid id, it will be treated as highest hierarchy.
        If two effects share the same id, the newest effect will have the higher hierarchy,

        Args:
            effect: The effect to be added.
        """
        if self._state is None:
            raise UninitializedError("The app must be initialized before interacting with this method.")

        effects = self._state.effects[effect._device_type]

        self._state._effects_changed.set()
        if effect.id is not None and len(effects) > 0 and effect.id in self.config.effect_id_hierarchy:
            highest_available_index = 0
            for id in self.config.effect_id_hierarchy:
                found_effects = self.find_effects_by_id(id, effect._device_type)
                if len(found_effects) > 0:
                    highest_available_index = effects.index(found_effects[-1]) + 1 # Newer effects are treated as higher hierarchy than older effects

                    # There is no point in checking the rest of the hierarchy if no other effects are in the list
                    if highest_available_index == len(effects):
                        effects.append(effect)
                        return

                if id == effect.id:
                    effects.insert(highest_available_index, effect)
                    return
        else:
            effects.append(effect)

    def remove_effect(self: Self, effect: Effect) -> None:
        """
        Remove an effect from it's device's effects list.

        Args:
            effect: The effect to be removed.
        """
        if self._state is None:
            raise UninitializedError("The app must be initialized before interacting with this method.")

        effects = self._state.effects[effect._device_type]

        if effect in effects:
            effects.remove(effect)
            self._state._effects_changed.set()

    def remove_effects_by_ids(self: Self, ids: list[str], devices: list[DeviceType]) -> None:
        """
        Remove effects by their ids from the specified effects lists by their ids.

        Args:
            ids: The effect ids to remove.
            devices: The device types of the effects to remove.
        """
        if self._state is None:
            raise UninitializedError("The app must be initialized before interacting with this method.")

        for id in ids:
            for device_type in devices:
                effects = self.find_effects_by_id(id, device_type)
                for effect in effects:
                    self.remove_effect(effect)

    async def _send(self: Self, payload: Any, *, try_reconnect: bool = True) -> None:
        """
        Send data through the Razer Chroma SDK.

        Args:
            try_reconnect: Whether a reconnection should be attempted if the websocket is unexpectedly closed.
        """
        if self._websocket is not None:
            try:
                await self._websocket.send(json.dumps(payload))
                return logger.debug("Sent payload to Razer Chroma SDK")
            except (ConnectionError, websockets.ConnectionClosed):
                if try_reconnect and self.started_event.is_set():
                    await self.stop(complete=False) # Don't clear current effects
                    await self.start()
                    return await self._send(payload, try_reconnect=False)
                raise
        raise UninitializedError("The app must be intialized to send data through the websocket.")

    async def _update_effects(self: Self) -> None:
        """
        Update the colors of devices with active effects, update any effect animations, and remove expired effects.
        """
        next_update_seconds: float | None = None
        while True:
            if self._state is not None:
                if next_update_seconds is None:
                    # Await effect changed if no current effects will update
                    await self._state._effects_changed.wait()
                else:
                    # Await the next update time or effect changed, whichever comes first
                    with suppress(TimeoutError):
                        await asyncio.wait_for(self._state._effects_changed.wait(), timeout=next_update_seconds)

                next_update_seconds = None
                decimal_colors: dict[DeviceType, list[list[int]] | None] = {key: [] for key in self.config.supported_devices}
                for device in self.config.supported_devices:
                    effects = self._state.effects[device]
                    expiring_effects = []
                    effect_changed = False

                    for effect in effects:
                        if effect.update_rate_seconds is not None:
                            toleranced_update_rate = effect.update_rate_seconds - self.update_tolerance_seconds
                            if time.monotonic() - effect._last_update_time >= (toleranced_update_rate):
                                if effect.expires_after_updates is not None:
                                    if effect.expires_after_updates == 0:
                                        expiring_effects.append(effect)
                                        continue
                                    effect.expires_after_updates -= 1
                                if effect.update is not None:
                                    effect.colors = effect.update(deepcopy(effect.colors))
                                    effect_changed = True
                                effect._last_update_time = time.monotonic()
                            else:
                                effect_next_update = toleranced_update_rate - (time.monotonic() - effect._last_update_time)
                                next_update_seconds = effect_next_update if next_update_seconds is None else min(next_update_seconds, effect_next_update)
                    for effect in expiring_effects:
                        self.remove_effect(effect)
                        effect_changed = True

                    effect_changed = effect_changed or self._state._effects_changed.is_set()

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
                self._state._effects_changed.clear() # Reset effects changed event

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
            else:
                await self.started_event.wait() # self._state should only become non-None when the app is started
