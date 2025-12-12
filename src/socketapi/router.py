from typing import Any, Awaitable, Callable, ParamSpec, TypedDict, TypeVar

from socketapi.handlers import ChannelHandler
from socketapi.manager import SocketManager

P = ParamSpec("P")
R = TypeVar("R")


class ChannelDefinition(TypedDict):
    name: str
    func: Callable[..., Awaitable[Any]]
    default_response: bool


class Router:
    def __init__(self):
        self.functions: list[ChannelDefinition] = []
        self._socket_manager: SocketManager | None = None

    def channel(
        self, name: str, default_response: bool = True
    ) -> Callable[
        [Callable[P, Awaitable[R]]], ChannelHandler[P, R] | Callable[P, Awaitable[R]]
    ]:
        def decorator(
            func: Callable[P, Awaitable[R]],
        ) -> Callable[P, Awaitable[R]] | ChannelHandler[P, R]:
            self.functions.append(
                {"name": name, "func": func, "default_response": default_response}
            )
            if self._socket_manager:
                return self._socket_manager.channel_handlers[name]
            return func

        return decorator

    def assign_socket_manager(self, socket_manager: SocketManager) -> None:
        self._socket_manager = socket_manager
