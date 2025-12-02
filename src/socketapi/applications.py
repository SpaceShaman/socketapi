from functools import wraps
from typing import Any, Awaitable, Callable, ParamSpec, TypeVar

from starlette.applications import Starlette
from starlette.routing import WebSocketRoute
from starlette.websockets import WebSocket, WebSocketDisconnect

P = ParamSpec("P")
R = TypeVar("R")


class ChannelManager:
    def __init__(self) -> None:
        self.channels: dict[str, set[WebSocket]] = {}

    def create_channel(self, channel: str) -> None:
        self.channels[channel] = set()

    async def subscribe(self, channel: str, websocket: WebSocket) -> WebSocket | None:
        if channel not in self.channels:
            await websocket.send_json({"error": f"Channel '{channel}' not found."})
            return None
        self.channels[channel].add(websocket)
        await websocket.send_json({"type": "subscribed", "channel": channel})
        return websocket


class SocketAPI(Starlette):
    def __init__(self) -> None:
        self.channel_manager = ChannelManager()
        self.handlers: dict[str, Callable[..., Any]] = {}
        routes = [WebSocketRoute("/", self._websocket_endpoint)]
        super().__init__(routes=routes)

    def channel(
        self,
        name: str,
    ) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]:
        def decorator(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
            @wraps(func)
            async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
                result = await func(*args, **kwargs)
                return result

            self.channel_manager.create_channel(name)
            self.handlers[name] = wrapper
            return wrapper

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
            if subscripted_ws := await self.channel_manager.subscribe(
                channel, websocket
            ):
                default_response = await self.handlers[channel]()
                await self._send_data(subscripted_ws, channel, default_response)

    async def _send_data(
        self, websocket: WebSocket, channel: str, payload: dict[str, Any]
    ) -> None:
        await websocket.send_json({"type": "data", "channel": channel, "data": payload})
