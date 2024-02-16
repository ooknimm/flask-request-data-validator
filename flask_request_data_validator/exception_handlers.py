import json
from typing import Any, Callable, Dict

from flask import Response

from flask_request_data_validator.exceptions import (
    InternalServerError,
    RequestValidationError,
)
from flask_request_data_validator.utils import ResponseEncoder


def request_vaildation_error(exc: RequestValidationError):
    return Response(
        json.dumps({"detail": exc.errors}, cls=ResponseEncoder),
        status=422,
        mimetype="application/json",
    )


def internal_server_error(exc: Exception):
    return Response(
        json.dumps({"detail": "Internal Server Error"}),
        status=500,
        mimetype="application/json",
    )


exception_handler: Dict[Any, Callable[[Any], Response]] = {
    RequestValidationError: request_vaildation_error,
    InternalServerError: internal_server_error,
}
