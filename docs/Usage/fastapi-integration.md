# Integration with FastAPI

SocketAPI can be seamlessly integrated with FastAPI by creating a hybrid application that inherits from both frameworks. Since both SocketAPI and FastAPI inherit from Starlette, you can create a mixin class that combines their functionality.

## Why Integrate?

Combining SocketAPI with FastAPI allows you to:

- Serve traditional REST API endpoints alongside WebSocket-based real-time communication
- Build a complete full-stack application with a single server

## Basic Integration

Create a class that inherits from both FastAPI and SocketAPI:

```python
from fastapi import FastAPI
from socketapi import SocketAPI

class HybridAPI(SocketAPI, FastAPI):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, *kwargs)

app = HybridAPI(title="My Hybrid API", version="1.0.0")

# Define REST endpoints using FastAPI decorators
@app.get("/")
async def root():
    return {"message": "Hello from FastAPI!"}

@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id, "name": "Item"}

# Define WebSocket actions and channels using SocketAPI decorators
@app.action("calculate")
async def calculate(a: int, b: int):
    return {"result": a + b}

@app.channel("notifications")
async def notifications(message: str = "Welcome"):
    return {"message": message}
```

## Running the Hybrid Application

Start the server with Uvicorn:

```bash
uvicorn main:app --reload
```

Now you have:
- REST API available at `http://localhost:8000/`
- WebSocket API available at `ws://localhost:8000/`
- OpenAPI documentation at `http://localhost:8000/docs`

## Real-World Example: Chat Application

Here's a complete example of a chat application with both REST and WebSocket endpoints:

```python
from datetime import datetime
from typing import Annotated

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from socketapi import RequiredOnSubscribe, SocketAPI

class HybridAPI(SocketAPI, FastAPI):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

app = HybridAPI(
    title="Chat Application API",
    description="REST and WebSocket API for chat",
    version="1.0.0"
)

# Pydantic models
class User(BaseModel):
    id: int
    username: str
    email: str

class Message(BaseModel):
    user: str
    text: str
    timestamp: datetime

class CreateMessage(BaseModel):
    user_id: int
    text: str

# In-memory storage (use a database in production)
users_db: dict[int, User] = {
    1: User(id=1, username="alice", email="alice@example.com"),
    2: User(id=2, username="bob", email="bob@example.com"),
}

messages_db: list[Message] = []

# REST Endpoints
@app.get("/")
async def root():
    return {
        "message": "Chat Application API",
        "endpoints": {
            "rest": "http://localhost:8000/docs",
            "websocket": "ws://localhost:8000/"
        }
    }

@app.get("/users", response_model=list[User])
async def list_users():
    """Get all users"""
    return list(users_db.values())

@app.get("/users/{user_id}", response_model=User)
async def get_user(user_id: int):
    """Get a specific user"""
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    return users_db[user_id]

@app.get("/messages", response_model=list[Message])
async def get_messages(limit: int = 50):
    """Get recent chat messages"""
    return messages_db[-limit:]

@app.post("/messages", response_model=Message)
async def create_message_rest(message: CreateMessage):
    """Create a new message via REST (also broadcasts to WebSocket subscribers)"""
    if message.user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    user = users_db[message.user_id]
    msg = Message(
        user=user.username,
        text=message.text,
        timestamp=datetime.now()
    )
    messages_db.append(msg)
    
    # Broadcast to WebSocket subscribers
    await chat_channel(
        user=msg.user,
        text=msg.text,
        timestamp=msg.timestamp.isoformat()
    )
    
    return msg

# WebSocket Channels and Actions
@app.channel("chat")
async def chat_channel(user: str, text: str, timestamp: str):
    """Real-time chat channel"""
    return {
        "user": user,
        "text": text,
        "timestamp": timestamp
    }

@app.channel("user_status")
async def user_status_channel(
    user_id: Annotated[int, RequiredOnSubscribe]
):
    """Subscribe to a user's online status"""
    if user_id not in users_db:
        return {"error": "User not found"}
    return {
        "user_id": user_id,
        "username": users_db[user_id].username,
        "status": "online"
    }

@app.action("send_message")
async def send_message(user_id: int, text: str):
    """Send a message via WebSocket"""
    if user_id not in users_db:
        return {"error": "User not found"}
    
    user = users_db[user_id]
    msg = Message(
        user=user.username,
        text=text,
        timestamp=datetime.now()
    )
    messages_db.append(msg)
    
    # Broadcast to all chat subscribers
    await chat_channel(
        user=msg.user,
        text=msg.text,
        timestamp=msg.timestamp.isoformat()
    )
    
    return {
        "success": True,
        "message_id": len(messages_db) - 1
    }

@app.action("typing")
async def typing_indicator(user_id: int, is_typing: bool):
    """Broadcast typing indicator"""
    if user_id not in users_db:
        return {"error": "User not found"}
    
    user = users_db[user_id]
    await user_status_channel(user_id=user_id)
    
    return {"success": True}
```

## Usage Examples

### REST API Usage

Get all users:
```bash
curl http://localhost:8000/users
```

Get messages:
```bash
curl http://localhost:8000/messages?limit=10
```

Create a message via REST:
```bash
curl -X POST http://localhost:8000/messages \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "text": "Hello from REST!"}'
```

### WebSocket API Usage

Subscribe to chat:
```json
{"type": "subscribe", "channel": "chat"}
```

Send a message:
```json
{
    "type": "action",
    "channel": "send_message",
    "data": {"user_id": 1, "text": "Hello from WebSocket!"}
}
```

Subscribe to user status with authentication:
```json
{
    "type": "subscribe",
    "channel": "user_status",
    "data": {"user_id": 1}
}
```

## Sharing Configuration

You can share middleware, CORS settings, and other configuration between FastAPI and SocketAPI:

```python
from fastapi.middleware.cors import CORSMiddleware

class HybridAPI(SocketAPI, FastAPI):
    def __init__(self, *args, **kwargs):
        SocketAPI.__init__(self)
        FastAPI.__init__(self, *args, routes=self.routes, **kwargs)

app = HybridAPI(
    title="My API",
    version="1.0.0",
)

# Add CORS middleware (applies to both REST and WebSocket)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Custom WebSocket Path

By default, SocketAPI uses `/` as the WebSocket endpoint. You can customize this:

```python
from starlette.routing import WebSocketRoute

class HybridAPI(SocketAPI, FastAPI):
    def __init__(self, *args, websocket_path: str = "/ws", **kwargs):
        # Don't call SocketAPI.__init__ to avoid creating default route
        self._socket_manager = SocketManager()
        
        # Create custom WebSocket route
        ws_route = WebSocketRoute(websocket_path, self._websocket_endpoint)
        
        # Initialize FastAPI with custom routes
        FastAPI.__init__(self, *args, routes=[ws_route], **kwargs)

app = HybridAPI(
    title="My API",
    websocket_path="/ws"  # WebSocket now at ws://localhost:8000/ws
)

@app.get("/")
async def root():
    return {"message": "REST endpoint"}

@app.action("ping")
async def ping():
    return {"pong": True}
```

## Testing

You can test both REST and WebSocket endpoints:

```python
from fastapi.testclient import TestClient

def test_rest_endpoint():
    client = TestClient(app)
    response = client.get("/users")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_websocket_action():
    client = TestClient(app)
    with client.websocket_connect("/") as websocket:
        websocket.send_json({
            "type": "action",
            "channel": "send_message",
            "data": {"user_id": 1, "text": "Test"}
        })
        response = websocket.receive_json()
        assert response["type"] == "action"
        assert response["status"] == "completed"
        assert response["data"]["success"] is True
```

## Best Practices

1. **Separation of Concerns**: Use REST for CRUD operations and WebSocket for real-time updates
2. **Shared Business Logic**: Extract shared logic into separate functions that both REST and WebSocket handlers can call
3. **Authentication**: Implement authentication for both REST (JWT tokens) and WebSocket (token in subscribe data)
4. **Error Handling**: Use FastAPI's exception handlers for REST and SocketAPI's error messages for WebSocket
5. **Documentation**: Document REST endpoints with FastAPI's automatic OpenAPI, and WebSocket protocol separately

## Advantages

✅ Single server for both REST and WebSocket  
✅ Shared middleware and configuration  
✅ Automatic OpenAPI documentation for REST endpoints  
✅ Type-safe with Pydantic models  
✅ Easy to test both protocols  
✅ Reduced complexity in deployment  

## Limitations

⚠️ SocketAPI's WebSocket endpoint cannot be documented in OpenAPI  
⚠️ FastAPI's dependency injection doesn't work with SocketAPI decorators  
⚠️ Requires understanding of both frameworks  

## Alternative: Mount as Sub-application

If you prefer to keep them separate, you can mount SocketAPI as a sub-application:

```python
from fastapi import FastAPI
from socketapi import SocketAPI

# Create separate apps
rest_app = FastAPI(title="REST API")
socket_app = SocketAPI()

# Define REST endpoints
@rest_app.get("/")
async def root():
    return {"message": "REST API"}

# Define WebSocket endpoints
@socket_app.action("ping")
async def ping():
    return {"pong": True}

# Mount SocketAPI under /ws
rest_app.mount("/ws", socket_app)
```

This approach keeps them separate but runs on the same server:
- REST API: `http://localhost:8000/`
- WebSocket API: `ws://localhost:8000/ws/`
