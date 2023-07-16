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


@pytest.mark.parametrize(
    "path,body,expected_status,expected_response",
    [("/users?q=query_string", {"name": "nick", "address": "seoul"}, 200, {"name": "nick", "address": "seoul", "q": "query_string"})],
)
def test_query_string_param(path, body, expected_status, expected_response):
    response = client.post(path, json=body)
    assert response.status_code == expected_status
    assert response.get_json() == expected_response
