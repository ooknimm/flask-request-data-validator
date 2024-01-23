import io
from pathlib import Path
from typing import Annotated, Optional

import pytest
from flask import Flask, jsonify
from werkzeug.datastructures import FileStorage

from flask_parameter_validator import Body, File, Form, parameter_validator
from tests.conftest import Item, User, match_pydantic_error_url

app = Flask(__name__)
client = app.test_client()


@app.post("/users")
@parameter_validator
def create_user(user: User):
    return jsonify(user.model_dump())


@app.post("/users-embed")
@parameter_validator
def create_user_embed(user: User = Body(embed=True)):
    return jsonify(user.model_dump())


@app.put("/users")
@parameter_validator
def put_user(user: User, importance: Annotated[int, Body()]):
    return jsonify({"user": user.model_dump(), "importance": importance})


@app.post("/items")
@parameter_validator
def create_item(item: Item, user: User):
    return jsonify({"item": item.model_dump(), "user": user.model_dump()})


@app.put("/items")
@parameter_validator
def put_item(item: Item, user: Optional[User] = None):
    response = {"item": item.model_dump()}
    if user:
        response.update({"user": user.model_dump()})
    return response


@app.post("/form")
@parameter_validator
def form_item(item: Annotated[Item, Form()]):
    return jsonify({"item": item.model_dump()})


@pytest.mark.parametrize(
    "path,body,expected_status,expected_response",
    [
        (
            "/users",
            {"name": "Nick", "address": "seoul"},
            200,
            {"name": "Nick", "address": "seoul"},
        ),
        (
            "/users",
            {"name": "Nick", "address": 99},
            422,
            {
                "detail": [
                    {
                        "type": "string_type",
                        "loc": ["body", "user", "address"],
                        "msg": "Input should be a valid string",
                        "input": 99,
                        "url": match_pydantic_error_url("string_type"),
                    }
                ]
            },
        ),
        (
            "/users",
            {},
            422,
            {
                "detail": [
                    {
                        "type": "missing",
                        "loc": ["body", "user"],
                        "msg": "Field required",
                        "input": {},
                        "url": match_pydantic_error_url("missing"),
                    }
                ]
            },
        ),
        (
            "/users-embed",
            {"user": {"name": "Nick", "address": "seoul"}},
            200,
            {"name": "Nick", "address": "seoul"},
        ),
    ],
)
def test_single_body_param(path, body, expected_status, expected_response):
    response = client.post(path, json=body)
    assert response.status_code == expected_status
    assert response.get_json() == expected_response


@pytest.mark.parametrize(
    "path,body,expected_status,expected_response",
    [
        (
            "/items",
            {
                "user": {"name": "nick", "address": "seoul"},
                "item": {"name": "Foo", "price": 5000, "quantity": 50},
            },
            200,
            {
                "user": {"name": "nick", "address": "seoul"},
                "item": {"name": "Foo", "price": 5000, "quantity": 50},
            },
        )
    ],
)
def test_multiple_body_params(path, body, expected_status, expected_response):
    response = client.post(path, json=body)
    assert response.status_code == expected_status
    assert response.get_json() == expected_response


@pytest.mark.parametrize(
    "path,body,expected_status,expected_response",
    [
        (
            "/items",
            {
                "user": {"name": "nick", "address": "seoul"},
                "item": {"name": "Foo", "price": 5000, "quantity": 50},
            },
            200,
            {
                "user": {"name": "nick", "address": "seoul"},
                "item": {"name": "Foo", "price": 5000, "quantity": 50},
            },
        ),
        (
            "/items",
            {"item": {"name": "Foo", "price": 5000, "quantity": 50}},
            200,
            {"item": {"name": "Foo", "price": 5000, "quantity": 50}},
        ),
        (
            "/items",
            {"item": {"name": "Foo", "price": 5000, "quantity": "i don't know"}},
            422,
            {
                "detail": [
                    {
                        "type": "int_parsing",
                        "loc": ["body", "item", "quantity"],
                        "msg": "Input should be a valid integer, unable to parse string as an integer",
                        "input": "i don't know",
                        "url": match_pydantic_error_url("int_parsing"),
                    }
                ]
            },
        ),
    ],
)
def test_optional_params(path, body, expected_status, expected_response):
    response = client.put(path, json=body)
    assert response.status_code == expected_status
    assert response.get_json() == expected_response


@pytest.mark.parametrize(
    "path,body,expected_status,expected_response",
    [
        (
            "/users",
            {"user": {"name": "nick", "address": "seoul"}, "importance": 3},
            200,
            {"user": {"name": "nick", "address": "seoul"}, "importance": 3},
        ),
        (
            "/users",
            {"user": {"name": "nick", "address": "seoul"}, "importance": "not integer"},
            422,
            {
                "detail": [
                    {
                        "type": "int_parsing",
                        "loc": ["body", "importance"],
                        "msg": "Input should be a valid integer, unable to parse string as an integer",
                        "input": "not integer",
                        "url": match_pydantic_error_url("int_parsing"),
                    }
                ]
            },
        ),
    ],
)
def test_single_value_params(path, body, expected_status, expected_response):
    response = client.put(path, json=body)
    assert response.status_code == expected_status
    assert response.get_json() == expected_response


@pytest.mark.parametrize(
    "path,body,expected_status,expected_response",
    [
        (
            "/form",
            {"name": "Foo", "price": 5000, "quantity": 50},
            200,
            {"item": {"name": "Foo", "price": 5000, "quantity": 50}},
        ),
        (
            "/form",
            {"price": 5000, "quantity": 50},
            422,
            {
                "detail": [
                    {
                        "input": {"price": "5000", "quantity": "50"},
                        "loc": ["body", "item", "name"],
                        "msg": "Field required",
                        "type": "missing",
                        "url": match_pydantic_error_url("missing"),
                    }
                ]
            },
        ),
    ],
)
def test_form_data(path, body, expected_status, expected_response):
    response = client.post(path, data=body)
    assert response.status_code == expected_status
    assert response.get_json() == expected_response
