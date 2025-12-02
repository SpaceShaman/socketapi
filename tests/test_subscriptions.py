from socketapi import SocketAPI
from socketapi.testclient import TestClient

app = SocketAPI()

chat_calls: int = 0
news_calls: int = 0


@app.channel("chat")
async def chat() -> dict[str, str]:
    global chat_calls
    chat_calls += 1
    return {"message": "Welcome to the chat channel!"}


@app.channel("news", default_response=False)
async def news() -> dict[str, str]:
    global news_calls
    news_calls += 1
    return {"headline": "Breaking News!"}


def test_subscribe_to_channel():
    client = TestClient(app)

    assert "chat" in app.channel_manager.channels
    assert len(app.channel_manager.channels["chat"]) == 0

    with client.websocket_connect("/") as websocket:
        websocket.send_json({"type": "subscribe", "channel": "chat"})
        assert len(app.channel_manager.channels["chat"]) == 1
        response = websocket.receive_json()
        assert response == {"type": "subscribed", "channel": "chat"}
        response = websocket.receive_json()
        assert response == {
            "type": "data",
            "channel": "chat",
            "data": {"message": "Welcome to the chat channel!"},
        }
    global chat_calls
    assert chat_calls == 1
    chat_calls = 0


def test_subscribe_to_channel_without_default_response():
    client = TestClient(app)

    with client.websocket_connect("/") as websocket:
        websocket.send_json({"type": "subscribe", "channel": "news"})
        response = websocket.receive_json()
        assert response == {"type": "subscribed", "channel": "news"}
    global news_calls
    assert news_calls == 0


def test_subscribe_to_nonexistent_channel():
    client = TestClient(app)

    with client.websocket_connect("/") as websocket:
        websocket.send_json({"type": "subscribe", "channel": "nonexistent"})
        response = websocket.receive_json()
        assert response.get("error") == "Channel 'nonexistent' not found."
