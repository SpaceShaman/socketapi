from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Awaitable, Callable, ParamSpec, TypeVar

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route, WebSocketRoute
from starlette.websockets import WebSocket, WebSocketDisconnect

from .handlers import ActionHandler, ChannelHandler
from .manager import SocketManager
from .router import Router

P = ParamSpec("P")
R = TypeVar("R")


class SocketAPI(Starlette):
    def __init__(self, host: str = "localhost", port: int = 8000) -> None:
        self.server_host = host
        self.server_port = port
        self._socket_manager = SocketManager()
        self.server_started = False
        routes = [
            WebSocketRoute("/", self._websocket_endpoint),
            Route("/_broadcast", self._broadcast_endpoint, methods=["POST"]),
        ]
        super().__init__(routes=routes, lifespan=self._lifespan)

    @asynccontextmanager
    async def _lifespan(self, app: "SocketAPI") -> AsyncGenerator[None, None]:
        self.server_started = True
        yield
        self.server_started = False

    def channel(
        self, name: str, default_response: bool = False
    ) -> Callable[[Callable[P, Awaitable[R]]], ChannelHandler[P, R]]:
        def decorator(func: Callable[P, Awaitable[R]]) -> ChannelHandler[P, R]:
            handler = ChannelHandler(
                func, name, self._socket_manager, default_response, self
            )
            self._socket_manager.create_channel(name, handler)
            return handler

        return decorator

    def action(
        self, name: str
    ) -> Callable[[Callable[P, Awaitable[R]]], ActionHandler[P, R]]:
        def decorator(func: Callable[P, Awaitable[R]]) -> ActionHandler[P, R]:
            handler = ActionHandler(func, name, self._socket_manager)
            self._socket_manager.create_action(name, handler)
            return handler

        return decorator

    async def _broadcast_endpoint(self, request: Request) -> JSONResponse:
        payload = await request.json()
        channel = payload.get("channel")
        data = payload.get("data", {})
        handler = self._socket_manager.channel_handlers[channel]
        await handler(**data)
        return JSONResponse({"status": "success"})

    async def _websocket_endpoint(self, websocket: WebSocket) -> None:
        await websocket.accept()
        try:
            while True:
                data = await websocket.receive_json()
                await self._handle_message(websocket, data)
        except WebSocketDisconnect:
            await self._socket_manager.unsubscribe_all(websocket)

    async def _handle_message(
        self, websocket: WebSocket, message: dict[str, Any]
    ) -> None:
        message_type = message.get("type")
        if not message_type:
            await self._socket_manager.error(websocket, "Message type is required.")
            return
        channel = message.get("channel")
        if not channel:
            await self._socket_manager.error(websocket, "Channel is required.")
            return
        data = message.get("data", {})
        match message_type:
            case "subscribe":
                await self._socket_manager.subscribe(channel, websocket, data)
            case "unsubscribe":
                await self._socket_manager.unsubscribe(channel, websocket)
            case "action":
                await self._socket_manager.action(channel, websocket, data)
            case _:
                await self._socket_manager.error(
                    websocket, f"Unknown message type: {message_type}."
                )

    def include_router(self, router: Router) -> None:
        for name, channel in router.channels.items():
            handler = ChannelHandler(
                channel["func"].fn,
                name,
                self._socket_manager,
                channel["default_response"],
                self,
            )
            channel["func"].set(handler)
            self._socket_manager.create_channel(name, handler)
        for name, action in router.actions.items():
            handler = ActionHandler(
                action["func"].fn,
                name,
                self._socket_manager,
            )
            action["func"].set(handler)
            self._socket_manager.create_action(name, handler)
