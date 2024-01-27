import inspect
import json
from functools import update_wrapper
from typing import (
    Annotated,
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
    Union,
    get_args,
    get_origin,
)

import werkzeug.exceptions
from flask import Response, request
from pydantic import BaseModel, ValidationError
from pydantic_core import ErrorDetails, PydanticUndefined
from werkzeug.datastructures import Headers

from flask_parameter_validator import _params
from flask_parameter_validator.dependant import Dependant
from flask_parameter_validator.utils import ResponseEncoder


class ParameterValidator:
    def __init__(self, call: Callable[..., Any]) -> None:
        self._call = call
        update_wrapper(self, call)
        self.dependant: Dependant = self._get_dependant()

    def _update_field_info(
        self, field: _params.FieldAdapter, param_name: str, param: inspect.Parameter
    ):
        _field_info = field.field_info
        _field_info.title = param_name
        if _field_info.default == PydanticUndefined:
            _field_info.default = param.default
        _field_info.annotation = param.annotation
        field.field_info = _field_info

    def _update_params(
        self,
        dependant: Dependant,
        param_name: str,
        param: inspect.Parameter,
        field: _params.FieldAdapter,
    ) -> None:
        if isinstance(field, _params.Body) or isinstance(field, _params.Form):
            self._update_field_info(field, param_name, param)
            dependant.body_params[param_name] = field
        elif isinstance(field, _params.Path):
            self._update_field_info(field, param_name, param)
            dependant.path_params[param_name] = field
        elif isinstance(field, _params.Query):
            self._update_field_info(field, param_name, param)
            dependant.query_params[param_name] = field
        elif isinstance(field, _params.Header):
            self._update_field_info(field, param_name, param)
            dependant.header_params[param_name] = field
        elif isinstance(field, _params.File):
            self._update_field_info(field, param_name, param)
            dependant.file_params[param_name] = field

    def _get_dependant(self) -> Dependant:
        dependant = Dependant()
        func_signatures = inspect.signature(self._call)
        signature_params = func_signatures.parameters

        field: _params.FieldAdapter
        for param_name, param in signature_params.items():
            if get_origin(param.annotation) is Annotated:
                annotated_param = get_args(param.annotation)
                # type_annotation = annotated_param[0]
                field = annotated_param[1]
            elif isinstance(param.default, _params.FieldAdapter):
                field = param.default
            elif param.annotation is inspect._empty:
                continue
            else:
                field = _params.Body(
                    title=param_name,
                    default=param.default,
                    annotation=param.annotation,
                )
            self._update_params(
                dependant=dependant,
                param_name=param_name,
                param=param,
                field=field,
            )
        return dependant

    def _solve_dependencies(
        self,
    ) -> Tuple[Dict[str, BaseModel], List[Union[Dict[str, Any], ErrorDetails]]]:
        solved_params: Dict[str, BaseModel] = {}
        errors: List[Union[Dict[str, Any], ErrorDetails]] = []

        headers: Headers = request.headers
        _params, _errors = self.dependant.solve_header_params(headers)
        errors.extend(_errors)
        solved_params.update(_params)

        path: Dict[str, Any] = request.view_args or {}
        _params, _errors = self.dependant.solve_path_params(path)
        errors.extend(_errors)
        solved_params.update(_params)

        query: Dict[str, str] = request.args or {}
        _params, _errors = self.dependant.solve_query_params(query)
        errors.extend(_errors)
        solved_params.update(_params)

        files: Dict[str, Any] = request.files or {}
        _params, _errors = self.dependant.solve_file_params(files)
        errors.extend(_errors)
        solved_params.update(_params)

        if self.dependant.body_params:
            received_body: Union[Dict[str, str], bytes, None] = None
            if self.dependant.is_form_type:
                received_body = dict(request.form)
            else:
                body_bytes = request.get_data()
                if body_bytes and not request.content_type or request.is_json:
                    json_body = request.get_json(silent=True)
                    if json_body is not None:
                        received_body = json_body
                    else:
                        try:
                            json_body = json.loads(body_bytes.decode())
                            received_body = json_body
                        except json.JSONDecodeError as e:
                            validation_error = {
                                "type": "json_invalid",
                                "loc": ("body", e.pos),
                                "msg": "JSON decode error",
                                "input": {},
                                "ctx": {"error": e.msg},
                            }
                            errors.append(validation_error)
                            return solved_params, errors
                if received_body is None and body_bytes:
                    received_body = body_bytes

            _params, _errors = self.dependant.solve_body(received_body)
            errors.extend(_errors)
            solved_params.update(_params)
        return solved_params, errors

    def __call__(self, *args, **kwargs):
        solved, errors = self._solve_dependencies()
        if errors:
            return Response(
                json.dumps({"detail": errors}, cls=ResponseEncoder),
                status=422,
                mimetype="application/json",
            )
        return self._call(*args, **{**kwargs, **solved})

    def __repr__(self):
        return repr(self._call)


def parameter_validator(func):
    return ParameterValidator(func)
