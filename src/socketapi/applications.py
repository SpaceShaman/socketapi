from typing import Any, Awaitable, Callable, Generic, ParamSpec, TypeVar

from starlette.applications import Starlette
from starlette.routing import WebSocketRoute
from starlette.websockets import WebSocket, WebSocketDisconnect

P = ParamSpec("P")
R = TypeVar("R")


class ChannelHandler(Generic[P, R]):
    def __init__(
        self,
        func: Callable[P, Awaitable[R]],
        channel: str,
        sockets: set[WebSocket],
        default_response: bool,
    ) -> None:
        self._func = func
        self._channel = channel
        self._sockets = sockets
        self._default_response = default_response

    async def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R | None:
        data = await self._func(*args, **kwargs)
        for websocket in self._sockets:
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
        await websocket.send_json({"type": "data", "channel": channel, "data": payload})


class ChannelManager:
    def __init__(self) -> None:
        self.channels: dict[str, set[WebSocket]] = {}
        self.handlers: dict[str, ChannelHandler[Any, Any]] = {}

    def create_channel(self, channel: str) -> None:
        self.channels[channel] = set()

    async def subscribe(self, channel: str, websocket: WebSocket) -> None | WebSocket:
        if channel not in self.channels:
            await websocket.send_json({"error": f"Channel '{channel}' not found."})
            return None
        self.channels[channel].add(websocket)
        await websocket.send_json({"type": "subscribed", "channel": channel})
        await self.handlers[channel].send_initial_data(websocket)
        return websocket


class SocketAPI(Starlette):
    def __init__(self) -> None:
        self.channel_manager = ChannelManager()
        routes = [WebSocketRoute("/", self._websocket_endpoint)]
        super().__init__(routes=routes)

    def channel(
        self, name: str, default_response: bool = True
    ) -> Callable[[Callable[P, Awaitable[R]]], ChannelHandler[P, R]]:
        def decorator(func: Callable[P, Awaitable[R]]) -> ChannelHandler[P, R]:
            self.channel_manager.create_channel(name)
            handler = ChannelHandler(
                func, name, self.channel_manager.channels[name], default_response
            )
            self.channel_manager.handlers[name] = handler
            return handler

        return decorator

    async def _websocket_endpoint(self, websocket: WebSocket) -> None:
        await websocket.accept()
        try:
            while True:
                data = await websocket.receive_json()
                await self._handle_message(websocket, data)
        except WebSocketDisconnect:
            pass

    async def _handle_message(self, websocket: WebSocket, data: dict[str, str]) -> None:
        message_type = data.get("type")
        if not message_type:
            await websocket.send_json({"error": "Message type is required."})
            return
        channel = data.get("channel")
        if not channel:
            await websocket.send_json({"error": "Channel is required."})
            return
        if message_type == "subscribe":
            await self.channel_manager.subscribe(channel, websocket)
