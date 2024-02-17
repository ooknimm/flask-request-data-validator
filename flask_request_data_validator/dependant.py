import inspect
from typing import Any, Dict, List, Optional, Tuple, TypeVar, Union

from pydantic import BaseModel, ValidationError
from pydantic_core import ErrorDetails, PydanticUndefined
from werkzeug.datastructures import FileStorage, Headers, MultiDict

from flask_request_data_validator._params import (
    Body,
    Cookie,
    FieldAdapter,
    File,
    Form,
    Header,
    Path,
    Query,
)

ParamType = TypeVar("ParamType", bound=FieldAdapter)


class Dependant:
    def __init__(
        self,
        *,
        path_parmas: Optional[Dict[str, Path]] = None,
        query_params: Optional[Dict[str, Query]] = None,
        header_params: Optional[Dict[str, Header]] = None,
        body_params: Optional[Dict[str, Body]] = None,
        file_params: Optional[Dict[str, File]] = None,
        cookie_params: Optional[Dict[str, Cookie]] = None,
    ):
        self.path_params = path_parmas or {}
        self.query_params = query_params or {}
        self.header_params = header_params or {}
        self.body_params = body_params or {}
        self.file_params = file_params or {}
        self.cookie_params = cookie_params or {}

    @property
    def is_form_type(self) -> bool:
        return any(
            param for param in self.body_params.values() if isinstance(param, Form)
        )

    def solve_body(
        self, received_body: Optional[Union[Dict[str, Any], bytes]]
    ) -> Tuple[Dict[str, BaseModel], List[Union[Dict[str, Any], ErrorDetails]]]:
        solved: Dict[str, BaseModel] = {}
        errors: List[Union[Dict[str, Any], ErrorDetails]] = []
        if not self.body_params:
            return solved, errors
        key = next(iter(self.body_params.keys()))
        embed = getattr(self.body_params[key], "embed", False)
        param_alias_omitted = len(self.body_params) == 1 and not embed
        if param_alias_omitted:
            received_body = {key: received_body}

        for param_name, param in self.body_params.items():
            loc: Tuple[str, ...]
            if param_alias_omitted:
                loc = ("body",)
            else:
                loc = (
                    "body",
                    param_name,
                )
            value: Optional[Any] = None
            if received_body is not None:
                try:
                    if isinstance(received_body, dict):
                        value = received_body.get(param_name)
                    else:
                        raise AttributeError
                except AttributeError:
                    error = ValidationError.from_exception_data(
                        "Field required",
                        [
                            {
                                "type": "missing",
                                "loc": loc,
                                "input": {},
                            }
                        ],
                    ).errors()[0]
                    error["input"] = None
                    errors.append(error)
                    continue
            if value is None:
                if param.default in (inspect.Signature.empty, PydanticUndefined):
                    error = ValidationError.from_exception_data(
                        "Field required",
                        [
                            {
                                "type": "missing",
                                "loc": loc,
                                "input": {},
                            }
                        ],
                    ).errors()[0]
                    error["input"] = None
                    errors.append(error)
                else:
                    solved[param_name] = param.default
                    continue
            else:
                validated_param, _errors = param.validate(value, loc=loc)
                if _errors:
                    errors.extend(_errors)
                if validated_param:
                    solved[param_name] = validated_param
        return solved, errors

    def _solve_params(
        self,
        received_params: Union[Dict[str, Any], Headers, MultiDict[str, Any]],
        params: Dict[str, ParamType],
    ) -> Tuple[Dict[str, BaseModel], List[Union[Dict[str, Any], ErrorDetails]]]:
        solved: Dict[str, BaseModel] = {}
        errors: List[Union[Dict[str, Any], ErrorDetails]] = []
        for param_name, param in params.items():
            _param_name = param_name
            if isinstance(param, Header):
                _param_name = param_name.replace("_", "-")
            loc: Tuple[str, ...] = (param.loc, _param_name)
            _received_param: Any
            if (
                isinstance(received_params, (Headers, MultiDict))
                and param.annotation_is_sequence
            ):
                _received_param = received_params.getlist(_param_name)
            else:
                _received_param = received_params.get(_param_name)
            if not _received_param:
                if param.default in (inspect.Signature.empty, PydanticUndefined):
                    error = ValidationError.from_exception_data(
                        "Field required",
                        [
                            {
                                "type": "missing",
                                "loc": loc,
                                "input": None,
                            }
                        ],
                    ).errors()[0]
                    errors.append(error)
                    continue
                else:
                    solved[param_name] = param.default
                    continue

            vallidated_param, _errors = param.validate(_received_param, loc=loc)
            if _errors:
                errors.extend(_errors)
            if vallidated_param:
                solved[param_name] = vallidated_param
        return solved, errors

    def solve_header_params(
        self, headers: Headers
    ) -> Tuple[Dict[str, BaseModel], List[Union[Dict[str, Any], ErrorDetails]]]:
        return self._solve_params(headers, self.header_params)

    def solve_path_params(
        self, path: Dict[str, Any]
    ) -> Tuple[Dict[str, BaseModel], List[Union[Dict[str, Any], ErrorDetails]]]:
        return self._solve_params(path, self.path_params)

    def solve_query_params(
        self, query: MultiDict[str, Any]
    ) -> Tuple[Dict[str, BaseModel], List[Union[Dict[str, Any], ErrorDetails]]]:
        return self._solve_params(query, self.query_params)

    def solve_file_params(
        self, files: MultiDict[str, FileStorage]
    ) -> Tuple[Dict[str, BaseModel], List[Union[Dict[str, Any], ErrorDetails]]]:
        return self._solve_params(files, self.file_params)

    def solve_cookie_params(
        self, cookies: MultiDict[str, str]
    ) -> Tuple[Dict[str, BaseModel], List[Union[Dict[str, Any], ErrorDetails]]]:
        return self._solve_params(cookies, self.cookie_params)
