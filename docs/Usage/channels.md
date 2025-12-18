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

By default, clients do **not** receive initial data automatically after subscribing. They only receive the confirmation message. To enable automatic initial data delivery, use `default_response=True`.

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

By default, channels do **not** send initial data immediately after a client subscribes. You can enable this behavior by setting `default_response=True`:

```python
@app.channel("news", default_response=True)
async def news_channel():
    return {"headline": "Breaking News!"}
```

Send:
```json
{"type": "subscribe", "channel": "news"}
```

Receive confirmation and initial data:
```json
{"type": "subscribed", "channel": "news"}
{"type": "data", "channel": "news", "data": {"headline": "Breaking News!"}}
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

**Note:** By default, no initial data is sent automatically. To receive initial data after subscribing, set `default_response=True` on the channel decorator.

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

## Broadcasting from Outside Server Context

One of the most powerful features of SocketAPI channels is the ability to call channel functions from **outside the server context** - even from different processes or threads. This makes it incredibly useful for integrating with other technologies that run in separate processes.

### Use Cases

- **Background tasks**: Celery workers, RQ jobs, or other task queues
- **Database triggers**: PostgreSQL NOTIFY/LISTEN or other database events
- **External services**: Webhooks, message queues (RabbitMQ, Redis), or third-party APIs
- **Scheduled jobs**: Cron jobs or APScheduler tasks
- **Separate processes**: Any Python process that has access to your SocketAPI app instance

### How It Works

Channel functions work seamlessly regardless of where they're called from. When called from outside the WebSocket request context, SocketAPI automatically handles broadcasting to all subscribed clients.

```python
from socketapi import SocketAPI

app = SocketAPI()

@app.channel("broadcast_channel")
async def broadcast_channel(message: str):
    return {"message": message}

# This works from anywhere - inside actions, background tasks, or external processes
async def external_process():
    # Call from a completely different context
    await broadcast_channel(message="Hello from external process!")
```


### Custom Host and Port Configuration

If the server is running on a different host than `localhost` or a different port than `8000`, you need to provide these details when creating the SocketAPI object so that other processes know the server address and can communicate with it:

```python
from socketapi import SocketAPI

# Server running on custom host and/or port
app = SocketAPI(host="192.168.1.100", port=9000)

# Now external processes can broadcast to this server
```

If the server is running on the default host (`localhost`) and port (`8000`), no additional configuration is needed.

### Important Notes

- Channel functions are **thread-safe** and **process-safe**
- No special configuration needed - it just works!
- All subscribed clients receive broadcasts regardless of where the function is called
- Parameters are validated the same way as when called from actions
- Works with both sync and async contexts

!!! note "Broadcasting from a Different Machine"
    By default, the broadcast endpoint only accepts connections from localhost (`127.0.0.1`, `::1`, `localhost`) for security reasons. If you need to call channel functions from a different machine or server, you must explicitly configure `broadcast_allowed_hosts` when creating the SocketAPI instance:
    
    ```python
    app = SocketAPI(
        host="0.0.0.0",
        port=8000,
        broadcast_allowed_hosts=("127.0.0.1", "::1", "localhost", "192.168.1.50")
    )
    ```
    
    Add the IP address of the machine that needs to communicate with the server to the `broadcast_allowed_hosts` tuple.

This feature makes SocketAPI perfect for building real-time applications that need to integrate with existing infrastructure and external services.

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

2. Receive confirmation (no initial data by default):
```json
{"type": "subscribed", "channel": "notifications"}
```

3. Receive broadcasts when `send_notification` is called:
```json
{"type": "data", "channel": "notifications", "data": {"user_id": 123, "type": "alert", "notifications": []}}
```

1. Unsubscribe when done:
```json
{"type": "unsubscribe", "channel": "notifications"}
```

