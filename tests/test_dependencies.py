from typing import Annotated, Any

from pydantic import BaseModel

from socketapi import Depends, SocketAPI
from socketapi.annotations import RequiredOnSubscribe
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


class Address(BaseModel):
    street: str
    city: str
    zip_code: str


class ComplexDataModel(BaseModel):
    name: str
    value: int
    address: Address


async def complex_data_dependency(complex_data: ComplexDataModel) -> ComplexDataModel:
    complex_data.value += 10
    return complex_data


@app.action("action_with_complex_data_dependency")
async def action_with_complex_data_dependency(
    dep: Annotated[ComplexDataModel, Depends(complex_data_dependency)],
) -> ComplexDataModel:
    return dep


@app.action("action_with_multiple_dependencies")
async def action_with_multiple_dependencies(
    dep1: Annotated[str, Depends(common_dependency)],
    dep2: Annotated[dict[str, str], Depends(nested_dependency)],
) -> dict[str, Any]:
    return {
        "dep1": dep1,
        "dep2": dep2,
    }


@app.channel("channel_with_dependency", default_response=True)
async def channel_with_dependency(
    dep: Annotated[str, Depends(common_dependency), RequiredOnSubscribe],
) -> str:
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


def test_action_with_complex_data_dependency():
    with client.websocket_connect("/") as websocket:
        websocket.send_json(
            {
                "type": "action",
                "channel": "action_with_complex_data_dependency",
                "data": {
                    "dep": {
                        "complex_data": {
                            "name": "Test",
                            "value": 5,
                            "address": {
                                "street": "123 Main St",
                                "city": "Anytown",
                                "zip_code": "12345",
                            },
                        },
                    },
                },
            }
        )
        response = websocket.receive_json()
        assert response == {
            "type": "action",
            "channel": "action_with_complex_data_dependency",
            "status": "completed",
            "data": {
                "name": "Test",
                "value": 15,
                "address": {
                    "street": "123 Main St",
                    "city": "Anytown",
                    "zip_code": "12345",
                },
            },
        }


def test_action_with_multiple_dependencies():
    with client.websocket_connect("/") as websocket:
        websocket.send_json(
            {
                "type": "action",
                "channel": "action_with_multiple_dependencies",
                "data": {
                    "dep1": {
                        "a": 7,
                        "b": "foo",
                    },
                    "dep2": {
                        "x": {
                            "a": 21,
                            "b": "bar",
                        },
                    },
                },
            }
        )
        response = websocket.receive_json()
        assert response == {
            "type": "action",
            "channel": "action_with_multiple_dependencies",
            "status": "completed",
            "data": {
                "dep1": "dependency result",
                "dep2": {"x": "dependency result"},
            },
        }


def test_channel_with_dependency():
    with client.websocket_connect("/") as websocket:
        websocket.send_json(
            {
                "type": "subscribe",
                "channel": "channel_with_dependency",
                "data": {
                    "dep": {
                        "a": 55,
                        "b": "baz",
                    },
                },
            }
        )
        response = websocket.receive_json()
        assert response == {
            "type": "subscribed",
            "channel": "channel_with_dependency",
        }
        response = websocket.receive_json()
        assert response == {
            "type": "data",
            "channel": "channel_with_dependency",
            "data": "dependency result",
        }
