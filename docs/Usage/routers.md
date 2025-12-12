# Routers

Routers in SocketAPI allow you to organize your application into logical groups and split your code across multiple files. This is particularly useful for large applications where you want to separate concerns and maintain a clean project structure.

## Basic Router Usage

Create a router and define channels and actions on it:

```python
from socketapi import Router, SocketAPI

app = SocketAPI()
router = Router()

@router.channel("notifications")
async def notifications(message: str = "No new notifications"):
    return {"message": message}

@router.action("mark_as_read")
async def mark_as_read(notification_id: int):
    return {"id": notification_id, "read": True}

# Include the router in your app
app.include_router(router)
```

## Organizing Multiple Files

For larger applications, split your routers into separate files:

### Project Structure

```
my_app/
├── main.py
├── routers/
│   ├── __init__.py
│   ├── users.py
│   ├── chat.py
│   └── notifications.py
```

### routers/users.py

```python
from socketapi import Router
from pydantic import BaseModel

router = Router()

class User(BaseModel):
    id: int
    username: str
    email: str

@router.channel("user_status")
async def user_status(user_id: int, status: str = "online"):
    return {"user_id": user_id, "status": status}

@router.action("get_user")
async def get_user(user_id: int) -> User:
    # Fetch user from database
    return User(id=user_id, username="john_doe", email="john@example.com")

@router.action("update_status")
async def update_status(user_id: int, status: str):
    # Update user status in database
    await user_status(user_id=user_id, status=status)
    return {"success": True}
```

### routers/chat.py

```python
from socketapi import Router
from pydantic import BaseModel
from typing import Annotated
from socketapi import RequiredOnSubscribe

router = Router()

class Message(BaseModel):
    user: str
    text: str
    room: str

@router.channel("chat_room")
async def chat_room(
    room_id: Annotated[str, RequiredOnSubscribe],
    message: Message | None = None
):
    if message:
        return message
    return {"room": room_id, "text": "Welcome to the chat room!"}

@router.action("send_message")
async def send_message(message: Message):
    # Save message to database
    await chat_room(room_id=message.room, message=message)
    return {"sent": True}

@router.action("get_history")
async def get_history(room_id: str, limit: int = 50):
    # Fetch chat history from database
    return {"room": room_id, "messages": []}
```

### routers/notifications.py

```python
from socketapi import Router
from typing import Annotated
from socketapi import RequiredOnSubscribe

router = Router()

@router.channel("notifications", default_response=False)
async def notifications(
    user_id: Annotated[int, RequiredOnSubscribe],
    notification_type: str = "all"
):
    return {
        "user_id": user_id,
        "type": notification_type,
        "count": 0
    }

@router.action("notify_user")
async def notify_user(user_id: int, message: str, notification_type: str = "info"):
    # Send notification to user
    await notifications(user_id=user_id, notification_type=notification_type)
    return {"notified": True}
```

### main.py

```python
from socketapi import SocketAPI
from routers import users, chat, notifications

app = SocketAPI()

# Include all routers
app.include_router(users.router)
app.include_router(chat.router)
app.include_router(notifications.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Cross-Router Communication

Routers can interact with each other. You can call channel functions from different routers:

### routers/analytics.py

```python
from socketapi import Router

router = Router()

@router.channel("analytics")
async def analytics(event: str, data: dict):
    return {"event": event, "data": data}
```

### routers/orders.py

```python
from socketapi import Router
from .analytics import analytics

router = Router()

@router.action("create_order")
async def create_order(product_id: int, quantity: int):
    # Create order in database
    order_id = 12345
    
    # Track analytics event
    await analytics(
        event="order_created",
        data={"order_id": order_id, "product_id": product_id, "quantity": quantity}
    )
    
    return {"order_id": order_id, "status": "created"}
```

---

Routers make no difference from the client's perspective - all channels and actions are available at the root level, regardless of which router they're defined in.
