from typing import Annotated, Any

from socketapi import Depends, SocketAPI
from socketapi.testclient import TestClient

app = SocketAPI()
client = TestClient(app)


async def common_dependency(a: int, b: str) -> str:
    return "dependency result"


@app.action("action_one")
async def action_one(
    dep: Annotated[dict[str, Any], Depends(common_dependency)],
) -> dict[str, Any]:
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
