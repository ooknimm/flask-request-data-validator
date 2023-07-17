from typing import Annotated, Optional

import pytest
from flask import Flask, jsonify

from flask_parameter_validator.params import Query
from flask_parameter_validator.validator import parameter_validator
from tests.conftest import Item, User

app = Flask(__name__)
client = app.test_client()


@app.post("/users")
@parameter_validator
def create_user(user: User, q: Annotated[Optional[str], Query()] = None):
    response = user.model_dump()
    if q:
        response.update({"q": q})
    return jsonify(response)


@app.post("/greater_than")
@parameter_validator
def greater_than(q: Annotated[Optional[int], Query(gt=40)] = None):
    return jsonify({"q": q})


@pytest.mark.parametrize(
    "path,body,expected_status,expected_response",
    [("/users?q=query_string", {"name": "nick", "address": "seoul"}, 200, {"name": "nick", "address": "seoul", "q": "query_string"})],
)
def test_query_string_param(path, body, expected_status, expected_response):
    response = client.post(path, json=body)
    assert response.status_code == expected_status
    assert response.get_json() == expected_response


@pytest.mark.parametrize(
    "path,body,expected_status,expected_response",
    [
        ("/greater_than?q=41", {}, 200, {"q": 41}),
        (
            "/greater_than?q=30",
            {},
            422,
            {
                "detail": [
                    {
                        "type": "greater_than",
                        "ctx": {"gt": 40},
                        "input": "30",
                        "loc": ["query", "q"],
                        "msg": "Input should be greater than 40",
                        "url": "https://errors.pydantic.dev/2.1.2/v/greater_than",
                    }
                ]
            },
        ),
    ],
)
def test_greater_than_query_string_param(path, body, expected_status, expected_response):
    response = client.post(path, json=body)
    assert response.status_code == expected_status
    assert response.get_json() == expected_response
