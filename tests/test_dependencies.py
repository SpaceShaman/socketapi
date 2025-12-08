from typing import Annotated

from socketapi import Depends, SocketAPI
from socketapi.testclient import TestClient

app = SocketAPI()
client = TestClient(app)


async def common_dependency(a: int, b: str) -> str:
    return "dependency result"


@app.action("action_one")
async def action_one(
    dep: Annotated[str, Depends(common_dependency)],
) -> str:
    return dep


async def nested_dependency(
    x: Annotated[str, Depends(common_dependency)],
) -> dict[str, str]:
    return {"x": x}


@app.action("action_with_nested_dependency")
async def action_with_nested_dependency(
    dep: Annotated[dict[str, str], Depends(nested_dependency)],
) -> dict[str, str]:
    return dep


def test_action_with_dependency():
    with client.websocket_connect("/") as websocket:
        websocket.send_json(
            {
                "type": "action",
                "channel": "action_one",
                "data": {
                    "dep": {
                        "a": 42,
                        "b": "hello",
                    },
                },
            }
        )
        response = websocket.receive_json()
        assert response == {
            "type": "action",
            "channel": "action_one",
            "status": "completed",
            "data": "dependency result",
        }


def test_action_with_nested_dependency():
    with client.websocket_connect("/") as websocket:
        websocket.send_json(
            {
                "type": "action",
                "channel": "action_with_nested_dependency",
                "data": {
                    "dep": {
                        "x": {
                            "a": 100,
                            "b": "world",
                        },
                    },
                },
            }
        )
        response = websocket.receive_json()
        assert response == {
            "type": "action",
            "channel": "action_with_nested_dependency",
            "status": "completed",
            "data": {"x": "dependency result"},
        }
