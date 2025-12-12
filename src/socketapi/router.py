from collections.abc import Coroutine
from typing import Any, Callable, Generic, ParamSpec, TypedDict, TypeVar

from socketapi.handlers import ActionHandler, ChannelHandler

P = ParamSpec("P")
R = TypeVar("R")


class FuncRef(Generic[P, R]):
    def __init__(self, fn: Callable[P, Coroutine[Any, Any, R]]) -> None:
        self.fn: Callable[P, Coroutine[Any, Any, R]] = fn

    def set(self, fn: Callable[P, Coroutine[Any, Any, R]]) -> None:
        self.fn = fn

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> Coroutine[Any, Any, R]:
        return self.fn(*args, **kwargs)


class ChannelDefinition(TypedDict):
    func: FuncRef[Any, Any]
    default_response: bool


class ActionDefinition(TypedDict):
    func: FuncRef[Any, Any]


class Router:
    def __init__(self):
        self.channels: dict[str, ChannelDefinition] = {}
        self.actions: dict[str, ActionDefinition] = {}

    def channel(
        self, name: str, default_response: bool = True
    ) -> Callable[
        [Callable[P, Coroutine[Any, Any, R]]],
        ChannelHandler[P, R] | Callable[P, Coroutine[Any, Any, R]],
    ]:
        def decorator(
            func: Callable[P, Coroutine[Any, Any, R]],
        ) -> Callable[P, Coroutine[Any, Any, R]] | ChannelHandler[P, R]:
            ref = FuncRef(func)
            self.channels[name] = {
                "func": ref,
                "default_response": default_response,
            }
            return ref

        return decorator

    def action(
        self, name: str
    ) -> Callable[
        [Callable[P, Coroutine[Any, Any, R]]],
        ActionHandler[P, R] | Callable[P, Coroutine[Any, Any, R]],
    ]:
        def decorator(
            func: Callable[P, Coroutine[Any, Any, R]],
        ) -> Callable[P, Coroutine[Any, Any, R]] | ActionHandler[P, R]:
            ref = FuncRef(func)
            self.actions[name] = {"func": ref}
            return ref

        return decorator
