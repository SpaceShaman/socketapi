# pyright: reportPrivateUsage=false

from socketapi import SocketAPI
from socketapi.testclient import TestClient

app = SocketAPI()


@app.channel("chat", default_response=False)
async def chat() -> dict[str, str]:
    return {"message": "Welcome"}


def test_disconnect():
    client = TestClient(app)

    with client.websocket_connect("/") as websocket:
        websocket.send_json({"type": "subscribe", "channel": "chat"})
        websocket.receive_json()
        assert len(app._socket_manager.channels["chat"]) == 1

    assert len(app._socket_manager.channels["chat"]) == 0
