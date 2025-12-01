from starlette.applications import Starlette
from starlette.routing import WebSocketRoute
from starlette.websockets import WebSocket, WebSocketDisconnect


class SocketAPI(Starlette):
    def __init__(self):
        routes = [WebSocketRoute("/", self.websocket_endpoint)]
        super().__init__(routes=routes)

    async def websocket_endpoint(self, websocket: WebSocket):
        await websocket.accept()
        try:
            while True:
                data = await websocket.receive_text()
                await websocket.send_text(data)
        except WebSocketDisconnect:
            pass
