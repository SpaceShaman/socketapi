from socketapi import Router, SocketAPI
from socketapi.testclient import TestClient

app = SocketAPI()
client = TestClient(app)

router = Router()


@router.channel("test_channel")
async def channel() -> dict[str, str]:
    return {"message": "Test Channel"}


app.include_router(router)


def test_subscribe_to_channel_from_router():
    with client.websocket_connect("/") as websocket:
        websocket.send_json({"type": "subscribe", "channel": "test_channel"})
        response = websocket.receive_json()
        assert response == {"type": "subscribed", "channel": "test_channel"}
        response = websocket.receive_json()
        assert response == {
            "type": "data",
            "channel": "test_channel",
            "data": {"message": "Test Channel"},
        }
