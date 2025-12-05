# Channels

Channels in SocketAPI implement a publish/subscribe pattern, allowing clients to subscribe to real-time data streams. When you decorate a function with `@app.channel()`, it becomes a broadcasting endpoint that can push data to all subscribed clients.

## Basic Channel Definition

```python
from socketapi import SocketAPI

app = SocketAPI()

@app.channel("chat")
async def chat_channel(message: str = "Welcome"):
    return {"message": message}
```

This creates a channel named `"chat"` that clients can subscribe to.

## Subscribing to a Channel

Clients subscribe by sending a message with `type: "subscribe"`:

Send:
```json
{"type": "subscribe", "channel": "chat"}
```

Receive confirmation:
```json
{"type": "subscribed", "channel": "chat"}
```

By default, clients automatically receive initial data after subscribing:
```json
{"type": "data", "channel": "chat", "data": {"message": "Welcome"}}
```

## Unsubscribing from a Channel

Clients can unsubscribe at any time:

Send:
```json
{"type": "unsubscribe", "channel": "chat"}
```

Receive:
```json
{"type": "unsubscribed", "channel": "chat"}
```

When a WebSocket connection closes, clients are automatically unsubscribed from all channels.

## Broadcasting Messages

Once a channel is defined, you can broadcast messages to all subscribers by calling the decorated function:

```python
@app.channel("chat")
async def chat_channel(message: str):
    return {"message": message}

@app.action("send_message")
async def send_message(text: str):
    # Broadcast to all subscribers of the "chat" channel
    await chat_channel(message=text)
```

All subscribers will receive:
```json
{"type": "data", "channel": "chat", "data": {"message": "text from action"}}
```

## Default Response Behavior

By default, channels send initial data immediately after a client subscribes. You can disable this behavior:

```python
@app.channel("news", default_response=False)
async def news_channel():
    return {"headline": "Breaking News!"}
```

Send:
```json
{"type": "subscribe", "channel": "news"}
```

Receive only confirmation (no initial data):
```json
{"type": "subscribed", "channel": "news"}
```

The client will only receive data when you explicitly call the channel function:

```python
@app.action("publish_news")
async def publish_news():
    await news_channel()  # Now all subscribers receive the data
```

## Parameters and Validation

Channels support typed parameters with automatic validation using Pydantic:

```python
@app.channel("user_updates")
async def user_updates(user_id: int, include_details: bool = True):
    # Fetch user data based on parameters
    return {"user_id": user_id, "details": include_details}
```

When broadcasting, pass parameters as keyword arguments:

```python
await user_updates(user_id=123, include_details=False)
```

## Required Parameters on Subscribe

You can require clients to provide parameters when subscribing using the `RequiredOnSubscribe` annotation:

```python
from typing import Annotated
from socketapi import RequiredOnSubscribe, SocketAPI

app = SocketAPI()

@app.channel("private_chat")
async def private_chat(
    token: Annotated[str, RequiredOnSubscribe],
    message: str = "Welcome"
):
    # Validate token, fetch user data, etc.
    return {"message": message, "authenticated": True}
```

Clients must provide required parameters when subscribing:

Send:
```json
{
    "type": "subscribe",
    "channel": "private_chat",
    "data": {"token": "secret_token"}
}
```

Receive:
```json
{"type": "subscribed", "channel": "private_chat"}
```

Then receive initial data:
```json
{
    "type": "data",
    "channel": "private_chat",
    "data": {"message": "Welcome", "authenticated": true}
}
```

If required parameters are missing or invalid:

Send:
```json
{"type": "subscribe", "channel": "private_chat"}
```

Receive error:
```json
{
    "type": "error",
    "message": "Invalid parameters for action 'private_chat'"
}
```

## Using Pydantic Models

You can use Pydantic models for complex data structures:

```python
from pydantic import BaseModel

class ChatMessage(BaseModel):
    user: str
    text: str
    timestamp: int

@app.channel("typed_chat")
async def typed_chat(message: ChatMessage = ChatMessage(user="system", text="Welcome", timestamp=0)):
    return message
```

## Error Handling

If a client tries to subscribe to a non-existent channel:

Send:
```json
{"type": "subscribe", "channel": "nonexistent"}
```

Receive:
```json
{
    "type": "error",
    "message": "Channel 'nonexistent' not found."
}
```

## Complete Example

```python
from typing import Annotated
from socketapi import RequiredOnSubscribe, SocketAPI

app = SocketAPI()

@app.channel("notifications")
async def notifications(user_id: Annotated[int, RequiredOnSubscribe], notification_type: str = "all"):
    # Fetch notifications for the user
    return {
        "user_id": user_id,
        "type": notification_type,
        "notifications": []
    }

@app.action("send_notification")
async def send_notification(user_id: int, message: str):
    # Broadcast notification to specific user's subscribers
    await notifications(user_id=user_id, notification_type="alert")
```

Client workflow:

1. Subscribe with required parameters:
```json
{"type": "subscribe", "channel": "notifications", "data": {"user_id": 123}}
```

2. Receive confirmation and initial data:
```json
{"type": "subscribed", "channel": "notifications"}
{"type": "data", "channel": "notifications", "data": {"user_id": 123, "type": "all", "notifications": []}}
```

3. Receive broadcasts when `send_notification` is called:
```json
{"type": "data", "channel": "notifications", "data": {"user_id": 123, "type": "alert", "notifications": []}}
```

1. Unsubscribe when done:
```json
{"type": "unsubscribe", "channel": "notifications"}
```

