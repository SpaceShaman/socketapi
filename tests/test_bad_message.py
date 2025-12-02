from socketapi import SocketAPI
from socketapi.testclient import TestClient

app = SocketAPI()


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


def test_send_message_with_unknown_type():
    client = TestClient(app)

    with client.websocket_connect("/") as websocket:
        websocket.send_json({"type": "unknown", "channel": "chat"})
        response = websocket.receive_json()
        assert response.get("error") == "Unknown message type: unknown."
