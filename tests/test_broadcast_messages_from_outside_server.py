import json
import multiprocessing
from time import sleep

import pytest
import uvicorn
import websockets

from socketapi import SocketAPI

app = SocketAPI()


@app.channel("broadcast_channel", default_response=False)
async def broadcast_channel(message: str) -> dict[str, str]:
    return {"message": message}


def run_server():
    uvicorn.run(app, host="0.0.0.0", port=8000)


@pytest.mark.asyncio
async def test_broadcast_messages_from_outside_server_context():
    server_process = multiprocessing.Process(target=run_server)
    server_process.start()
    sleep(1)  # Give the server time to start

    uri = "ws://localhost:8000/"
    try:
        async with websockets.connect(uri) as websocket:
            await websocket.send(
                json.dumps({"type": "subscribe", "channel": "broadcast_channel"})
            )
            response = json.loads(await websocket.recv())
            assert response == {"type": "subscribed", "channel": "broadcast_channel"}
            await broadcast_channel(message="Hello from outside!")
            response = json.loads(await websocket.recv())
            assert response == {
                "type": "data",
                "channel": "broadcast_channel",
                "data": {"message": "Hello from outside!"},
            }
    finally:
        server_process.terminate()
        server_process.join(timeout=5)
        if server_process.is_alive():
            server_process.kill()
