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

from flask_parameter_validator import params
from flask_parameter_validator.model import Dependant


class ParameterValidator:
    def __init__(self, call: Callable[..., Any]) -> None:
        self.call = call
        update_wrapper(self, call)
        self.dependant: Dependant = self.get_dependant()

    def update_field_info(self, field: params.FieldAdapter, param_name: str, param: inspect.Parameter):
        _field_info = field.field_info
        _field_info.title = param_name
        _field_info.default = param.default
        _field_info.annotation = param.annotation
        field.field_info = _field_info

    def get_dependant(self) -> Dependant:
        dependant = Dependant()
        func_signatures = inspect.signature(self.call)
        signature_params = func_signatures.parameters

        field: params.FieldAdapter
        for param_name, param in signature_params.items():
            if get_origin(param.annotation) is Annotated:
                annotated_param = get_args(param.annotation)
                type_annotation = annotated_param[0]
                field = annotated_param[1]
                if isinstance(field, params.Body):
                    self.update_field_info(field, param_name, param)
                    dependant.body_params[param_name] = field
                elif isinstance(field, params.Path):
                    self.update_field_info(field, param_name, param)
                    dependant.path_params[param_name] = field
                elif isinstance(field, params.Query):
                    self.update_field_info(field, param_name, param)
                    dependant.query_params[param_name] = field
            else:
                field = params.Body(title=param_name, default=param.default, annotation=param.annotation)
                dependant.body_params[param_name] = field
        return dependant

    def solve_path_params(self, path: Dict[str, Any]) -> Tuple[Dict[str, BaseModel], List[Union[Dict[str, Any], ErrorDetails]]]:
        solved: Dict[str, BaseModel] = {}
        errors: List[Union[Dict[str, Any], ErrorDetails]] = []
        loc: Tuple[str, ...]
        for param_name, param in self.dependant.path_params.items():
            loc = (
                "path",
                param_name,
            )
            _received_path = path.get(param_name)
            if not _received_path:
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

            validated_param, _errors = param.validate(_received_path, loc=loc)
            if _errors:
                errors.extend(_errors)
            if validated_param:
                solved[param_name] = validated_param
        return solved, errors

    def solve_query_params(self, query: Dict[str, Any]) -> Tuple[Dict[str, BaseModel], List[Union[Dict[str, Any], ErrorDetails]]]:
        solved: Dict[str, BaseModel] = {}
        errors: List[Union[Dict[str, Any], ErrorDetails]] = []
        loc: Tuple[str, ...]
        for param_name, param in self.dependant.query_params.items():
            loc = (
                "query",
                param_name,
            )
            _received_path = query.get(param_name)
            if not _received_path:
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

            validated_param, _errors = param.validate(_received_path, loc=loc)
            if _errors:
                errors.extend(_errors)
            if validated_param:
                solved[param_name] = validated_param
        return solved, errors

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

    def solve_dependencies(self) -> Tuple[Dict[str, BaseModel], List[Union[Dict[str, Any], ErrorDetails]]]:
        path: Dict[str, Any] = request.view_args or {}
        query: Dict[Any, Any] = request.args or {}
        received_body: Dict[str, Any] = request.json or {}
        # form_data: Dict[str, Any] = request.form or {}
        # files: Dict[str, Any] = request.files or {}

        solved: Dict[str, BaseModel] = {}
        errors: List[Union[Dict[str, Any], ErrorDetails]] = []

        _params, _errors = self.solve_path_params(path)
        errors.extend(_errors)
        solved.update(_params)

        _params, _errors = self.solve_body(received_body)
        errors.extend(_errors)
        solved.update(_params)

        _params, _errors = self.solve_query_params(query)
        errors.extend(_errors)
        solved.update(_params)

        return solved, errors

    def __call__(self, *args, **kwargs):
        solved, errors = self.solve_dependencies()
        if errors:
            return Response(json.dumps({"detail": errors}), status=422, mimetype="application/json")
        return self.call(**solved)

    def __repr__(self):
        return repr(self.call)


def parameter_validator(func):
    return ParameterValidator(func)
