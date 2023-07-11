import inspect
from typing import Any, Callable, Annotated
from pydantic.fields import FieldInfo
from pydantic import create_model
from typing import get_args
from functools import update_wrapper
from flask import request
from flask_parameter_validator import params


class ParameterValidator:
    def __init__(self, call: Callable[..., Any]):
        self.call = call
        update_wrapper(self, call)
        self.get_dependant()
    
    def analyze_param(param_name, annotation, default):
        pass



    def get_dependant(self):
        func_signatures = inspect.signature(self.call)
        signature_params = func_signatures.parameters
        for param_name, param in signature_params.items():
            self.analyze_param(
                param_name=param_name,
                annotation=param.annotation,
                default=param.default
            )

    def solve_dependencies(self):
        # request.url_rule
        # path = request.view_args
        # query = request.args
        # data = request.json
        # form_data = request.form
        # files = request.files
        pass    
    
    def __call__(self, *args, **kwargs):
        try:
            self.solve_dependencies()
        except Exception as e:
            print(e)

        return self.call(*args, **kwargs)
    
    def __repr__(self):
        return repr(self.call)


def parameter_validator(func):
    return ParameterValidator(func)