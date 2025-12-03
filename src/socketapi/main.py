from typing import Awaitable, Callable, ParamSpec, TypeVar

from starlette.applications import Starlette
from starlette.routing import WebSocketRoute
from starlette.websockets import WebSocket, WebSocketDisconnect

from .handlers import ChannelHandler
from .manager import SocketManager

P = ParamSpec("P")
R = TypeVar("R")


class SocketAPI(Starlette):
    def __init__(self) -> None:
        self._socket_manager = SocketManager()
        routes = [WebSocketRoute("/", self._websocket_endpoint)]
        super().__init__(routes=routes)

    def channel(
        self, name: str, default_response: bool = True
    ) -> Callable[[Callable[P, Awaitable[R]]], ChannelHandler[P, R]]:
        def decorator(func: Callable[P, Awaitable[R]]) -> ChannelHandler[P, R]:
            self._socket_manager.create_channel(name)
            handler = ChannelHandler(func, name, self._socket_manager, default_response)
            self._socket_manager.handlers[name] = handler
            return handler

        return decorator

    async def _websocket_endpoint(self, websocket: WebSocket) -> None:
        await websocket.accept()
        try:
            while True:
                data = await websocket.receive_json()
                await self._handle_message(websocket, data)
        except WebSocketDisconnect:
            await self._socket_manager.unsubscribe_all(websocket)

    async def _handle_message(self, websocket: WebSocket, data: dict[str, str]) -> None:
        message_type = data.get("type")
        if not message_type:
            await self._socket_manager.error(websocket, "Message type is required.")
            return
        channel = data.get("channel")
        if not channel:
            await self._socket_manager.error(websocket, "Channel is required.")
            return
        match message_type:
            case "subscribe":
                await self._socket_manager.subscribe(channel, websocket)
            case "unsubscribe":
                await self._socket_manager.unsubscribe(channel, websocket)
            case _:
                await self._socket_manager.error(
                    websocket, f"Unknown message type: {message_type}."
                )
