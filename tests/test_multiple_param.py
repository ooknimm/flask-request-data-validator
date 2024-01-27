from typing import Annotated, Dict, Optional, Union

import pytest
from flask import Flask, jsonify
from pydantic import BaseModel

from flask_parameter_validator import Body, Path, Query, parameter_validator
from tests.conftest import match_pydantic_error_url

app = Flask(__name__)
client = app.test_client()


class Item(BaseModel):
    name: str
    description: Union[str, None] = None
    price: float
    tax: Union[float, None] = None


class User(BaseModel):
    name: str
    address: Union[str, None] = None


@app.put("/items/<item_id>")
@parameter_validator
def update_item(
    *,
    user: Optional[User] = None,
    item_id: int = Path(title="The ID of the item to get", ge=0, le=1000),
    q: Optional[str] = Query(default=None),
    item: Optional[Item] = None,
    importance: Annotated[Optional[int], Body()] = None,
):
    results: Dict = {"item_id": item_id}
    if q:
        results.update({"q": q})
    if user:
        results.update({"user": user.model_dump()})
    if importance:
        results.update({"importance": importance})
    if item:
        results.update({"item": item.model_dump()})
    return results


@app.put("/v2/items/<item_id>")
@parameter_validator
def update_item_v2(
    *, item_id: int = Path(), item: Item, user: User, importance: int = Body()
):
    results = {
        "item_id": item_id,
        "item": item.model_dump(),
        "user": user.model_dump(),
        "importance": importance,
    }
    return results


@app.post("/index-weights/")
@parameter_validator
def create_index_weights(weights: Dict[int, float]):
    return weights


@pytest.mark.parametrize(
    "title,path,body,expected_status,expected_response",
    [
        (
            "no_item",
            "/items/1?q=bar",
            {"user": {"name": "Foo", "address": "seoul"}, "importance": "1"},
            200,
            {
                "item_id": 1,
                "importance": 1,
                "q": "bar",
                "user": {"address": "seoul", "name": "Foo"},
            },
        ),
        (
            "no_query",
            "/items/1",
            {
                "user": {"name": "Foo"},
                "importance": "1",
                "item": {"name": "Bar", "price": 100},
            },
            200,
            {
                "item_id": 1,
                "importance": 1,
                "user": {
                    "name": "Foo",
                    "address": None,
                },
                "item": {
                    "name": "Bar",
                    "price": 100,
                    "description": None,
                    "tax": None,
                },
            },
        ),
        ("no_body_q_bar", "/items/5?q=bar", None, 200, {"item_id": 5, "q": "bar"}),
        ("no_body", "/items/5", None, 200, {"item_id": 5}),
        (
            "id_foo",
            "/items/foo",
            None,
            422,
            {
                "detail": [
                    {
                        "type": "int_parsing",
                        "loc": ["path", "item_id"],
                        "msg": "Input should be a valid integer, unable to parse string as an integer",
                        "input": "foo",
                        "url": match_pydantic_error_url("int_parsing"),
                    }
                ]
            },
        ),
    ],
)
def test_form_data(title, path, body, expected_status, expected_response):
    response = client.put(path, json=body)
    assert response.status_code == expected_status
    assert response.get_json() == expected_response


def test_post_body_no_data():
    response = client.put("/v2/items/5", json=None)
    assert response.status_code == 422
    assert response.get_json() == {
        "detail": [
            {
                "type": "missing",
                "loc": ["body", "item"],
                "msg": "Field required",
                "input": None,
                "url": match_pydantic_error_url("missing"),
            },
            {
                "type": "missing",
                "loc": ["body", "user"],
                "msg": "Field required",
                "input": None,
                "url": match_pydantic_error_url("missing"),
            },
            {
                "type": "missing",
                "loc": ["body", "importance"],
                "msg": "Field required",
                "input": None,
                "url": match_pydantic_error_url("missing"),
            },
        ]
    }


def test_post_body_empty_list():
    response = client.put("/v2/items/5", json=[])
    assert response.status_code == 422
    assert response.get_json() == {
        "detail": [
            {
                "type": "missing",
                "loc": ["body", "item"],
                "msg": "Field required",
                "input": None,
                "url": match_pydantic_error_url("missing"),
            },
            {
                "type": "missing",
                "loc": ["body", "user"],
                "msg": "Field required",
                "input": None,
                "url": match_pydantic_error_url("missing"),
            },
            {
                "type": "missing",
                "loc": ["body", "importance"],
                "msg": "Field required",
                "input": None,
                "url": match_pydantic_error_url("missing"),
            },
        ]
    }


def test_post_body():
    data = {"2": 2.2, "3": 3.3}
    response = client.post("/index-weights/", json=data)
    assert response.status_code == 200, response.text
    assert response.get_json() == data


def test_post_invalid_body():
    data = {"foo": 2.2, "3": 3.3}
    response = client.post("/index-weights/", json=data)
    assert response.status_code == 422, response.text
    assert response.get_json() == {
        "detail": [
            {
                "type": "int_parsing",
                "loc": ["body", "foo", "[key]"],
                "msg": "Input should be a valid integer, unable to parse string as an integer",
                "input": "foo",
                "url": match_pydantic_error_url("int_parsing"),
            }
        ]
    }
