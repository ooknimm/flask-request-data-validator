from typing import Annotated, Optional

import pytest
from flask import Flask, jsonify

from flask_parameter_validator import Body, Path, Query, parameter_validator
from tests.conftest import User

app = Flask(__name__)
client = app.test_client()


@app.post("/multiple/<id>")
@parameter_validator
def post_multiple(
    user: User,
    importance: Annotated[int, Body()],
    id: Annotated[int, Path()],
    q1: Annotated[str, Query()],
    q2: Annotated[Optional[str], Query()] = None,
):
    return jsonify({"user": user.model_dump(), "importance": importance, "id": id, "q1": q1, "q2": q2})


@pytest.mark.parametrize(
    "path,body,expected_status,expected_response",
    [
        (
            "/multiple/1?q1=bar",
            {"user": {"name": "Foo", "address": "seoul"}, "importance": "1"},
            200,
            {"id": 1, "importance": 1, "q1": "bar", "q2": None, "user": {"address": "seoul", "name": "Foo"}},
        ),
        (
            "/multiple/1?q1=bar&q2=bar2",
            {"user": {"name": "Foo", "address": "seoul"}, "importance": "1"},
            200,
            {"id": 1, "importance": 1, "q1": "bar", "q2": "bar2", "user": {"address": "seoul", "name": "Foo"}},
        ),
    ],
)
def test_form_data(path, body, expected_status, expected_response):
    response = client.post(path, json=body)
    assert response.status_code == expected_status
    assert response.get_json() == expected_response
