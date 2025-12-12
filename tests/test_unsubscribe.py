# pyright: reportPrivateUsage=false

from socketapi import SocketAPI
from socketapi.testclient import TestClient

app = SocketAPI()

chat_calls: int = 0


@app.channel("chat", default_response=False)
async def chat() -> dict[str, str]:
    global chat_calls
    chat_calls += 1
    return {"message": "Welcome"}


def test_unsubscribe_from_channel():
    global chat_calls
    client = TestClient(app)

    assert "chat" in app._socket_manager._channels
    assert len(app._socket_manager._channels["chat"]) == 0

    with client.websocket_connect("/") as websocket:
        websocket.send_json({"type": "subscribe", "channel": "chat"})
        response = websocket.receive_json()
        assert response == {"type": "subscribed", "channel": "chat"}
        assert len(app._socket_manager._channels["chat"]) == 1

        websocket.send_json({"type": "unsubscribe", "channel": "chat"})
        response = websocket.receive_json()
        assert response == {"type": "unsubscribed", "channel": "chat"}
        assert len(app._socket_manager._channels["chat"]) == 0
    assert chat_calls == 0
    chat_calls = 0
