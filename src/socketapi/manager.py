from typing import TYPE_CHECKING, Any

from starlette.websockets import WebSocket

from socketapi.validation import validate_and_execute

if TYPE_CHECKING:
    from .handlers import ActionHandler, ChannelHandler


class SocketManager:
    def __init__(self) -> None:
        self.channels: dict[str, set[WebSocket]] = {}
        self.channel_handlers: dict[str, "ChannelHandler[Any, Any]"] = {}
        self.action_handlers: dict[str, "ActionHandler[Any, Any]"] = {}

    def create_channel(self, name: str, handler: "ChannelHandler[Any, Any]") -> None:
        self.channel_handlers[name] = handler
        self.channels[name] = set()

    def create_action(self, name: str, handler: "ActionHandler[Any, Any]") -> None:
        self.action_handlers[name] = handler

    async def subscribe(
        self, channel: str, websocket: WebSocket, result: dict[str, Any]
    ) -> None:
        handler = self.channel_handlers.get(channel)
        if not handler:
            await self.error(websocket, f"Channel '{channel}' not found.")
            return None
        try:
            result = await validate_and_execute(handler.func, result, on_subscribe=True)
        except Exception as e:
            await self.error(websocket, str(e))
            return None
        self.channels[channel].add(websocket)
        await self.send(websocket, "subscribed", channel)
        if handler.default_response:
            await handler.send_initial_data(websocket, result)

    async def unsubscribe(self, channel: str, websocket: WebSocket) -> None:
        if channel in self.channels:
            self.channels[channel].discard(websocket)
        await self.send(websocket, "unsubscribed", channel)

    async def action(
        self, channel: str, websocket: WebSocket, data: dict[str, Any]
    ) -> None:
        if channel not in self.action_handlers:
            await self.error(websocket, f"Action '{channel}' not found.")
            return None
        try:
            result = await validate_and_execute(
                self.action_handlers[channel].func, data
            )
        except Exception as e:
            await self.error(websocket, str(e))
            return None
        if hasattr(result, "model_dump"):
            result = result.model_dump()
        await self.send(
            websocket,
            "action",
            channel,
            result,
            "completed",
        )

    async def send(
        self,
        websocket: WebSocket,
        type: str,
        channel: str,
        data: Any | None = None,
        status: str | None = None,
    ) -> None:
        payload = {"type": type, "channel": channel}
        if status:
            payload["status"] = status
        if data:
            payload["data"] = data
        await self._send_json(websocket, payload)

    async def error(self, websocket: WebSocket, message: str) -> None:
        await self._send_json(websocket, {"type": "error", "message": message})

    async def _send_json(self, websocket: WebSocket, data: dict[str, Any]) -> None:
        try:
            await websocket.send_json(data)
        except Exception:
            await self.unsubscribe_all(websocket)

    async def unsubscribe_all(self, websocket: WebSocket) -> None:
        for sockets in list(self.channels.values()):
            sockets.discard(websocket)
