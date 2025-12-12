import asyncio
from typing import Any

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


@app.action("multiple_params_action")
async def multiple_params_action(a: int, b: str, c: dict[str, int]) -> dict[str, Any]:
    return {"a": a, "b": b, "c": c}


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
    action_called = 0


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
        assert response == {
            "type": "error",
            "message": "Action 'nonexistent_action' not found.",
        }


def test_trigger_action_with_multiple_params():
    with client.websocket_connect("/") as websocket:
        websocket.send_json(
            {
                "type": "action",
                "channel": "multiple_params_action",
                "data": {"a": 10, "b": "test", "c": {"key": 42}},
            }
        )
        response = websocket.receive_json()
        assert response == {
            "type": "action",
            "channel": "multiple_params_action",
            "status": "completed",
            "data": {"a": 10, "b": "test", "c": {"key": 42}},
        }


def test_trigger_action_with_missing_params():
    with client.websocket_connect("/") as websocket:
        websocket.send_json(
            {
                "type": "action",
                "channel": "multiple_params_action",
                "data": {"a": 10, "b": "test"},
            }
        )
        response = websocket.receive_json()
        assert response == {
            "type": "error",
            "message": "Invalid parameters for action 'multiple_params_action'",
        }


def test_trigger_action_by_calling_action_handler_directly():
    global action_called
    asyncio.run(action())

    assert action_called == 1
    action_called = 0
