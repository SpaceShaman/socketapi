# Dependencies

Dependencies in SocketAPI allow you to inject reusable logic into your actions and channels. Using the `Depends` function with Python's `Annotated` type hints, you can create shared functionality like authentication, database connections, or data processing that can be reused across multiple endpoints.

## Basic Dependency Definition

```python
from typing import Annotated
from socketapi import Depends, SocketAPI

app = SocketAPI()

async def common_dependency(a: int, b: str) -> str:
    return "dependency result"

@app.action("greet")
async def greet(dep: Annotated[str, Depends(common_dependency)]):
    return {"message": dep}
```

This creates a dependency function `common_dependency` that can be injected into any action or channel.

## Using Dependencies in Actions

When you use a dependency in an action, clients must provide the dependency's parameters within the action call:

Send:
```json
{
    "type": "action",
    "channel": "greet",
    "data": {
        "dep": {
            "a": 42,
            "b": "hello"
        }
    }
}
```

Receive:
```json
{
    "type": "action",
    "channel": "greet",
    "status": "completed",
    "data": {"message": "dependency result"}
}
```

The dependency function `common_dependency` receives the parameters `a` and `b` from the nested `dep` object in the request data.

## Nested Dependencies

Dependencies can depend on other dependencies, creating a chain of reusable components:

```python
async def common_dependency(a: int, b: str) -> str:
    return "dependency result"

async def nested_dependency(
    x: Annotated[str, Depends(common_dependency)]
) -> dict[str, str]:
    return {"x": x}

@app.action("process")
async def process(
    dep: Annotated[dict[str, str], Depends(nested_dependency)]
) -> dict[str, str]:
    return dep
```

Send:
```json
{
    "type": "action",
    "channel": "process",
    "data": {
        "dep": {
            "x": {
                "a": 100,
                "b": "world"
            }
        }
    }
}
```

Receive:
```json
{
    "type": "action",
    "channel": "process",
    "status": "completed",
    "data": {"x": "dependency result"}
}
```

The `nested_dependency` function depends on `common_dependency`, and the `process` action depends on `nested_dependency`. Parameters are nested accordingly in the request data.

## Using Pydantic Models in Dependencies

Dependencies can use Pydantic models for complex data validation:

```python
from pydantic import BaseModel

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

@app.action("process_data")
async def process_data(
    dep: Annotated[ComplexDataModel, Depends(complex_data_dependency)]
) -> ComplexDataModel:
    return dep
```

Send:
```json
{
    "type": "action",
    "channel": "process_data",
    "data": {
        "dep": {
            "complex_data": {
                "name": "Test",
                "value": 5,
                "address": {
                    "street": "123 Main St",
                    "city": "Anytown",
                    "zip_code": "12345"
                }
            }
        }
    }
}
```

Receive:
```json
{
    "type": "action",
    "channel": "process_data",
    "status": "completed",
    "data": {
        "name": "Test",
        "value": 15,
        "address": {
            "street": "123 Main St",
            "city": "Anytown",
            "zip_code": "12345"
        }
    }
}
```

The dependency modifies the `value` field (adding 10) before returning it to the action.

## Common Use Cases

### Authentication

```python
from typing import Annotated

class User(BaseModel):
    id: int
    username: str
    role: str

async def get_current_user(token: str) -> User:
    # Validate token and fetch user from database
    if token == "invalid":
        raise ValueError("Invalid token")
    return User(id=1, username="alice", role="admin")

@app.action("get_profile")
async def get_profile(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    return current_user
```

Send:
```json
{
    "type": "action",
    "channel": "get_profile",
    "data": {
        "current_user": {
            "token": "valid_token_here"
        }
    }
}
```

### Database Connection

```python
class DatabaseConnection:
    def __init__(self, db_url: str):
        self.db_url = db_url
    
    async def query(self, sql: str):
        # Execute query
        return []

async def get_db(db_url: str = "postgresql://localhost/mydb") -> DatabaseConnection:
    db = DatabaseConnection(db_url)
    return db

@app.action("fetch_users")
async def fetch_users(
    db: Annotated[DatabaseConnection, Depends(get_db)]
):
    users = await db.query("SELECT * FROM users")
    return {"users": users}
```

### Data Transformation

```python
from datetime import datetime

class TransformedData(BaseModel):
    data: str
    timestamp: int
    processed: bool

async def transform_data(raw_data: str) -> TransformedData:
    return TransformedData(
        data=raw_data.upper(),
        timestamp=int(datetime.now().timestamp()),
        processed=True
    )

@app.action("submit_data")
async def submit_data(
    transformed: Annotated[TransformedData, Depends(transform_data)]
) -> TransformedData:
    # Save transformed data
    return transformed
```

Send:
```json
{
    "type": "action",
    "channel": "submit_data",
    "data": {
        "transformed": {
            "raw_data": "hello world"
        }
    }
}
```

Receive:
```json
{
    "type": "action",
    "channel": "submit_data",
    "status": "completed",
    "data": {
        "data": "HELLO WORLD",
        "timestamp": 1701234567,
        "processed": true
    }
}
```

## Dependencies in Channels

Dependencies work the same way in channels as they do in actions:

```python
from typing import Annotated

async def validate_token(token: str) -> dict:
    # Validate user token
    return {"user_id": 123, "valid": True}

@app.channel("private_updates")
async def private_updates(
    auth: Annotated[dict, Depends(validate_token), RequiredOnSubscribe],
    message: str = "Welcome"
):
    return {"message": message, "user_id": auth["user_id"]}
```

Subscribe:
```json
{
    "type": "subscribe",
    "channel": "private_updates",
    "data": {
        "auth": {
            "token": "secret_token"
        }
    }
}
```

Receive:
```json
{"type": "subscribed", "channel": "private_updates"}
```

Then receive initial data:
```json
{
    "type": "data",
    "channel": "private_updates",
    "data": {"message": "Welcome", "user_id": 123}
}
```

## Multiple Dependencies

Actions and channels can use multiple dependencies:

```python
async def get_user(token: str) -> User:
    return User(id=1, username="alice", role="admin")

async def get_settings(theme: str = "dark") -> dict:
    return {"theme": theme, "notifications": True}

@app.action("get_dashboard")
async def get_dashboard(
    user: Annotated[User, Depends(get_user)],
    settings: Annotated[dict, Depends(get_settings)]
):
    return {
        "user": user,
        "settings": settings
    }
```

Send:
```json
{
    "type": "action",
    "channel": "get_dashboard",
    "data": {
        "user": {
            "token": "valid_token"
        },
        "settings": {
            "theme": "light"
        }
    }
}
```

