# pyright: reportPrivateUsage=false
import asyncio

from socketapi import SocketAPI
from socketapi.testclient import TestClient

app = SocketAPI()
client = TestClient(app)

chat_calls: int = 0
news_calls: int = 0


@app.channel("chat")
async def chat(message: str = "Welcome") -> dict[str, str]:
    global chat_calls
    chat_calls += 1
    return {"message": message}


@app.channel("news", default_response=False)
async def news() -> dict[str, str]:
    global news_calls
    news_calls += 1
    return {"headline": "Breaking News!"}


def test_subscribe_to_channel():
    global chat_calls
    assert "chat" in app._socket_manager.channels
    assert len(app._socket_manager.channels["chat"]) == 0

    with client.websocket_connect("/") as websocket:
        websocket.send_json({"type": "subscribe", "channel": "chat"})
        assert len(app._socket_manager.channels["chat"]) == 1
        response = websocket.receive_json()
        assert response == {"type": "subscribed", "channel": "chat"}
        response = websocket.receive_json()
        assert response == {
            "type": "data",
            "channel": "chat",
            "data": {"message": "Welcome"},
        }
    assert chat_calls == 1
    chat_calls = 0


def test_subscribe_to_channel_without_default_response():
    global news_calls
    with client.websocket_connect("/") as websocket:
        websocket.send_json({"type": "subscribe", "channel": "news"})
        response = websocket.receive_json()
        assert response == {"type": "subscribed", "channel": "news"}
    assert news_calls == 0


def test_subscribe_to_nonexistent_channel():
    with client.websocket_connect("/") as websocket:
        websocket.send_json({"type": "subscribe", "channel": "nonexistent"})
        response = websocket.receive_json()
        assert response.get("error") == "Channel 'nonexistent' not found."


def test_subscribe_to_channel_and_receive_some_data():
    global chat_calls
    with client.websocket_connect("/") as websocket:
        websocket.send_json({"type": "subscribe", "channel": "chat"})
        response = websocket.receive_json()
        assert response == {"type": "subscribed", "channel": "chat"}
        response = websocket.receive_json()
        assert response == {
            "type": "data",
            "channel": "chat",
            "data": {"message": "Welcome"},
        }
        asyncio.run(chat(message="Test Message"))
        response = websocket.receive_json()
        assert response == {
            "type": "data",
            "channel": "chat",
            "data": {"message": "Test Message"},
        }
    assert chat_calls == 2
    chat_calls = 0


def test_subscribe_to_channel_without_default_response_and_receive_some_data():
    global news_calls
    client = TestClient(app)

    with client.websocket_connect("/") as websocket:
        websocket.send_json({"type": "subscribe", "channel": "news"})
        response = websocket.receive_json()
        assert response == {"type": "subscribed", "channel": "news"}
        asyncio.run(news())
        response = websocket.receive_json()
        assert response == {
            "type": "data",
            "channel": "news",
            "data": {"headline": "Breaking News!"},
        }
    assert news_calls == 1
    news_calls = 0
