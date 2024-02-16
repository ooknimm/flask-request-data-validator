from typing import Union

import pytest
from flask import Flask, jsonify
from pydantic import BaseModel, Field

from flask_request_data_validator import Body, Path, parameter_validator
from tests.conftest import match_pydantic_error_url

app = Flask(__name__)
client = app.test_client()


class Item(BaseModel):
    name: str
    description: Union[str, None] = Field(
        default=None, title="The description of the item", max_length=300
    )
    price: float = Field(gt=0, description="The price must be greater than zero")
    tax: Union[float, None] = None


@app.post("/items/")
@parameter_validator
def create_item(item: Item):
    return jsonify(item.model_dump())


@app.put("/items/<item_id>")
@parameter_validator
def update_item(item_id: int = Path(), item: Item = Body(embed=True)):
    results = {"item_id": item_id, "item": item.model_dump()}
    return results


@pytest.mark.parametrize(
    "title,data,expected_status,expected_response",
    [
        (
            "body float",
            {"name": "Foo", "price": 50.5},
            200,
            {"name": "Foo", "price": 50.5, "description": None, "tax": None},
        ),
        (
            "post_with_str_float",
            {"name": "Foo", "price": "50.5"},
            200,
            {"name": "Foo", "price": 50.5, "description": None, "tax": None},
        ),
        (
            "post_with_str_float_description",
            {"name": "Foo", "price": "50.5", "description": "Some Foo"},
            200,
            {
                "name": "Foo",
                "price": 50.5,
                "description": "Some Foo",
                "tax": None,
            },
        ),
        (
            "post_with_str_float_description_tax",
            {"name": "Foo", "price": "50.5", "description": "Some Foo", "tax": 0.3},
            200,
            {
                "name": "Foo",
                "price": 50.5,
                "description": "Some Foo",
                "tax": 0.3,
            },
        ),
        (
            "post_with_only_name",
            {"name": "Foo"},
            422,
            {
                "detail": [
                    {
                        "type": "missing",
                        "loc": ["body", "price"],
                        "msg": "Field required",
                        "input": {"name": "Foo"},
                        "url": match_pydantic_error_url("missing"),
                    }
                ]
            },
        ),
        (
            "post_with_only_name_price",
            {"name": "Foo", "price": "twenty"},
            422,
            {
                "detail": [
                    {
                        "type": "float_parsing",
                        "loc": ["body", "price"],
                        "msg": "Input should be a valid number, unable to parse string as a number",
                        "input": "twenty",
                        "url": match_pydantic_error_url("float_parsing"),
                    }
                ]
            },
        ),
        (
            "post_with_no_data",
            {},
            422,
            {
                "detail": [
                    {
                        "type": "missing",
                        "loc": ["body", "name"],
                        "msg": "Field required",
                        "input": {},
                        "url": match_pydantic_error_url("missing"),
                    },
                    {
                        "type": "missing",
                        "loc": ["body", "price"],
                        "msg": "Field required",
                        "input": {},
                        "url": match_pydantic_error_url("missing"),
                    },
                ]
            },
        ),
        (
            "post_with_none",
            None,
            422,
            {
                "detail": [
                    {
                        "type": "missing",
                        "loc": ["body"],
                        "msg": "Field required",
                        "input": None,
                        "url": match_pydantic_error_url("missing"),
                    }
                ]
            },
        ),
    ],
)
def test_create_item(title, data, expected_status, expected_response):
    response = client.post("/items/", json=data)
    assert response.status_code == expected_status
    assert response.get_json() == expected_response


def test_post_broken_body():
    response = client.post(
        "/items/",
        headers={"content-type": "application/json"},
        data="{some broken json}",
    )
    assert response.status_code == 422
    assert response.get_json() == {
        "detail": [
            {
                "type": "json_invalid",
                "loc": ["body", 1],
                "msg": "JSON decode error",
                "input": {},
                "ctx": {"error": "Expecting property name enclosed in double quotes"},
            }
        ]
    }


def test_post_form_for_json():
    response = client.post("/items/", data={"name": "Foo", "price": 50.5})
    assert response.status_code == 422, response.text
    assert response.get_json() == {
        "detail": [
            {
                "type": "missing",
                "loc": ["body"],
                "msg": "Field required",
                "input": None,
                "url": match_pydantic_error_url("missing"),
            }
        ]
    }


def test_explicit_content_type():
    response = client.post(
        "/items/",
        data='{"name": "Foo", "price": 50.5}',
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 200, response.text


def test_geo_json():
    response = client.post(
        "/items/",
        data='{"name": "Foo", "price": 50.5}',
        headers={"Content-Type": "application/geo+json"},
    )
    assert response.status_code == 200, response.text


def test_no_content_type_is_json():
    response = client.post(
        "/items/",
        data='{"name": "Foo", "price": 50.5}',
    )
    assert response.status_code == 200, response.text
    assert response.get_json() == {
        "name": "Foo",
        "description": None,
        "price": 50.5,
        "tax": None,
    }


@pytest.mark.parametrize(
    "title,header,expected_status,expected_response",
    [
        (
            "text/plain",
            {"Content-Type": "text/plain"},
            422,
            {
                "detail": [
                    {
                        "type": "model_attributes_type",
                        "loc": ["body"],
                        "msg": "Input should be a valid dictionary or object to extract fields from",
                        "input": '{"name": "Foo", "price": 50.5}',
                        "url": match_pydantic_error_url("model_attributes_type"),
                    }
                ]
            },
        ),
        (
            "application/geo+json-seq",
            {"Content-Type": "application/geo+json-seq"},
            422,
            {
                "detail": [
                    {
                        "type": "model_attributes_type",
                        "loc": ["body"],
                        "msg": "Input should be a valid dictionary or object to extract fields from",
                        "input": '{"name": "Foo", "price": 50.5}',
                        "url": match_pydantic_error_url("model_attributes_type"),
                    }
                ]
            },
        ),
        (
            "application/not-really-json",
            {"Content-Type": "application/not-really-json"},
            422,
            {
                "detail": [
                    {
                        "type": "model_attributes_type",
                        "loc": ["body"],
                        "msg": "Input should be a valid dictionary or object to extract fields from",
                        "input": '{"name": "Foo", "price": 50.5}',
                        "url": match_pydantic_error_url("model_attributes_type"),
                    }
                ]
            },
        ),
    ],
)
def test_wrong_headers(title, header, expected_status, expected_response):
    data = '{"name": "Foo", "price": 50.5}'
    response = client.post("/items/", data=data, headers=header)
    assert response.status_code == expected_status
    assert response.get_json() == expected_response


@pytest.mark.parametrize(
    "title,path,data,expected_status,expected_response",
    [
        (
            "success",
            "/items/5",
            {"item": {"name": "Foo", "price": 3.0}},
            200,
            {
                "item_id": 5,
                "item": {"name": "Foo", "price": 3.0, "description": None, "tax": None},
            },
        ),
        (
            "success",
            "/items/6",
            {
                "item": {
                    "name": "Bar",
                    "price": 0.2,
                    "description": "Some bar",
                    "tax": "5.4",
                }
            },
            200,
            {
                "item_id": 6,
                "item": {
                    "name": "Bar",
                    "price": 0.2,
                    "description": "Some bar",
                    "tax": 5.4,
                },
            },
        ),
        (
            "invalid_price",
            "/items/5",
            {"item": {"name": "Foo", "price": -3.0}},
            422,
            {
                "detail": [
                    {
                        "type": "greater_than",
                        "loc": ["body", "item", "price"],
                        "msg": "Input should be greater than 0",
                        "input": -3.0,
                        "ctx": {"gt": 0.0},
                        "url": match_pydantic_error_url("greater_than"),
                    }
                ]
            },
        ),
    ],
)
def test_update_item(title, path, data, expected_status, expected_response):
    response = client.put(path, json=data)
    assert response.status_code == expected_status
    assert response.get_json() == expected_response
