from socketapi import SocketAPI
from socketapi.testclient import TestClient

app = SocketAPI()

action_called: int = 0


@app.action("test_action")
async def action() -> None:
    global action_called
    action_called += 1


def test_trigger_action():
    global action_called
    client = TestClient(app)
    with client.websocket_connect("/") as websocket:
        websocket.send_json({"type": "action", "channel": "test_action"})
        response = websocket.receive_json()
        assert response == {
            "type": "action",
            "channel": "test_action",
            "status": "completed",
        }
        assert action_called == 1
