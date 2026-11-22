# ChromaLib

[![Build](https://github.com/peterservices/ChromaLib/actions/workflows/build.yml/badge.svg)](https://github.com/peterservices/ChromaLib/actions/workflows/build.yml)
[![Ruff](https://github.com/peterservices/ChromaLib/actions/workflows/ruff.yml/badge.svg)](https://github.com/peterservices/ChromaLib/actions/workflows/ruff.yml)

A typed library for Razer Chroma that supports effect layering, updates, and expiry while managing the connection with the Chroma SDK over a websocket, allowing you to focus on creating effects.

> [!NOTE]
> This library is in alpha and there may be breaking API changes in minor versions!
>
> Currently, Windows is the only supported platform, but support for Linux and macOS will be looked into.

## **Installing**

**Python 3.11 to 3.14 is supported**

```
pip install git+https://github.com/peterservices/ChromaLib.git
```

## **Simple Example**

coming soon

## **Features**

* Supports all major device types
* Supports custom effect update functions
* Utilizes Pydantic models for easy type validation
* Fully typed with docstrings
* Asynchronous background loop

All features are toggle-able via a JSON file generated when you first run the script.

> [!IMPORTANT]
> ChromaLib is not affiliated or endorsed in any way by Razer or any of their subsidaries