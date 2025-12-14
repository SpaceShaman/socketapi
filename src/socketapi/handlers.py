from typing import TYPE_CHECKING, Any, Awaitable, Callable, Generic, ParamSpec, TypeVar

from httpx import Client
from starlette.websockets import WebSocket

if TYPE_CHECKING:
    from .main import SocketAPI
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
        app: "SocketAPI",
    ) -> None:
        self.func = func
        self._channel = channel
        self._socket_manager = socket_manager
        self._app = app
        self.default_response = default_response

    async def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R | None:
        if not self._app.server_started:
            _broadcast_message_from_outside_server(
                self._app.server_host, self._app.server_port, self._channel, {**kwargs}
            )
            return None
        data = await self.func(*args, **kwargs)
        for websocket in list(self._socket_manager.channels[self._channel]):
            await self._send_data(websocket, self._channel, data)
        return data

    async def send_initial_data(self, websocket: WebSocket, payload: R) -> None:
        await self._send_data(websocket, self._channel, payload)

    async def _send_data(self, websocket: WebSocket, channel: str, payload: R) -> None:
        await self._socket_manager.send(websocket, "data", channel, payload)


class ActionHandler(Generic[P, R]):
    def __init__(
        self,
        func: Callable[P, Awaitable[R]],
        channel: str,
        socket_manager: "SocketManager",
    ) -> None:
        self.func = func
        self._channel = channel
        self._socket_manager = socket_manager

    async def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        return await self.func(*args, **kwargs)


def _broadcast_message_from_outside_server(
    host: str, port: int, channel: str, data: dict[str, Any]
) -> None:
    with Client() as client:
        response = client.post(
            f"http://{host}:{port}/_broadcast",
            json={
                "channel": channel,
                "data": data,
            },
        )
        response.raise_for_status()
