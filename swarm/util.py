import inspect
from datetime import datetime
from typing import Any, List, get_origin, get_args, Callable, Dict
from pydantic import BaseModel, TypeAdapter


def debug_print(debug: bool, *args: Any) -> None:
    if not debug:
        return
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = " ".join(map(str, args))
    print(f"\033[97m[\033[90m{timestamp}\033[97m]\033[90m {message}\033[0m")


def merge_fields(target, source):
    for key, value in source.items():
        if isinstance(value, str):
            target[key] += value
        elif value is not None and isinstance(value, dict):
            merge_fields(target[key], value)


def merge_chunk(final_response: dict, delta: dict) -> None:
    delta.pop("role", None)
    merge_fields(final_response, delta)

    tool_calls = delta.get("tool_calls")
    if tool_calls and len(tool_calls) > 0:
        index = tool_calls[0].pop("index")
        if "type" in tool_calls[0]:
            final_response["tool_calls"][index]["type"] = tool_calls[0].pop("type")
        merge_fields(final_response["tool_calls"][index], tool_calls[0])


def remove_titles(schema: dict | list) -> dict | list:
    """
    Recursively removes 'title' keys from the schema dictionary.

    Args:
        schema: The schema dictionary from which to remove 'title' keys.

    Returns:
        The schema dictionary without 'title' keys.
    """
    if isinstance(schema, dict):
        schema.pop('title', None)
        for key, value in schema.items():
            schema[key] = remove_titles(value)
    elif isinstance(schema, list):
        schema = [remove_titles(item) for item in schema]
    return schema

def function_to_json(func) -> dict:
    """
    Converts a Python function into a JSON-serializable dictionary
    that describes the function's signature, including its name,
    description, and parameters.

    Args:
        func: The function to be converted.

    Returns:
        A dictionary representing the function's signature in JSON format.
    """
    type_map = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        list: "array",
        dict: "object",
        type(None): "null",
    }


    try:
        signature = inspect.signature(func)
    except ValueError as e:
        raise ValueError(
            f"Failed to get signature for function {func.__name__}: {str(e)}"
        )

    parameters = {}
    for param in signature.parameters.values():
        annotation = param.annotation
        try:
            origin = get_origin(annotation)
            args = get_args(annotation)

            if isinstance(annotation, type) and issubclass(annotation, BaseModel):
                schema = annotation.model_json_schema()
                schema = remove_titles(schema)
                parameters[param.name] = schema
            elif origin is list and len(args) == 1:
                item_type = args[0]
                if isinstance(item_type, type) and issubclass(item_type, BaseModel):
                    # Handle list of BaseModel subclasses
                    item_schema = item_type.model_json_schema()
                    item_schema = remove_titles(item_schema)
                    parameters[param.name] = {
                        "type": "array",
                        "items": item_schema,
                    }
                elif item_type in type_map:
                    # Handle list of primitive types
                    parameters[param.name] = {
                        "type": "array",
                        "items": {"type": type_map.get(item_type, "string")},
                    }
                else:
                    # Default to string if type is unknown
                    parameters[param.name] = {
                        "type": "array",
                        "items": {"type": "string"},
                    }
            else:
                parameters[param.name] = {"type": type_map.get(annotation, "string")}
        except KeyError as e:
            raise KeyError(
                f"Unknown type annotation {annotation} for parameter {param.name}: {str(e)}"
            )

    required = [
        param.name
        for param in signature.parameters.values()
        if param.default == inspect._empty
    ]

    return {
        "type": "function",
        "function": {
            "name": func.__name__,
            "description": func.__doc__ or "",
            "parameters": {
                "type": "object",
                "properties": parameters,
                "required": required,
            },
        },
    }

def json_to_function_args(func: Callable, json_args: Dict[str, Any]) -> Dict[str, Any]:
    """Converts a JSON object to function arguments based on the function's annotations."""
    sig = inspect.signature(func)
    args = {}
    for name, param in sig.parameters.items():
        if name in json_args:
            annotation = param.annotation
            value = json_args[name]
            if inspect.isclass(annotation) and issubclass(annotation, BaseModel):
                args[name] = annotation(**value)
            elif (
                getattr(annotation, '__origin__', None) is list and
                hasattr(annotation, '__args__') and
                len(annotation.__args__) > 0
            ):
                item_type = annotation.__args__[0]
                if inspect.isclass(item_type) and issubclass(item_type, BaseModel):
                    args[name] = [item_type(**item) for item in value]
                elif item_type in [str, int, float, bool]:
                    args[name] = value  # Assuming the list is of the correct primitive type
                else:
                    args[name] = value  # Default to passing the value as is
            else:
                args[name] = value
        else:
            args[name] = param.default
    return args
