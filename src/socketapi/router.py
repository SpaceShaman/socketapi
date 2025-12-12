from typing import Any, Awaitable, Callable, ParamSpec, TypeVar

from socketapi.handlers import ChannelHandler

P = ParamSpec("P")
R = TypeVar("R")


class Router:
    def __init__(self):
        self.channels: dict[str, Callable[..., Awaitable[Any]]] = {}
        self._channel_handlers: dict[str, ChannelHandler[Any, Any]] = {}

    def channel(
        self, name: str
    ) -> Callable[[Callable[P, Awaitable[R]]], ChannelHandler[P, R]]:
        def decorator(func: Callable[P, Awaitable[R]]) -> ChannelHandler[P, R]:
            self.channels[name] = func
            return self._channel_handlers[name]

        return decorator
