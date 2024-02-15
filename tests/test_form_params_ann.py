from typing import Annotated

import pytest
from flask import Flask

from flask_parameter_validator import parameter_validator
from flask_parameter_validator.param_functions import Form
from tests.conftest import match_pydantic_error_url

app = Flask(__name__)
client = app.test_client()


@app.post("/login/")
@parameter_validator
def login(username: Annotated[str, Form()], password: Annotated[str, Form()]):
    return {"username": username}


@pytest.mark.parametrize(
    "data,expected_status,expected_response",
    [
        ({"username": "Foo", "password": "secret"}, 200, {"username": "Foo"}),
        (
            {"username": "Foo"},
            422,
            {
                "detail": [
                    {
                        "type": "missing",
                        "loc": ["body", "password"],
                        "msg": "Field required",
                        "input": None,
                        "url": match_pydantic_error_url("missing"),
                    }
                ]
            },
        ),
        (
            {"password": "secret"},
            422,
            {
                "detail": [
                    {
                        "type": "missing",
                        "loc": ["body", "username"],
                        "msg": "Field required",
                        "input": None,
                        "url": match_pydantic_error_url("missing"),
                    }
                ]
            },
        ),
        (
            {},
            422,
            {
                "detail": [
                    {
                        "type": "missing",
                        "loc": ["body", "username"],
                        "msg": "Field required",
                        "input": None,
                        "url": match_pydantic_error_url("missing"),
                    },
                    {
                        "type": "missing",
                        "loc": ["body", "password"],
                        "msg": "Field required",
                        "input": None,
                        "url": match_pydantic_error_url("missing"),
                    },
                ]
            },
        ),
    ],
)
def test_post_body_form(data, expected_status, expected_response):
    response = client.post("/login/", data=data)
    assert response.status_code == expected_status
    assert response.get_json() == expected_response


def test_post_body_json():
    response = client.post("/login/", json={"username": "Foo", "password": "secret"})
    assert response.status_code == 422, response.text
    assert response.get_json() == {
        "detail": [
            {
                "type": "missing",
                "loc": ["body", "username"],
                "msg": "Field required",
                "input": None,
                "url": match_pydantic_error_url("missing"),
            },
            {
                "type": "missing",
                "loc": ["body", "password"],
                "msg": "Field required",
                "input": None,
                "url": match_pydantic_error_url("missing"),
            },
        ]
    }
