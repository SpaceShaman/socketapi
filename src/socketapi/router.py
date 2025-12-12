from typing import Any, Awaitable, Callable, Generic, ParamSpec, TypedDict, TypeVar

from socketapi.handlers import ChannelHandler

P = ParamSpec("P")
R = TypeVar("R")


class FuncRef(Generic[P, R]):
    def __init__(self, fn: Callable[P, Awaitable[R]]):
        self.fn: Callable[P, Awaitable[R]] = fn

    def set(self, fn: Callable[P, Awaitable[R]]) -> None:
        self.fn = fn

    async def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        return await self.fn(*args, **kwargs)


class ChannelDefinition(TypedDict):
    func: FuncRef[Any, Any]
    default_response: bool


class Router:
    def __init__(self):
        self.channels: dict[str, ChannelDefinition] = {}

    def channel(
        self, name: str, default_response: bool = True
    ) -> Callable[
        [Callable[P, Awaitable[R]]], ChannelHandler[P, R] | Callable[P, Awaitable[R]]
    ]:
        def decorator(
            func: Callable[P, Awaitable[R]],
        ) -> Callable[P, Awaitable[R]] | ChannelHandler[P, R]:
            ref = FuncRef(func)
            self.channels[name] = {
                "func": ref,
                "default_response": default_response,
            }
            return ref

        return decorator
