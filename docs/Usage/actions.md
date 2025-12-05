# Actions

Actions in SocketAPI implement a request-response pattern similar to REST API endpoints. When you decorate a function with `@app.action()`, it becomes an endpoint that clients can call and receive a response.

## Basic Action Definition

```python
from socketapi import SocketAPI

app = SocketAPI()

@app.action("greet")
async def greet(name: str):
    return {"message": f"Hello, {name}!"}
```

This creates an action named `"greet"` that clients can invoke.

## Calling an Action

Clients call an action by sending a message with `type: "action"`:

Send:
```json
{
    "type": "action",
    "channel": "greet",
    "data": {"name": "Alice"}
}
```

Receive:
```json
{
    "type": "action",
    "channel": "greet",
    "status": "completed",
    "data": {"message": "Hello, Alice!"}
}
```

## Actions Without Parameters

You can define actions that don't require any parameters:

```python
@app.action("ping")
async def ping():
    return {"status": "ok"}
```

Send:
```json
{"type": "action", "channel": "ping"}
```

Receive:
```json
{
    "type": "action",
    "channel": "ping",
    "status": "completed",
    "data": {"status": "ok"}
}
```

## Actions Without Return Value

Actions can perform operations without returning data:

```python
@app.action("log_event")
async def log_event(event: str):
    print(f"Event logged: {event}")
    # No return statement
```

Send:
```json
{
    "type": "action",
    "channel": "log_event",
    "data": {"event": "user_login"}
}
```

Receive (no `data` field):
```json
{
    "type": "action",
    "channel": "log_event",
    "status": "completed"
}
```

## Multiple Parameters

Actions support multiple typed parameters:

```python
@app.action("calculate")
async def calculate(a: int, b: int, operation: str):
    if operation == "add":
        result = a + b
    elif operation == "multiply":
        result = a * b
    else:
        result = 0
    return {"result": result}
```

Send:
```json
{
    "type": "action",
    "channel": "calculate",
    "data": {"a": 5, "b": 3, "operation": "add"}
}
```

Receive:
```json
{
    "type": "action",
    "channel": "calculate",
    "status": "completed",
    "data": {"result": 8}
}
```

## Data Validation

SocketAPI uses Pydantic for automatic parameter validation. If parameters are missing or have incorrect types, an error is returned:

Missing parameter:

Send:
```json
{
    "type": "action",
    "channel": "calculate",
    "data": {"a": 5, "b": 3}
}
```

Receive:
```json
{
    "type": "error",
    "message": "Invalid parameters for action 'calculate'"
}
```

Incorrect type:

Send:
```json
{
    "type": "action",
    "channel": "calculate",
    "data": {"a": "not_a_number", "b": 3, "operation": "add"}
}
```

Receive:
```json
{
    "type": "error",
    "message": "Invalid parameters for action 'calculate'"
}
```

Note: Pydantic performs type coercion when possible. For example, `"5"` (string) can be converted to `5` (int).

## Using Pydantic Models

For complex data structures, you can use Pydantic models:

```python
from pydantic import BaseModel

class UserData(BaseModel):
    username: str
    email: str
    age: int

class UserResponse(BaseModel):
    id: int
    username: str
    created: bool

@app.action("create_user")
async def create_user(user: UserData) -> UserResponse:
    # Create user in database
    return UserResponse(id=1, username=user.username, created=True)
```

Send:
```json
{
    "type": "action",
    "channel": "create_user",
    "data": {
        "user": {
            "username": "alice",
            "email": "alice@example.com",
            "age": 25
        }
    }
}
```

Receive:
```json
{
    "type": "action",
    "channel": "create_user",
    "status": "completed",
    "data": {
        "id": 1,
        "username": "alice",
        "created": true
    }
}
```

## Nested Pydantic Models

You can use nested models for more complex structures:

```python
from pydantic import BaseModel

class Address(BaseModel):
    street: str
    city: str
    zipcode: str

class UserProfile(BaseModel):
    name: str
    email: str
    address: Address

@app.action("update_profile")
async def update_profile(profile: UserProfile):
    # Update user profile
    return {"success": True, "name": profile.name}
```

Send:
```json
{
    "type": "action",
    "channel": "update_profile",
    "data": {
        "profile": {
            "name": "Alice",
            "email": "alice@example.com",
            "address": {
                "street": "123 Main St",
                "city": "Springfield",
                "zipcode": "12345"
            }
        }
    }
}
```

## Returning Pydantic Models

When you return a Pydantic model, it's automatically serialized to JSON:

```python
class Product(BaseModel):
    id: int
    name: str
    price: float

@app.action("get_product")
async def get_product(product_id: int) -> Product:
    return Product(id=product_id, name="Widget", price=9.99)
```

Receive:
```json
{
    "type": "action",
    "channel": "get_product",
    "status": "completed",
    "data": {
        "id": 1,
        "name": "Widget",
        "price": 9.99
    }
}
```

## Combining Actions with Channels

Actions are commonly used to broadcast data to channels:

```python
@app.channel("chat")
async def chat_channel(message: str):
    return {"message": message}

@app.action("send_message")
async def send_message(text: str, user: str):
    # Broadcast to all chat subscribers
    await chat_channel(message=f"{user}: {text}")
    return {"sent": True}
```

When a client calls the action:

Send:
```json
{
    "type": "action",
    "channel": "send_message",
    "data": {"text": "Hello everyone!", "user": "Alice"}
}
```

The calling client receives:
```json
{
    "type": "action",
    "channel": "send_message",
    "status": "completed",
    "data": {"sent": true}
}
```

All subscribers to the "chat" channel receive:
```json
{
    "type": "data",
    "channel": "chat",
    "data": {"message": "Alice: Hello everyone!"}
}
```

## Error Handling

If a client tries to call a non-existent action:

Send:
```json
{"type": "action", "channel": "nonexistent_action"}
```

Receive:
```json
{
    "type": "error",
    "message": "Action 'nonexistent_action' not found."
}
```

## Complete Example

```python
from pydantic import BaseModel
from socketapi import SocketAPI

app = SocketAPI()

class Message(BaseModel):
    user: str
    text: str

class MessageResponse(BaseModel):
    id: int
    timestamp: int
    sent: bool

@app.channel("chat_room")
async def chat_room(message: Message):
    return message

@app.action("post_message")
async def post_message(message: Message) -> MessageResponse:
    # Save message to database
    import time
    message_id = 1
    timestamp = int(time.time())
    
    # Broadcast to all chat room subscribers
    await chat_room(message=message)
    
    # Return confirmation to sender
    return MessageResponse(id=message_id, timestamp=timestamp, sent=True)

@app.action("get_history")
async def get_history(limit: int = 10) -> dict[str, list]:
    # Fetch chat history from database
    return {"messages": []}
```

Client workflow:

1. Call action to post a message:
```json
{
    "type": "action",
    "channel": "post_message",
    "data": {
        "message": {
            "user": "Alice",
            "text": "Hello!"
        }
    }
}
```

2. Receive confirmation:
```json
{
    "type": "action",
    "channel": "post_message",
    "status": "completed",
    "data": {
        "id": 1,
        "timestamp": 1701234567,
        "sent": true
    }
}
```

3. All subscribers to "chat_room" receive:
```json
{
    "type": "data",
    "channel": "chat_room",
    "data": {
        "user": "Alice",
        "text": "Hello!"
    }
}
```

4. Get chat history:
```json
{
    "type": "action",
    "channel": "get_history",
    "data": {"limit": 20}
}
```
