from socketapi import SocketAPI
from socketapi.testclient import TestClient

app = SocketAPI()
client = TestClient(app)

action_called: int = 0
action_with_result_called: int = 0


@app.action("test_action")
async def action() -> None:
    global action_called
    action_called += 1


@app.action("action_with_result")
async def action_with_result(value: int) -> int:
    global action_with_result_called
    action_with_result_called += 1
    return value * 2


def test_trigger_action():
    global action_called

    with client.websocket_connect("/") as websocket:
        websocket.send_json({"type": "action", "channel": "test_action"})
        response = websocket.receive_json()
        assert response == {
            "type": "action",
            "channel": "test_action",
            "status": "completed",
        }
        assert action_called == 1


def test_trigger_action_with_result():
    global action_with_result_called

    with client.websocket_connect("/") as websocket:
        websocket.send_json(
            {"type": "action", "channel": "action_with_result", "data": {"value": 5}}
        )
        response = websocket.receive_json()
        assert response == {
            "type": "action",
            "channel": "action_with_result",
            "status": "completed",
            "data": 10,
        }
        assert action_with_result_called == 1


def test_trigger_nonexistent_action():
    with client.websocket_connect("/") as websocket:
        websocket.send_json({"type": "action", "channel": "nonexistent_action"})
        response = websocket.receive_json()
        assert response == {"error": "Action 'nonexistent_action' not found."}
