from typing import Annotated, List, Optional

import pytest
from flask import Flask

from flask_request_data_validator import Cookie, parameter_validator
from tests.conftest import match_pydantic_error_url

app = Flask(__name__)


@app.get("/nullable_cookie")
@parameter_validator
def nullable_cookie(x_token: Annotated[Optional[str], Cookie(default=None)]):
    return {"x_token": x_token}


@app.get("/required_cookie")
@parameter_validator
def required_cookie(x_token: Annotated[str, Cookie(max_length=5)]):
    return {"x_token": x_token}


@app.get("/list_cookie")
@parameter_validator
def list_cookie(x_token: Annotated[Optional[List[str]], Cookie(default=None)]):
    return {"x_token": x_token}


@pytest.mark.parametrize(
    "path,cookies,expected_status,expected_response",
    [
        ("/nullable_cookie", None, 200, {"x_token": None}),
        ("/nullable_cookie", {"x_token": "foo"}, 200, {"x_token": "foo"}),
        ("/nullable_cookie", {"x_token": 123}, 200, {"x_token": "123"}),
        ("/required_cookie", {"x_token": "a"}, 200, {"x_token": "a"}),
        (
            "/required_cookie",
            {"x_token": "abcdef"},
            422,
            {
                "detail": [
                    {
                        "ctx": {"max_length": 5},
                        "input": "abcdef",
                        "loc": ["cookie", "x_token"],
                        "msg": "String should have at most 5 characters",
                        "type": "string_too_long",
                        "url": match_pydantic_error_url("string_too_long"),
                    }
                ]
            },
        ),
        (
            "/required_cookie",
            None,
            422,
            {
                "detail": [
                    {
                        "input": None,
                        "loc": ["cookie", "x_token"],
                        "msg": "Field required",
                        "type": "missing",
                        "url": match_pydantic_error_url("missing"),
                    }
                ]
            },
        ),
        ("/list_cookie", None, 200, {"x_token": None}),
        ("/list_cookie", {"x_token": "foo"}, 200, {"x_token": ["foo"]}),
        # XXX: flask combine multiple field to string e.g. {"x_token": ["foo, bar"]}
        # (
        #     "/list_cookie",
        #     [("x_token", "foo"), ("x_token", "bar")],
        #     200,
        #     {"x_token": ["foo", "bar"]},
        # ),
    ],
)
def test_cookie(path, cookies, expected_status, expected_response):
    client = app.test_client()
    if cookies:
        for key, val in cookies.items():
            client.set_cookie(key=key, value=str(val))
    response = client.get(path)
    assert response.status_code == expected_status
    assert response.get_json() == expected_response
