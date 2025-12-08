from typing import Any, Callable

RequiredOnSubscribe = "required_on_subscribe"


class Depends:
    def __init__(self, dependency: Callable[..., Any]) -> None:
        self.dependency = dependency
