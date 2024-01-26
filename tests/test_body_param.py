import io
from typing import Annotated, Optional

import pytest
from flask import Flask, jsonify
from werkzeug.datastructures import FileStorage

from flask_parameter_validator import Body, File, Form, Path, parameter_validator
from tests.conftest import Item, User, match_pydantic_error_url

app = Flask(__name__)
client = app.test_client()


@app.post("/items/")
@parameter_validator
def create_item(item: Item):
    return jsonify(item.model_dump())


@app.put("/items/<item_id>")
@parameter_validator
def update_item(item_id: int = Path(), item: Item = Body(embed=True)):
    results = {"item_id": item_id, "item": item.model_dump()}
    return results


def test_body_float():
    response = client.post("/items/", json={"name": "Foo", "price": 50.5})
    assert response.status_code == 200
    assert response.get_json() == {
        "name": "Foo",
        "price": 50.5,
        "description": None,
        "tax": None,
    }


def test_post_with_str_float():
    response = client.post("/items/", json={"name": "Foo", "price": "50.5"})
    assert response.status_code == 200
    assert response.get_json() == {
        "name": "Foo",
        "price": 50.5,
        "description": None,
        "tax": None,
    }


def test_post_with_str_float_description():
    response = client.post(
        "/items/", json={"name": "Foo", "price": "50.5", "description": "Some Foo"}
    )
    assert response.status_code == 200
    assert response.get_json() == {
        "name": "Foo",
        "price": 50.5,
        "description": "Some Foo",
        "tax": None,
    }


def test_post_with_str_float_description_tax():
    response = client.post(
        "/items/",
        json={"name": "Foo", "price": "50.5", "description": "Some Foo", "tax": 0.3},
    )
    assert response.status_code == 200
    assert response.get_json() == {
        "name": "Foo",
        "price": 50.5,
        "description": "Some Foo",
        "tax": 0.3,
    }


def test_post_with_only_name():
    response = client.post("/items/", json={"name": "Foo"})
    assert response.status_code == 422
    assert response.get_json() == {
        "detail": [
            {
                "type": "missing",
                "loc": ["body", "price"],
                "msg": "Field required",
                "input": {"name": "Foo"},
                "url": match_pydantic_error_url("missing"),
            }
        ]
    }


def test_post_with_only_name_price():
    response = client.post("/items/", json={"name": "Foo", "price": "twenty"})
    assert response.status_code == 422
    assert response.get_json() == {
        "detail": [
            {
                "type": "float_parsing",
                "loc": ["body", "price"],
                "msg": "Input should be a valid number, unable to parse string as a number",
                "input": "twenty",
                "url": match_pydantic_error_url("float_parsing"),
            }
        ]
    }


def test_post_with_no_data():
    response = client.post("/items/", json={})
    assert response.status_code == 422
    assert response.get_json() == {
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
    }


def test_post_with_none():
    response = client.post("/items/", json=None)
    assert response.status_code == 422
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


def test_wrong_headers():
    data = '{"name": "Foo", "price": 50.5}'
    response = client.post("/items/", data=data, headers={"Content-Type": "text/plain"})
    assert response.status_code == 422, response.text
    assert response.get_json() == {
        "detail": [
            {
                "type": "model_attributes_type",
                "loc": ["body"],
                "msg": "Input should be a valid dictionary or object to extract fields from",
                "input": '{"name": "Foo", "price": 50.5}',
                "url": match_pydantic_error_url("model_attributes_type"),
            }
        ]
    }
    response = client.post(
        "/items/", data=data, headers={"Content-Type": "application/geo+json-seq"}
    )
    assert response.status_code == 422, response.text
    assert response.get_json() == {
        "detail": [
            {
                "type": "model_attributes_type",
                "loc": ["body"],
                "msg": "Input should be a valid dictionary or object to extract fields from",
                "input": '{"name": "Foo", "price": 50.5}',
                "url": match_pydantic_error_url("model_attributes_type"),
            }
        ]
    }
    response = client.post(
        "/items/", data=data, headers={"Content-Type": "application/not-really-json"}
    )
    assert response.status_code == 422, response.text
    assert response.get_json() == {
        "detail": [
            {
                "type": "model_attributes_type",
                "loc": ["body"],
                "msg": "Input should be a valid dictionary or object to extract fields from",
                "input": '{"name": "Foo", "price": 50.5}',
                "url": match_pydantic_error_url("model_attributes_type"),
            }
        ]
    }


def test_items_5():
    response = client.put("/items/5", json={"item": {"name": "Foo", "price": 3.0}})
    assert response.status_code == 200
    assert response.get_json() == {
        "item_id": 5,
        "item": {"name": "Foo", "price": 3.0, "description": None, "tax": None},
    }


def test_items_6():
    response = client.put(
        "/items/6",
        json={
            "item": {
                "name": "Bar",
                "price": 0.2,
                "description": "Some bar",
                "tax": "5.4",
            }
        },
    )
    assert response.status_code == 200
    assert response.get_json() == {
        "item_id": 6,
        "item": {
            "name": "Bar",
            "price": 0.2,
            "description": "Some bar",
            "tax": 5.4,
        },
    }


def test_invalid_price():
    response = client.put("/items/5", json={"item": {"name": "Foo", "price": -3.0}})
    assert response.status_code == 422
    assert response.get_json() == {
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
    }
