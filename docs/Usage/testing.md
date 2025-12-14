# Testing

SocketAPI includes a built-in `TestClient` based on Starlette's test client, making it easy to test your WebSocket actions and channels.

## Basic Usage

```python
from socketapi import SocketAPI
from socketapi.testclient import TestClient

app = SocketAPI()

@app.action("calculate")
async def calculate(a: int, b: int) -> int:
    return a + b

@app.channel("notifications")
async def notifications(message: str):
    return {"message": message}

def test_action():
    client = TestClient(app)
    
    with client.websocket_connect("/") as websocket:
        # Send action request
        websocket.send_json({
            "type": "action",
            "channel": "calculate",
            "data": {"a": 5, "b": 3}
        })
        
        # Receive response
        response = websocket.receive_json()
        assert response["data"] == 8
        assert response["status"] == "completed"

def test_channel():
    client = TestClient(app)
    
    with client.websocket_connect("/") as websocket:
        # Subscribe to channel
        websocket.send_json({
            "type": "subscribe",
            "channel": "notifications"
        })
        
        # Receive subscription confirmation
        response = websocket.receive_json()
        assert response["type"] == "subscribed"
        assert response["channel"] == "notifications"
```

The `TestClient` provides a simple way to test your WebSocket endpoints without running a live server.
