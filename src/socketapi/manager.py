from typing import TYPE_CHECKING, Any, ParamSpec, TypeVar

from starlette.websockets import WebSocket

if TYPE_CHECKING:
    from .handlers import ChannelHandler


P = ParamSpec("P")
R = TypeVar("R")


class SocketManager:
    def __init__(self) -> None:
        self.channels: dict[str, set[WebSocket]] = {}
        self.handlers: dict[str, "ChannelHandler[Any, Any]"] = {}

    def create_channel(self, channel: str) -> None:
        self.channels[channel] = set()

    async def subscribe(self, channel: str, websocket: WebSocket) -> None | WebSocket:
        if channel not in self.channels:
            await self.error(websocket, f"Channel '{channel}' not found.")
            return None
        self.channels[channel].add(websocket)
        await self.send(websocket, "subscribed", channel)
        await self.handlers[channel].send_initial_data(websocket)
        return websocket

    async def unsubscribe(self, channel: str, websocket: WebSocket) -> None:
        if channel in self.channels:
            self.channels[channel].discard(websocket)
        await self.send(websocket, "unsubscribed", channel)

    async def send(
        self, websocket: WebSocket, type: str, channel: str, data: Any | None = None
    ) -> None:
        payload = {"type": type, "channel": channel}
        if data:
            payload["data"] = data
        await self._send_json(websocket, payload)

    async def error(self, websocket: WebSocket, message: str) -> None:
        await self._send_json(websocket, {"error": message})

    async def _send_json(self, websocket: WebSocket, data: dict[str, Any]) -> None:
        try:
            await websocket.send_json(data)
        except Exception:
            await self.unsubscribe_all(websocket)

    async def unsubscribe_all(self, websocket: WebSocket) -> None:
        for sockets in list(self.channels.values()):
            sockets.discard(websocket)
