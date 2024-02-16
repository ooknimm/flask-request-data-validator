from enum import Enum

import pytest
from flask import Flask, jsonify

from flask_request_data_validator import Path, parameter_validator
from tests.conftest import User, match_pydantic_error_url

app = Flask(__name__)
client = app.test_client()


@app.put("/users/<user_id>")
@parameter_validator
def put_user(*, user_id: int = Path(), user: User):
    return jsonify({"user_id": user_id, **user.model_dump()})


@app.post("/greater_than/<user_id>")
@parameter_validator
def greater_than(user_id: int = Path(gt=10)):
    return jsonify({"user_id": user_id})


@app.get("/files/<path:file_path>")
@parameter_validator
def read_file(file_path: str = Path()):
    return {"file_path": file_path}


class ItemName(str, Enum):
    foo = "foo"
    bar = "bar"
    baz = "baz"


@app.get("/items/<item_name>")
@parameter_validator
def get_model(item_name: ItemName = Path()):
    if item_name is ItemName.foo:
        return {"item_name": item_name, "message": "item is foo"}

    if item_name.value == "bar":
        return {"item_name": item_name, "message": "item is bar"}

    return {"item_name": item_name, "message": "item is baz"}


@pytest.mark.parametrize(
    "path,body,expected_status,expected_response",
    [
        (
            "/users/1",
            {"name": "nick", "address": "seoul"},
            200,
            {"user_id": 1, "name": "nick", "address": "seoul"},
        ),
        (
            "/users/first",
            {"name": "nick", "address": "seoul"},
            422,
            {
                "detail": [
                    {
                        "type": "int_parsing",
                        "loc": ["path", "user_id"],
                        "msg": "Input should be a valid integer, unable to parse string as an integer",
                        "input": "first",
                        "url": "https://errors.pydantic.dev/2.1.2/v/int_parsing",
                    }
                ]
            },
        ),
    ],
)
def test_path_params(path, body, expected_status, expected_response):
    response = client.put(path, json=body)
    assert response.status_code == expected_status
    assert response.get_json() == expected_response


@pytest.mark.parametrize(
    "path,body,expected_status,expected_response",
    [
        (
            "/greater_than/100",
            {},
            200,
            {"user_id": 100},
        ),
        (
            "/greater_than/1",
            {},
            422,
            {
                "detail": [
                    {
                        "type": "greater_than",
                        "ctx": {"gt": 10},
                        "input": "1",
                        "loc": ["path", "user_id"],
                        "msg": "Input should be greater than 10",
                        "url": match_pydantic_error_url("greater_than"),
                    }
                ]
            },
        ),
    ],
)
def test_greater_than_path_params(path, body, expected_status, expected_response):
    response = client.post(path, json=body)
    assert response.status_code == expected_status
    assert response.get_json() == expected_response


def test_file_path():
    response = client.get("/files/home/me/myfile.txt")
    assert response.status_code == 200, response.text
    assert response.get_json() == {"file_path": "home/me/myfile.txt"}


@pytest.mark.parametrize(
    "path,expected_status,expected_response",
    [
        (
            "/items/foo",
            200,
            {"item_name": "foo", "message": "item is foo"},
        ),
        (
            "/items/bar",
            200,
            {"item_name": "bar", "message": "item is bar"},
        ),
        (
            "/items/baz",
            200,
            {"item_name": "baz", "message": "item is baz"},
        ),
        (
            "/items/qux",
            422,
            {
                "detail": [
                    {
                        "type": "enum",
                        "loc": ["path", "item_name"],
                        "msg": "Input should be 'foo','bar' or 'baz'",
                        "input": "qux",
                        "ctx": {"expected": "'foo','bar' or 'baz'"},
                    }
                ]
            },
        ),
    ],
)
def test_get_enums(path, expected_status, expected_response):
    response = client.get(path)
    assert response.status_code == expected_status
    assert response.get_json() == expected_response
