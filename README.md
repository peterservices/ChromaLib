# ChromaLib

[![license](https://img.shields.io/pypi/l/chromalib.svg)](https://pypi.python.org/pypi/chromalib)
[![version](https://img.shields.io/pypi/v/chromalib.svg)](https://pypi.python.org/pypi/chromalib)
[![pyversions](https://img.shields.io/pypi/pyversions/chromalib.svg)](https://pypi.python.org/pypi/chromalib)

A typed library for Razer Chroma that supports effect layering, updates, and expiry while managing the connection with the Chroma SDK over a websocket, allowing you to focus on creating effects.

> [!NOTE]
> This library is in alpha and there may be breaking API changes in minor versions!
>
> Currently, Windows is the only supported platform, but support for Linux and macOS will be looked into.

## **Installing**

**Python 3.11 to 3.15 is supported**

```
pip install chromalib
```

## **Simple Example**

<details>

<summary>Example</summary>

```python
import asyncio

from chromalib import (
    AppCategory,
    AppConfiguration,
    AuthorConfiguration,
    ChromaApp,
    Color,
    DeviceType,
    EffectMethod,
    KeyboardEffect,
    create_explosion_colors,
    generate_explosion_updater,
)

configuration = AppConfiguration(
    title="Red Keyboard Integration",
    description="Sets the keyboard to red",
    author=AuthorConfiguration(
        name="YourName",
        contact="YourWebsite"
    ),
    supported_devices=[
        DeviceType.KEYBOARD
    ],
    category=AppCategory.APPLICATION,
    effect_id_hierarchy=[
        "background",
        "foreground"
    ] # Optional
)

app = ChromaApp(config=configuration)

async def main():
    await app.start()
    colors = [[Color(blue=1)] * 24] * 8 # 24 columns x 8 rows (Yes this is not optimal, will be improved later)
    app.add_effect(KeyboardEffect(
        colors=colors,
        method=EffectMethod.FILL,
        id="background"
    ))

    await asyncio.sleep(0.5)

    color = Color()
    color.RGB_int = (255, 0, 0) # Another way to specify color values
    app.add_effect(KeyboardEffect(
        colors=create_explosion_colors(color),
        method=EffectMethod.FILL_NON_ZERO,
        update=generate_explosion_updater(),
        update_rate_seconds=0.12,
        expires_after_updates=15,
        id="foreground"
    ))

    await asyncio.sleep(4)
    await app.stop()
asyncio.run(main())
```

</details>

## **Features**

* Supports all major device types
* Supports custom effect update functions
* Utilizes Pydantic models for easy type validation
* Fully typed with docstrings
* Asynchronous background loop

> [!IMPORTANT]
> ChromaLib is not affiliated or endorsed in any way by Razer or any of its subsidaries
