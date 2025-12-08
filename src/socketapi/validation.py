import inspect
from typing import Any, Callable, get_args

from pydantic import BaseModel, create_model

from socketapi import Depends, RequiredOnSubscribe


async def validate_data(
    func: Callable[..., Any], data: dict[str, Any], on_subscribe: bool = False
) -> Any:
    fields: dict[str, Any] = {}
    sig = inspect.signature(func)
    for name, param in sig.parameters.items():
        param_type = (
            param.annotation if param.annotation is not inspect.Parameter.empty else Any
        )
        annotation = _get_annotation(param_type)
        if on_subscribe and annotation != RequiredOnSubscribe:
            continue
        if isinstance(annotation, Depends):
            data[name] = await validate_data(
                annotation.dependency, data.get(name, {}), on_subscribe
            )
            dep_sig = inspect.signature(annotation.dependency)
            param_type = dep_sig.return_annotation
        fields[name] = (param_type, ...)
    model_cls = create_model("Validator", **fields)
    try:
        model_instance = model_cls(**data)
    except Exception as e:
        raise ValueError(f"Invalid parameters for action '{func.__name__}'") from e
    validated = {k: getattr(model_instance, k) for k in model_cls.model_fields}
    return await func(**validated)

    # model_cls = _build_input_model_from_signature(func, data, on_subscribe)
    # try:
    #     model_instance = model_cls(**data)
    # except Exception as e:
    #     raise ValueError(f"Invalid parameters for action '{func.__name__}'") from e
    # validated = {k: getattr(model_instance, k) for k in model_cls.model_fields}
    # return func(**validated)


def _build_input_model_from_signature(
    handler: Callable[..., Any], data: dict[str, Any], on_subscribe: bool
) -> type[BaseModel]:
    sig = inspect.signature(handler)
    fields: dict[str, Any] = {}
    for name, param in sig.parameters.items():
        param_type = (
            param.annotation if param.annotation is not inspect.Parameter.empty else Any
        )
        annotation = _get_annotation(param_type)
        if isinstance(annotation, Depends):
            param_type = _build_input_model_from_signature(
                annotation.dependency, data[name], on_subscribe
            )
        if on_subscribe and annotation != RequiredOnSubscribe:
            continue
        fields[name] = (param_type, ...)
    return create_model("Validator", **fields)


def _get_annotation(param_type: Any) -> Any:
    if annotation := get_args(param_type)[1:]:
        return annotation[0]
    return None
