from typing import Annotated, Optional

import pytest
from flask import Flask, jsonify

from flask_parameter_validator.params import Path
from flask_parameter_validator.validator import parameter_validator
from tests.conftest import Item, User

app = Flask(__name__)
client = app.test_client()


@app.put("/users/<user_id>")
@parameter_validator
def put_user(user_id: Annotated[int, Path()], user: User):
    return jsonify({"user_id": user_id, **user.model_dump()})


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
