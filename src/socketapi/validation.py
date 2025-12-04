import inspect
from typing import Any, Callable

from pydantic import BaseModel, create_model


def validate_data(func: Callable[..., Any], data: dict[str, Any]) -> dict[str, Any]:
    model_cls = _build_input_model_from_signature(func)
    try:
        model_instance = model_cls(**data)
    except Exception as e:
        raise ValueError(f"Invalid parameters for action '{func.__name__}'") from e
    return model_instance.model_dump()


def _build_input_model_from_signature(handler: Callable[..., Any]) -> type[BaseModel]:
    sig = inspect.signature(handler)
    fields: dict[str, Any] = {}
    for name, param in sig.parameters.items():
        ann = (
            param.annotation if param.annotation is not inspect.Parameter.empty else Any
        )
        fields[name] = (ann, ...)
    return create_model("Validator", **fields)
