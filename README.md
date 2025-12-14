<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://github.com/SpaceShaman/socketapi/raw/master/docs/assets/logo-light.png">
  <img src="https://github.com/SpaceShaman/socketapi/raw/master/docs/assets/logo-dark.png" alt="socketapi">
</picture>

<!--intro-start-->
[![GitHub License](https://img.shields.io/github/license/SpaceShaman/socketapi)](https://github.com/SpaceShaman/socketapi?tab=MIT-1-ov-file)
[![Tests](https://img.shields.io/github/actions/workflow/status/SpaceShaman/socketapi/publish.yml?label=tests)](https://github.com/SpaceShaman/socketapi/blob/master/.github/workflows/tests.yml)
[![Codecov](https://img.shields.io/codecov/c/github/SpaceShaman/socketapi)](https://codecov.io/gh/SpaceShaman/socketapi)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/socketapi)](https://pypi.org/project/socketapi)
[![PyPI - Version](https://img.shields.io/pypi/v/socketapi)](https://pypi.org/project/socketapi)
[![Code style: black](https://img.shields.io/badge/code%20style-black-black)](https://github.com/psf/black)
[![Linting: Ruff](https://img.shields.io/badge/linting-Ruff-black?logo=ruff&logoColor=black)](https://github.com/astral-sh/ruff)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Starlette](https://img.shields.io/badge/technology-Starlette-blue?logoColor=blue)](https://starlette.dev)
[![Pydantic](https://img.shields.io/badge/technology-Pydantic-blue?logo=pydantic&logoColor=blue)](https://docs.pydantic.dev)
[![Pytest](https://img.shields.io/badge/testing-Pytest-red?logo=pytest&logoColor=red)](https://docs.pytest.org/)
[![Material for MkDocs](https://img.shields.io/badge/docs-Material%20for%20MkDocs-yellow?logo=MaterialForMkDocs&logoColor=yellow)](https://spaceshaman.github.io/socketapi/)

The main goal of **SocketAPI** is to provide an easy-to-use and flexible framework for building [WebSocket](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API) APIs using [Python](https://www.python.org/). It leverages the power of [Starlette](https://starlette.dev/) for handling [WebSocket](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API) connections and [Pydantic](https://docs.pydantic.dev) for data validation and serialization.
It uses a **single multiplexed WebSocket connection**, allowing clients to exchange different types of information through **endpoint-like actions** and **channel subscriptions**, defined similarly to routes in [FastAPI](https://fastapi.tiangolo.com/).
The framework is inspired by both [FastAPI](https://fastapi.tiangolo.com/) and [Phoenix LiveView](https://hexdocs.pm/phoenix_live_view/Phoenix.LiveView.html), combining familiar declarative endpoints with real-time, channel-oriented communication.

## Installation

You can install SocketAPI using pip:

```bash
pip install socketapi
```

## Simple example

### Server

```python
from socketapi import SocketAPI

app = SocketAPI()

# Define "add_numbers" action - endpoint for performing calculations
@app.action("add_numbers")
async def add_numbers(a: int, b: int) -> int:
    return a + b

# Define "chat" channel - subscription for receiving messages
@app.channel("chat")
async def chat_channel(message: str = "Welcome"):
    return {"message": message}

# Action that sends a message to all "chat" channel subscribers
@app.action("send_message")
async def send_message(message: str):
    await chat_channel(message=message)
```

Run the server with any ASGI server (e.g., [Uvicorn](https://www.uvicorn.org/)):
```bash
uvicorn main:app --reload
```

### Client Usage

Connect to the WebSocket endpoint at `ws://localhost:8000/` and exchange JSON messages.

#### Calling an action (request-response pattern)

Send:
```json
{"type": "action", "channel": "add_numbers", "data": {"a": 5, "b": 3}}
```

Receive:
```json
{"type": "action", "channel": "add_numbers", "status": "completed", "data": 8}
```

#### Subscribing to a channel (pub/sub pattern)

Send:
```json
{"type": "subscribe", "channel": "chat"}
```

Receive confirmation:
```json
{"type": "subscribed", "channel": "chat"}
```

#### Broadcasting to channel subscribers

Send:
```json
{"type": "action", "channel": "send_message", "data": {"message": "Hello everyone!"}}
```

Receive confirmation:
```json
{"type": "action", "channel": "send_message", "status": "completed"}
```

All subscribers receive:
```json
{"type": "data", "channel": "chat", "data": {"message": "Hello everyone!"}}
```

**How it works:**

- **Actions** (`@app.action`) - endpoint-like, request-response pattern. Client sends a request and receives a response.
- **Channels** (`@app.channel`) - pub/sub pattern. Client subscribes to a channel and automatically receives all data emitted to that channel.
- **Single WebSocket** - all operations (actions, channels) work through a single WebSocket connection multiplexed via the `channel` field.
<!--intro-end-->

## Documentation

The full documentation is available at [spaceshaman.github.io/socketapi/](https://spaceshaman.github.io/socketapi/)

## Features and Roadmap

<!--roadmap-start-->
- [x] Define actions with request-response pattern
- [x] Define channels with pub/sub pattern
- [x] Single multiplexed WebSocket connection
- [x] Pydantic models for data validation
- [x] Error handling and validation
- [X] Dependency injection system (like FastAPI)
- [X] Router class for splitting API into multiple files similar to FastAPI
- [X] Broadcasting messages from outside the server context by calling channel-decorated functions
- [X] Error reporting inside decorated handlers with automatic error messages sent to client
<!--roadmap-end-->

## Changelog

<!--changelog-start-->
Changes for each release are thoroughly documented in [release notes](https://github.com/SpaceShaman/socketapi/releases)
<!--changelog-end-->

## Contributing

<!--contributing-start-->
Contributions are welcome! Feel free to open an issue or submit a pull request.
I would like to keep the library to be safe as possible, so i would appreciate if you cover any new feature with tests to maintain 100% coverage.

### Install in a development environment

1. First, clone the repository:

    ```bash
    git clone git@github.com:SpaceShaman/socketapi.git
    ```

2. Install [uv](https://docs.astral.sh/uv/) if you don't have it:

    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

3. Create a virtual environment and install the dependencies:

    ```bash
    cd socketapi
    uv sync
    ```

### Run tests

You can run the tests with the following command:

```bash
uv run pytest
```

You can also run the tests with coverage:
```bash
uv run pytest --cov=socketapi
```
<!--contributing-end-->

## License

This project is licensed under the terms of the [MIT license](https://github.com/SpaceShaman/socketapi?tab=MIT-1-ov-file)
