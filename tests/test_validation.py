from pydantic import BaseModel

from socketapi import SocketAPI
from socketapi.testclient import TestClient

app = SocketAPI()
client = TestClient(app)


@app.action("simple_action")
async def simple_action(x: int) -> int:
    return x + 1


class DataModel(BaseModel):
    x: int
    y: str


class ComplexDataModel(BaseModel):
    a: int
    b: str
    c: DataModel


@app.action("complex_action")
async def complex_action(complex_data: ComplexDataModel) -> dict[str, str]:
    complex_data.a
    return {"test": "success"}


@app.action("action_without_params_type")
async def action_without_params_type(any_data):  # type: ignore
    return any_data  # type: ignore


def test_trigger_first_action_with_bad_parm_type():
    with client.websocket_connect("/") as websocket:
        websocket.send_json(
            {"type": "action", "channel": "simple_action", "data": {"x": "not_an_int"}}
        )
        response = websocket.receive_json()
        assert response == {
            "type": "error",
            "message": "Invalid parameters for action 'simple_action'",
        }


def test_trigger_first_action_with_number_as_string():
    with client.websocket_connect("/") as websocket:
        websocket.send_json(
            {"type": "action", "channel": "simple_action", "data": {"x": "5"}}
        )
        response = websocket.receive_json()
        assert response == {
            "type": "action",
            "channel": "simple_action",
            "status": "completed",
            "data": 6,
        }


def test_trigger_complex_action_with_correct_data():
    with client.websocket_connect("/") as websocket:
        websocket.send_json(
            {
                "type": "action",
                "channel": "complex_action",
                "data": {
                    "complex_data": {
                        "a": 10,
                        "b": "test",
                        "c": {"x": 1, "y": "value"},
                    }
                },
            }
        )
        response = websocket.receive_json()
        assert response == {
            "type": "action",
            "channel": "complex_action",
            "status": "completed",
            "data": {"test": "success"},
        }


def test_trigger_complex_action_with_incorrect_data():
    with client.websocket_connect("/") as websocket:
        websocket.send_json(
            {
                "type": "action",
                "channel": "complex_action",
                "data": {
                    "complex_data": {
                        "a": "not_an_int",
                        "b": "test",
                        "c": {"x": 1, "y": "value"},
                    }
                },
            }
        )
        response = websocket.receive_json()
        assert response == {
            "type": "error",
            "message": "Invalid parameters for action 'complex_action'",
        }


def test_trigger_action_without_params_type():
    with client.websocket_connect("/") as websocket:
        websocket.send_json(
            {
                "type": "action",
                "channel": "action_without_params_type",
                "data": {"any_data": {"key": "value"}},
            }
        )
        response = websocket.receive_json()
        assert response == {
            "type": "action",
            "channel": "action_without_params_type",
            "status": "completed",
            "data": {"key": "value"},
        }
