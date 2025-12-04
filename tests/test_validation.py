from socketapi import SocketAPI
from socketapi.testclient import TestClient

app = SocketAPI()
client = TestClient(app)


@app.action("first_action")
async def first_action(x: int) -> int:
    return x + 1


def test_trigger_first_action_with_bad_parm_type():
    with client.websocket_connect("/") as websocket:
        websocket.send_json(
            {"type": "action", "channel": "first_action", "data": {"x": "not_an_int"}}
        )
        response = websocket.receive_json()
        assert response == {
            "type": "error",
            "message": "Invalid parameters for action 'first_action'",
        }
