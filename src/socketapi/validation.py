import inspect
from typing import Any, Callable, get_args

from pydantic import BaseModel, create_model

from socketapi.annotations import RequiredOnSubscribe


def validate_data(
    func: Callable[..., Any], data: dict[str, Any], on_subscribe: bool = False
) -> dict[str, Any]:
    model_cls = _build_input_model_from_signature(func, on_subscribe)
    try:
        model_instance = model_cls(**data)
    except Exception as e:
        raise ValueError(f"Invalid parameters for action '{func.__name__}'") from e
    return {k: getattr(model_instance, k) for k in model_cls.model_fields}


def _build_input_model_from_signature(
    handler: Callable[..., Any], on_subscribe: bool
) -> type[BaseModel]:
    sig = inspect.signature(handler)
    fields: dict[str, Any] = {}
    for name, param in sig.parameters.items():
        ann = (
            param.annotation if param.annotation is not inspect.Parameter.empty else Any
        )
        if on_subscribe and get_args(ann)[1:] != (RequiredOnSubscribe,):
            continue
        fields[name] = (ann, ...)
    return create_model("Validator", **fields)
