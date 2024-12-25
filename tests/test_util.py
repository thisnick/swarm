from swarm.util import function_to_json, json_to_function_args
from typing import Any, Callable, Dict, List
import inspect
from pydantic import BaseModel

def test_basic_function():
    def basic_function(arg1, arg2):
        return arg1 + arg2

    result = function_to_json(basic_function)
    assert result == {
        "type": "function",
        "function": {
            "name": "basic_function",
            "description": "",
            "parameters": {
                "type": "object",
                "properties": {
                    "arg1": {"type": "string"},
                    "arg2": {"type": "string"},
                },
                "required": ["arg1", "arg2"],
            },
        },
    }


def test_complex_function():
    def complex_function_with_types_and_descriptions(
        arg1: int, arg2: str, arg3: float = 3.14, arg4: bool = False
    ):
        """This is a complex function with a docstring."""
        pass

    result = function_to_json(complex_function_with_types_and_descriptions)
    assert result == {
        "type": "function",
        "function": {
            "name": "complex_function_with_types_and_descriptions",
            "description": "This is a complex function with a docstring.",
            "parameters": {
                "type": "object",
                "properties": {
                    "arg1": {"type": "integer"},
                    "arg2": {"type": "string"},
                    "arg3": {"type": "number"},
                    "arg4": {"type": "boolean"},
                },
                "required": ["arg1", "arg2"],
            },
        },
    }


def test_pydantic_model_function():
    from pydantic import BaseModel

    class MyModel(BaseModel):
        field1: str
        field2: int

    def function_using_pydantic(model: MyModel):
        return model.field1

    result = function_to_json(function_using_pydantic)
    assert result == {
        "type": "function",
        "function": {
            "name": "function_using_pydantic",
            "description": "",
            "parameters": {
                "type": "object",
                "properties": {
                    "model": {
                        "type": "object",
                        "properties": {
                            "field1": {"type": "string"},
                            "field2": {"type": "integer"},
                        },
                        "required": ["field1", "field2"],
                    },
                },
                "required": ["model"],
            },
        },
    }


def test_pydantic_model_list_function():
    from pydantic import BaseModel
    from typing import List

    class Item(BaseModel):
        name: str
        quantity: int

    def function_with_model_list(items: List[Item]):
        return [item.name for item in items]

    result = function_to_json(function_with_model_list)
    assert result == {
        "type": "function",
        "function": {
            "name": "function_with_model_list",
            "description": "",
            "parameters": {
                "type": "object",
                "properties": {
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "quantity": {"type": "integer"},
                            },
                            "required": ["name", "quantity"],
                        },
                    },
                },
                "required": ["items"],
            },
        },
    }


def test_json_to_function_args_single_pydantic_model():
    class UserRequest(BaseModel):
        name: str
        age: int

    def sample_func(request: UserRequest):
        pass

    json_args = {
        "request": {
            "name": "Alice",
            "age": 30
        }
    }

    args = json_to_function_args(sample_func, json_args)

    assert isinstance(args['request'], UserRequest)
    assert args['request'].name == "Alice"
    assert args['request'].age == 30


def test_json_to_function_args_list_of_pydantic_models():
    class Item(BaseModel):
        id: int
        description: str

    def sample_func(items: List[Item]):
        pass

    json_args = {
        "items": [
            {"id": 1, "description": "Item 1"},
            {"id": 2, "description": "Item 2"}
        ]
    }

    args = json_to_function_args(sample_func, json_args)

    assert isinstance(args['items'], list)
    assert all(isinstance(item, Item) for item in args['items'])
    assert args['items'][0].id == 1
    assert args['items'][0].description == "Item 1"
    assert args['items'][1].id == 2
    assert args['items'][1].description == "Item 2"


def test_json_to_function_args_mixed_arguments():
    class Address(BaseModel):
        street: str
        city: str

    class Order(BaseModel):
        order_id: int
        items: List[str]

    def sample_func(address: Address, orders: List[Order], confirmed: bool = False):
        pass

    json_args = {
        "address": {
            "street": "123 Main St",
            "city": "Metropolis"
        },
        "orders": [
            {"order_id": 101, "items": ["apple", "banana"]},
            {"order_id": 102, "items": ["orange"]}
        ],
        "confirmed": True
    }

    args = json_to_function_args(sample_func, json_args)

    # Assert Address
    assert isinstance(args['address'], Address)
    assert args['address'].street == "123 Main St"
    assert args['address'].city == "Metropolis"

    # Assert Orders
    assert isinstance(args['orders'], list)
    assert len(args['orders']) == 2
    assert isinstance(args['orders'][0], Order)
    assert args['orders'][0].order_id == 101
    assert args['orders'][0].items == ["apple", "banana"]
    assert isinstance(args['orders'][1], Order)
    assert args['orders'][1].order_id == 102
    assert args['orders'][1].items == ["orange"]

    # Assert Confirmed
    assert args['confirmed'] is True


# Additional Unit Tests for Lists of Primitive Types

def test_function_to_json_with_list_of_strings():
    def function_with_str_list(names: List[str]):
        return ", ".join(names)

    result = function_to_json(function_with_str_list)
    assert result == {
        "type": "function",
        "function": {
            "name": "function_with_str_list",
            "description": "",
            "parameters": {
                "type": "object",
                "properties": {
                    "names": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": ["names"],
            },
        },
    }


def test_function_to_json_with_list_of_integers():
    def function_with_int_list(numbers: List[int]):
        return sum(numbers)

    result = function_to_json(function_with_int_list)
    assert result == {
        "type": "function",
        "function": {
            "name": "function_with_int_list",
            "description": "",
            "parameters": {
                "type": "object",
                "properties": {
                    "numbers": {
                        "type": "array",
                        "items": {"type": "integer"},
                    },
                },
                "required": ["numbers"],
            },
        },
    }


def test_function_to_json_with_list_of_floats():
    def function_with_float_list(values: List[float]):
        return [v * 2 for v in values]

    result = function_to_json(function_with_float_list)
    assert result == {
        "type": "function",
        "function": {
            "name": "function_with_float_list",
            "description": "",
            "parameters": {
                "type": "object",
                "properties": {
                    "values": {
                        "type": "array",
                        "items": {"type": "number"},
                    },
                },
                "required": ["values"],
            },
        },
    }


def test_json_to_function_args_with_list_of_strings():
    def sample_func(names: List[str]):
        pass

    json_args = {
        "names": ["Alice", "Bob", "Charlie"]
    }

    args = json_to_function_args(sample_func, json_args)

    assert isinstance(args['names'], list)
    assert all(isinstance(name, str) for name in args['names'])
    assert args['names'] == ["Alice", "Bob", "Charlie"]


def test_json_to_function_args_with_list_of_integers():
    def sample_func(numbers: List[int]):
        pass

    json_args = {
        "numbers": [1, 2, 3, 4, 5]
    }

    args = json_to_function_args(sample_func, json_args)

    assert isinstance(args['numbers'], list)
    assert all(isinstance(num, int) for num in args['numbers'])
    assert args['numbers'] == [1, 2, 3, 4, 5]


def test_json_to_function_args_with_list_of_floats():
    def sample_func(values: List[float]):
        pass

    json_args = {
        "values": [1.5, 2.5, 3.75]
    }

    args = json_to_function_args(sample_func, json_args)

    assert isinstance(args['values'], list)
    assert all(isinstance(val, float) for val in args['values'])
    assert args['values'] == [1.5, 2.5, 3.75]
