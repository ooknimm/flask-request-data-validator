from typing import Annotated, List, Optional, Union

import pytest
from flask import Flask

from flask_parameter_validator.param_functions import Header
from flask_parameter_validator.validator import parameter_validator

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
                        "url": "https://errors.pydantic.dev/2.1.2/v/string_too_long",
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
                        "input": {},
                        "loc": ["header", "x-token"],
                        "msg": "Field required",
                        "type": "missing",
                        "url": "https://errors.pydantic.dev/2.1.2/v/missing",
                    }
                ]
            },
        ),
    ],
)
def test_header(path, headers, expected_status, expected_response):
    response = client.get(path, headers=headers)
    assert response.status_code == expected_status
    assert response.get_json() == expected_response
