from unittest.mock import patch

import pytest

from socketapi import SocketAPI
from socketapi.testclient import TestClient


class FakeClientMiddleware:
    def __init__(self, app: SocketAPI, host: str, port: int):
        self.app = app
        self.host = host
        self.port = port

    async def __call__(self, scope, receive, send):  # type: ignore
        if scope["type"] in {"http", "websocket"}:
            scope["client"] = (self.host, self.port)
        await self.app(scope, receive, send)  # type: ignore


@pytest.mark.asyncio
async def test_broadcast_messages_from_outside_server():
    app = SocketAPI()
    app.add_middleware(FakeClientMiddleware, host="localhost", port=8000)  # type: ignore

    @app.channel("broadcast_channel")
    async def broadcast_channel(message: str = "") -> dict[str, str]:
        return {"message": message}

    client = TestClient(app)

    with client.websocket_connect("/") as websocket:
        websocket.send_json({"type": "subscribe", "channel": "broadcast_channel"})
        response = websocket.receive_json()
        assert response == {"type": "subscribed", "channel": "broadcast_channel"}

        app.server_started = False

        with patch("socketapi.handlers.Client", return_value=client):
            await broadcast_channel(message="Hello from mocked client!")

        app.server_started = True

        response = websocket.receive_json()
        assert response == {
            "type": "data",
            "channel": "broadcast_channel",
            "data": {"message": "Hello from mocked client!"},
        }


def test_call_broadcast_endpoint_from_non_localhost():
    app = SocketAPI()
    client = TestClient(app)

    response = client.post(
        "/_broadcast",
        json={"channel": "broadcast_channel", "data": {"message": "Test"}},
    )

    assert response.status_code == 403
