from socketapi import SocketAPI
from socketapi.testclient import TestClient


def test_connect_to_websocket():
    app = SocketAPI()
    client = TestClient(app)
    with client.websocket_connect("/") as websocket:
        websocket.send_text("Hello, World!")
        data = websocket.receive_text()
        assert data == "Hello, World!"


def test_subscribe_to_channel():
    app = SocketAPI()

    @app.subscribe("chat")
    async def chat():
        pass

    client = TestClient(app)

    with client.websocket_connect("/") as websocket:
        websocket.send_json({"type": "subscribe", "channel": "chat"})
