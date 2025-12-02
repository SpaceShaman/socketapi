from typing import Callable

from starlette.applications import Starlette
from starlette.routing import WebSocketRoute
from starlette.websockets import WebSocket, WebSocketDisconnect

from .types import DecoratedCallable


class SubscriptionManager:
    def __init__(self):
        self.channels: dict[str, set[WebSocket]] = {}

    def create_channel(self, channel: str):
        self.channels[channel] = set()


class SocketAPI(Starlette):
    def __init__(self) -> None:
        self.subscription_manager = SubscriptionManager()
        routes = [WebSocketRoute("/", self._websocket_endpoint)]
        super().__init__(routes=routes)

    async def _websocket_endpoint(self, websocket: WebSocket):
        await websocket.accept()
        try:
            while True:
                data = await websocket.receive_text()
                await websocket.send_text(data)
        except WebSocketDisconnect:
            pass

    def subscribe(
        self, channel: str
    ) -> Callable[[DecoratedCallable], DecoratedCallable]:
        def decorator(func: DecoratedCallable) -> DecoratedCallable:
            self.subscription_manager.create_channel(channel)
            return func

        return decorator
