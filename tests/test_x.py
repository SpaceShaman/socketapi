from socketapi import SocketAPI
from socketapi.testclient import TestClient

app = SocketAPI()


@app.subscribe("chat")
async def chat():
    pass


def test_subscribe_to_channel():
    client = TestClient(app)

    assert "chat" in app.subscription_manager.channels
    assert len(app.subscription_manager.channels["chat"]) == 0

    with client.websocket_connect("/") as websocket:
        websocket.send_json({"type": "subscribe", "channel": "chat"})
        assert len(app.subscription_manager.channels["chat"]) == 1
        response = websocket.receive_json()
        assert response == {"type": "subscribed", "channel": "chat"}


def test_subscribe_to_nonexistent_channel():
    client = TestClient(app)

    with client.websocket_connect("/") as websocket:
        websocket.send_json({"type": "subscribe", "channel": "nonexistent"})
        response = websocket.receive_json()
        assert response.get("error") == "Channel 'nonexistent' not found."


def test_send_message_without_type():
    client = TestClient(app)

    with client.websocket_connect("/") as websocket:
        websocket.send_json({"channel": "chat"})
        response = websocket.receive_json()
        assert response.get("error") == "Message type is required."


def test_send_message_without_channel():
    client = TestClient(app)

    with client.websocket_connect("/") as websocket:
        websocket.send_json({"type": "subscribe"})
        response = websocket.receive_json()
        assert response.get("error") == "Channel is required."
