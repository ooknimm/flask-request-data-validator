from typing import Annotated, List, Optional, Union

import pytest
from flask import Flask, jsonify

from flask_request_data_validator import Path, Query, parameter_validator
from tests.conftest import User, match_pydantic_error_url

app = Flask(__name__)
client = app.test_client()


@app.post("/users")
@parameter_validator
def create_user(user: User, q: Annotated[Optional[str], Query()] = None):
    response = user.model_dump()
    if q:
        response.update({"q": q})
    return jsonify(response)


@app.get("/multi_q")
@parameter_validator
def multi_q(q: Annotated[Union[List[str], None], Query(default=None)]):
    return jsonify({"q": q})


@app.get("/multi_q_default")
@parameter_validator
def multi_q_default(q: Annotated[List[str], Query(default=["foo", "bar"])]):
    return jsonify({"q": q})


@app.get("/multi_q_default2")
@parameter_validator
def multi_q_default2(q: Annotated[List[str], Query(default=[])]):
    return jsonify({"q": q})


@app.post("/greater_than")
@parameter_validator
def greater_than(q: Annotated[Optional[int], Query(gt=40)] = None):
    return jsonify({"q": q})


@app.get("/items/<item_id>")
@parameter_validator
def read_user_item(
    item_id: str = Path(),
    needy: str = Query(),
    skip: int = Query(default=0),
    limit: Annotated[Optional[int], Query()] = None,
):
    item = {"item_id": item_id, "needy": needy, "skip": skip, "limit": limit}
    return item


@pytest.mark.parametrize(
    "path,body,expected_status,expected_response",
    [
        (
            "/users?q=query_string",
            {"name": "nick", "address": "seoul"},
            200,
            {"name": "nick", "address": "seoul", "q": "query_string"},
        )
    ],
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
                        "url": match_pydantic_error_url("greater_than"),
                    }
                ]
            },
        ),
        (
            "/greater_than?q=string",
            None,
            422,
            {
                "detail": [
                    {
                        "type": "int_parsing",
                        "input": "string",
                        "loc": ["query", "q"],
                        "msg": "Input should be a valid integer, unable to parse string as an integer",
                        "url": match_pydantic_error_url("int_parsing"),
                    }
                ]
            },
        ),
    ],
)
def test_greater_than_query_string_param(
    path, body, expected_status, expected_response
):
    response = client.post(path, json=body)
    assert response.status_code == expected_status
    assert response.get_json() == expected_response


def test_foo_needy_very():
    response = client.get("/items/foo?needy=very")
    assert response.status_code == 200
    assert response.get_json() == {
        "item_id": "foo",
        "needy": "very",
        "skip": 0,
        "limit": None,
    }


def test_foo_no_needy():
    response = client.get("/items/foo?skip=a&limit=b")
    assert response.status_code == 422
    assert response.get_json() == {
        "detail": [
            {
                "type": "missing",
                "loc": ["query", "needy"],
                "msg": "Field required",
                "input": None,
                "url": match_pydantic_error_url("missing"),
            },
            {
                "type": "int_parsing",
                "loc": ["query", "skip"],
                "msg": "Input should be a valid integer, unable to parse string as an integer",
                "input": "a",
                "url": match_pydantic_error_url("int_parsing"),
            },
            {
                "type": "int_parsing",
                "loc": ["query", "limit"],
                "msg": "Input should be a valid integer, unable to parse string as an integer",
                "input": "b",
                "url": match_pydantic_error_url("int_parsing"),
            },
        ]
    }


def test_multi_query_values():
    url = "/multi_q?q=foo&q=bar"
    response = client.get(url)
    assert response.status_code == 200, response.text
    assert response.get_json() == {"q": ["foo", "bar"]}


def test_query_no_values():
    url = "/multi_q"
    response = client.get(url)
    assert response.status_code == 200, response.text
    assert response.get_json() == {"q": None}


def test_multi_query_default_values():
    url = "/multi_q_default"
    response = client.get(url)
    assert response.status_code == 200, response.text
    assert response.get_json() == {"q": ["foo", "bar"]}


def test_multi_query_values2():
    url = "/multi_q_default?q=baz&q=foobar"
    response = client.get(url)
    assert response.status_code == 200, response.text
    assert response.get_json() == {"q": ["baz", "foobar"]}


def test_default_multi_query_values():
    url = "/multi_q_default2?q=foo&q=bar"
    response = client.get(url)
    assert response.status_code == 200, response.text
    assert response.get_json() == {"q": ["foo", "bar"]}


def test_default_multi_query_no_values():
    url = "/multi_q_default2"
    response = client.get(url)
    assert response.status_code == 200, response.text
    assert response.get_json() == {"q": []}
