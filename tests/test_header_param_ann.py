from typing import Annotated, List, Optional

import pytest
from flask import Flask

from flask_request_data_validator import Header, parameter_validator
from tests.conftest import match_pydantic_error_url

app = Flask(__name__)
client = app.test_client()


@app.get("/nullable_header")
@parameter_validator
def nullable_header(x_token: Annotated[Optional[str], Header(default=None)]):
    return {"x-token": x_token}


@app.get("/required_header")
@parameter_validator
def required_header(x_token: Annotated[str, Header(max_length=5)]):
    return {"x-token": x_token}


@app.get("/list_header")
@parameter_validator
def list_header(x_token: Annotated[Optional[List[str]], Header(default=None)]):
    return {"x-token": x_token}


@pytest.mark.parametrize(
    "path,headers,expected_status,expected_response",
    [
        ("/nullable_header", None, 200, {"x-token": None}),
        ("/nullable_header", {"x-token": "foo"}, 200, {"x-token": "foo"}),
        ("/nullable_header", {"x-token": 123}, 200, {"x-token": "123"}),
        ("/required_header", {"x-token": "a"}, 200, {"x-token": "a"}),
        (
            "/required_header",
            {"x-token": "abcdef"},
            422,
            {
                "detail": [
                    {
                        "ctx": {"max_length": 5},
                        "input": "abcdef",
                        "loc": ["header", "x-token"],
                        "msg": "String should have at most 5 characters",
                        "type": "string_too_long",
                        "url": match_pydantic_error_url("string_too_long"),
                    }
                ]
            },
        ),
        (
            "/required_header",
            None,
            422,
            {
                "detail": [
                    {
                        "input": None,
                        "loc": ["header", "x-token"],
                        "msg": "Field required",
                        "type": "missing",
                        "url": match_pydantic_error_url("missing"),
                    }
                ]
            },
        ),
        ("/list_header", None, 200, {"x-token": None}),
        ("/list_header", {"x-token": "foo"}, 200, {"x-token": ["foo"]}),
        # XXX: flask combine multiple field to string e.g. {"x-token": ["foo, bar"]}
        # (
        #     "/list_header",
        #     [("x-token", "foo"), ("x-token", "bar")],
        #     200,
        #     {"x-token": ["foo", "bar"]},
        # ),
    ],
)
def test_header(path, headers, expected_status, expected_response):
    response = client.get(path, headers=headers)
    assert response.status_code == expected_status
    assert response.get_json() == expected_response
