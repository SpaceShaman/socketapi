from typing import Callable

from starlette.applications import Starlette
from starlette.routing import WebSocketRoute
from starlette.websockets import WebSocket, WebSocketDisconnect

from .types import DecoratedCallable


class SubscriptionManager:
    def __init__(self) -> None:
        self.channels: dict[str, set[WebSocket]] = {}

    def create_channel(self, channel: str) -> None:
        self.channels[channel] = set()

    async def subscribe(self, channel: str, websocket: WebSocket) -> None:
        if channel not in self.channels:
            await websocket.send_json({"error": f"Channel '{channel}' not found."})
            return
        self.channels[channel].add(websocket)


class SocketAPI(Starlette):
    def __init__(self) -> None:
        self.subscription_manager = SubscriptionManager()
        routes = [WebSocketRoute("/", self._websocket_endpoint)]
        super().__init__(routes=routes)

    def channel(self, name: str) -> Callable[[DecoratedCallable], DecoratedCallable]:
        def decorator(func: DecoratedCallable) -> DecoratedCallable:
            self.subscription_manager.create_channel(name)
            return func

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
            await self.subscription_manager.subscribe(channel, websocket)
