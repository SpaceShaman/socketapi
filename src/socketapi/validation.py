import inspect
from typing import Any, Callable, get_args

from pydantic import create_model

from socketapi import Depends, RequiredOnSubscribe


async def validate_and_execute(
    func: Callable[..., Any], data: dict[str, Any], on_subscribe: bool = False
) -> Any:
    fields: dict[str, Any] = {}
    sig = inspect.signature(func)
    for name, param in sig.parameters.items():
        param_type = (
            param.annotation if param.annotation is not inspect.Parameter.empty else Any
        )
        annotations = _get_annotations(param_type)
        if on_subscribe and RequiredOnSubscribe not in annotations:
            continue
        if dep_annotation := next(
            (ann for ann in annotations if isinstance(ann, Depends)), None
        ):
            data[name] = await validate_and_execute(
                dep_annotation.dependency, data.get(name, {})
            )
            dep_sig = inspect.signature(dep_annotation.dependency)
            param_type = dep_sig.return_annotation
        fields[name] = (param_type, ...)
    model_cls = create_model("Validator", **fields)
    try:
        model_instance = model_cls(**data)
    except Exception as e:
        raise ValueError(f"Invalid parameters for action '{func.__name__}'") from e
    validated = {k: getattr(model_instance, k) for k in model_cls.model_fields}
    return await func(**validated)


def _get_annotations(param_type: Any) -> tuple[Any, ...]:
    if annotation := get_args(param_type)[1:]:
        return annotation
    return ()
