import copy
import inspect
import json
from functools import update_wrapper
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Callable,
    Dict,
    List,
    NewType,
    Optional,
    Tuple,
    Type,
    TypeAlias,
    TypeVar,
    Union,
    cast,
    get_args,
    get_origin,
)

from flask import Response, jsonify, request
from pydantic import BaseModel, RootModel, TypeAdapter, create_model, validator
from pydantic_core import (
    ErrorDetails,
    PydanticUndefined,
    SchemaValidator,
    ValidationError,
    core_schema,
)

from flask_parameter_validator import _params
from flask_parameter_validator.model import Dependant

JSON_TYPE = ["application/json"]

ParamType = TypeVar("ParamType", bound=_params.FieldAdapter)


class ParameterValidator:
    def __init__(self, call: Callable[..., Any]) -> None:
        self.call = call
        update_wrapper(self, call)
        self.dependant: Dependant = self.get_dependant()

    def update_field_info(self, field: _params.FieldAdapter, param_name: str, param: inspect.Parameter):
        _field_info = field.field_info
        _field_info.title = param_name
        if _field_info.default == PydanticUndefined:
            _field_info.default = param.default
        _field_info.annotation = param.annotation
        field.field_info = _field_info

    def get_dependant(self) -> Dependant:
        dependant = Dependant()
        func_signatures = inspect.signature(self.call)
        signature_params = func_signatures.parameters

        field: _params.FieldAdapter
        for param_name, param in signature_params.items():
            if get_origin(param.annotation) is Annotated:
                annotated_param = get_args(param.annotation)
                type_annotation = annotated_param[0]
                field = annotated_param[1]
                if isinstance(field, _params.Body):
                    self.update_field_info(field, param_name, param)
                    dependant.body_params[param_name] = field
                elif isinstance(field, _params.Path):
                    self.update_field_info(field, param_name, param)
                    dependant.path_params[param_name] = field
                elif isinstance(field, _params.Query):
                    self.update_field_info(field, param_name, param)
                    dependant.query_params[param_name] = field
                elif isinstance(field, _params.Header):
                    self.update_field_info(field, param_name, param)
                    dependant.header_params[param_name] = field
            else:
                field = _params.Body(title=param_name, default=param.default, annotation=param.annotation)
                dependant.body_params[param_name] = field
        return dependant

    def solve_body(self, received_body: Dict[str, Any]) -> Tuple[Dict[str, BaseModel], List[Union[Dict[str, Any], ErrorDetails]]]:
        solved: Dict[str, BaseModel] = {}
        errors: List[Union[Dict[str, Any], ErrorDetails]] = []
        loc: Tuple[str, ...]
        # TODO embed, required param
        param_alias_omitted = len(self.dependant.body_params) == 1
        if param_alias_omitted:
            key = next(iter(self.dependant.body_params.keys()))
            received_body = {key: received_body}

        for param_name, param in self.dependant.body_params.items():
            loc = (
                "body",
                param_name,
            )
            _received_body = received_body.get(param_name)
            if not _received_body:
                if param.default is inspect.Signature.empty:
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
                    errors.append(error)
                    break
                else:
                    solved[param_name] = param.default
                    continue

            validated_param, _errors = param.validate(_received_body, loc=loc)
            if _errors:
                errors.extend(_errors)
            if validated_param:
                solved[param_name] = validated_param
        return solved, errors

    def solve_params(
        self,
        received_params: Dict[str, Any],
        params: Dict[str, ParamType],
    ) -> Tuple[Dict[str, BaseModel], List[Union[Dict[str, Any], ErrorDetails]]]:
        solved: Dict[str, BaseModel] = {}
        errors: List[Union[Dict[str, Any], ErrorDetails]] = []
        for param_name, param in params.items():
            _param_name = param_name
            if isinstance(param, _params.Header):
                _param_name = param_name.replace("_", "-")
            loc: Tuple[str, ...] = (param.__class__.__qualname__.lower(), _param_name)
            _received_param = received_params.get(param_name)
            if not _received_param:
                if param.default is inspect.Signature.empty:
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
                    errors.append(error)
                    break
                else:
                    solved[param_name] = param.default
                    continue

            vallidated_param, _errors = param.validate(_received_param, loc=loc)
            if _errors:
                errors.extend(_errors)
            if vallidated_param:
                solved[param_name] = vallidated_param
        return solved, errors

    def solve_dependencies(self) -> Tuple[Dict[str, BaseModel], List[Union[Dict[str, Any], ErrorDetails]]]:
        path: Dict[str, Any] = request.view_args or {}
        query: Dict[Any, Any] = request.args or {}
        headers: Dict[str, Any] = request.headers
        # form_data: Dict[str, Any] = request.form or {}
        # files: Dict[str, Any] = request.files or {}
        received_body: Dict[str, Any] = {}
        media_type = headers.get("content-type")
        if media_type in JSON_TYPE:
            received_body = request.json or {}

        solved_params: Dict[str, BaseModel] = {}
        errors: List[Union[Dict[str, Any], ErrorDetails]] = []

        _params, _errors = self.solve_params(headers, self.dependant.header_params)
        errors.extend(_errors)
        solved_params.update(_params)

        _params, _errors = self.solve_params(path, self.dependant.path_params)
        errors.extend(_errors)
        solved_params.update(_params)

        _params, _errors = self.solve_params(query, self.dependant.query_params)
        errors.extend(_errors)
        solved_params.update(_params)

        _params, _errors = self.solve_body(received_body)
        errors.extend(_errors)
        solved_params.update(_params)

        return solved_params, errors

    def __call__(self, *args, **kwargs):
        solved, errors = self.solve_dependencies()
        if errors:
            return Response(json.dumps({"detail": errors}), status=422, mimetype="application/json")
        return self.call(*args, **{**kwargs, **solved})

    def __repr__(self):
        return repr(self.call)


def parameter_validator(func):
    return ParameterValidator(func)
