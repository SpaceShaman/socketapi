from socketapi import SocketAPI
from socketapi.testclient import TestClient

app = SocketAPI()
client = TestClient(app)


def test_pass():
    assert True


def test_connect_to_websocket():
    with client.websocket_connect("/") as websocket:
        websocket.send_text("Hello, World!")
        data = websocket.receive_text()
        assert data == "Hello, World!"
