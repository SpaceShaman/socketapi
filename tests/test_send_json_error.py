# pyright: reportPrivateUsage=false
from unittest.mock import AsyncMock

import pytest

from socketapi import SocketAPI
from socketapi.testclient import TestClient

app = SocketAPI()
client = TestClient(app)


@app.channel("chat", default_response=False)
async def chat() -> dict[str, str]:
    return {"message": "Welcome"}


@pytest.mark.asyncio
async def test_send_json_exception_triggers_unsubscribe_all():
    with client.websocket_connect("/") as websocket:
        websocket.send_json({"type": "subscribe", "channel": "chat"})
        websocket.receive_json()

        # Verify websocket is subscribed
        assert len(app._socket_manager.channels["chat"]) == 1

        # Get the server-side websocket object
        server_websocket = list(app._socket_manager.channels["chat"])[0]

        # Mock send_json on server-side websocket to raise an exception
        original_send_json = server_websocket.send_json
        server_websocket.send_json = AsyncMock(
            side_effect=RuntimeError("Connection error")
        )

        # Trigger send_json through chat() which will call _send_data -> send -> _send_json
        with client:
            await chat()

        # The exception in _send_json should trigger unsubscribe_all
        assert len(app._socket_manager.channels["chat"]) == 0

        # Restore original method
        server_websocket.send_json = original_send_json


@pytest.mark.asyncio
async def test_send_json_exception_on_subscribe():
    with client.websocket_connect("/") as websocket:
        websocket.send_json({"type": "subscribe", "channel": "chat"})
        websocket.receive_json()  # subscribed message

        assert len(app._socket_manager.channels["chat"]) == 1

        # Get server-side websocket and mock it to fail on next send
        server_websocket = list(app._socket_manager.channels["chat"])[0]
        original_send_json = server_websocket.send_json
        server_websocket.send_json = AsyncMock(
            side_effect=RuntimeError("Connection error")
        )

        # Try to send error message - this will trigger exception in _send_json
        await app._socket_manager.error(server_websocket, "Test error")

        # Should trigger unsubscribe_all
        assert len(app._socket_manager.channels["chat"]) == 0

        server_websocket.send_json = original_send_json
