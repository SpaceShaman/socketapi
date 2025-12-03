from typing import TYPE_CHECKING, Awaitable, Callable, Generic, ParamSpec, TypeVar

from starlette.websockets import WebSocket

if TYPE_CHECKING:
    from .manager import SocketManager

P = ParamSpec("P")
R = TypeVar("R")


class ChannelHandler(Generic[P, R]):
    def __init__(
        self,
        func: Callable[P, Awaitable[R]],
        channel: str,
        socket_manager: "SocketManager",
        default_response: bool,
    ) -> None:
        self._func = func
        self._channel = channel
        self._socket_manager = socket_manager
        self._default_response = default_response

    async def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R | None:
        data = await self._func(*args, **kwargs)
        for websocket in list(self._socket_manager.channels[self._channel]):
            await self._send_data(websocket, self._channel, data)
        return data

    async def send_initial_data(
        self, websocket: WebSocket, *args: P.args, **kwargs: P.kwargs
    ) -> None:
        if not self._default_response:
            return
        data = await self._func(*args, **kwargs)
        await self._send_data(websocket, self._channel, data)

    async def _send_data(self, websocket: WebSocket, channel: str, payload: R) -> None:
        await self._socket_manager.send(websocket, "data", channel, payload)
