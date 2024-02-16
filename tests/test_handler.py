from flask import Flask, Response, jsonify

from flask_request_data_validator import (
    RequestValidationError,
    exception_handler,
    parameter_validator,
    request_vaildation_error,
)

app = Flask(__name__)
client = app.test_client()


def new_handler(exc: RequestValidationError):
    return Response("handler test")


@app.post("/foo")
@parameter_validator
def create_item(foo: int):
    return jsonify({"foo": foo})


def test_new_handler():
    exception_handler[RequestValidationError] = new_handler
    response = client.post("/foo", json={"foo": "bar"})
    assert response.status_code == 200
    assert response.get_data() == b"handler test"
    exception_handler[RequestValidationError] = request_vaildation_error
