<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://github.com/SpaceShaman/socketapi/raw/master/docs/assets/logo-light.png">
  <img src="https://github.com/SpaceShaman/socketapi/raw/master/docs/assets/logo-dark.png" alt="socketapi">
</picture>

<!--intro-start-->
[![GitHub License](https://img.shields.io/github/license/SpaceShaman/socketapi)](https://github.com/SpaceShaman/socketapi?tab=MIT-1-ov-file)
[![Tests](https://img.shields.io/github/actions/workflow/status/SpaceShaman/socketapi/release.yml?label=tests)](https://github.com/SpaceShaman/socketapi/blob/master/.github/workflows/tests.yml)
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
It uses a **single multiplexed WebSocket connection**, allowing clients to exchange different types of information through **endpoint-like actions**, defined similarly to routes in [FastAPI](https://fastapi.tiangolo.com/).
The framework is inspired by both [FastAPI](https://fastapi.tiangolo.com/) and [Phoenix LiveView](https://hexdocs.pm/phoenix_live_view/Phoenix.LiveView.html), combining familiar declarative endpoints with real-time, channel-oriented communication.
<!--intro-end-->

