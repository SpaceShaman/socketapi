from unittest.mock import patch

import pytest
import uvicorn

from socketapi import SocketAPI
from socketapi.testclient import TestClient

app = SocketAPI()
client = TestClient(app)


@app.channel("broadcast_channel", default_response=False)
async def broadcast_channel(message: str) -> dict[str, str]:
    return {"message": message}


def run_server():
    uvicorn.run(app, host="0.0.0.0", port=8000)


@pytest.mark.asyncio
async def test_broadcast_messages_from_outside_server():
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
