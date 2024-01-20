import inspect
import json
from functools import update_wrapper
from typing import (
    Annotated,
    Any,
    Callable,
    Dict,
    List,
    Tuple,
    Union,
    get_args,
    get_origin,
)

from flask import Response, request
from pydantic import BaseModel
from pydantic_core import ErrorDetails, PydanticUndefined

from flask_parameter_validator import _params
from flask_parameter_validator.dependant import Dependant


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
            else:
                if param.annotation is inspect._empty:
                    continue
                field = _params.Body(
                    title=param_name, default=param.default, annotation=param.annotation
                )
                dependant.body_params[param_name] = field
        return dependant

    def _solve_dependencies(
        self,
    ) -> Tuple[Dict[str, BaseModel], List[Union[Dict[str, Any], ErrorDetails]]]:
        solved_params: Dict[str, BaseModel] = {}
        errors: List[Union[Dict[str, Any], ErrorDetails]] = []

        headers: Dict[str, Any] = request.headers
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
            if self.dependant.is_form_type:
                received_body = dict(request.form)
            else:
                received_body = request.json or {}
            _params, _errors = self.dependant.solve_body(received_body)
            errors.extend(_errors)
            solved_params.update(_params)

        return solved_params, errors

    def __call__(self, *args, **kwargs):
        solved, errors = self._solve_dependencies()
        if errors:
            return Response(
                json.dumps({"detail": errors}), status=422, mimetype="application/json"
            )
        return self._call(*args, **{**kwargs, **solved})

    def __repr__(self):
        return repr(self._call)


def parameter_validator(func):
    return ParameterValidator(func)
