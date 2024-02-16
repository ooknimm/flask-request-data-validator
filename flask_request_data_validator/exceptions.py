from typing import Any, Dict, List

from pydantic_core import ErrorDetails


class RequestValidationError(Exception):
    def __init__(self, errors: List[Dict[str, Any] | ErrorDetails]) -> None:
        super().__init__()
        self.errors = errors


class InternalServerError(Exception):
    pass
