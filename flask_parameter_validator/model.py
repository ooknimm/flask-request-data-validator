from typing import Dict, List, Optional, Type

from flask_parameter_validator.params import FieldAdapter


class Dependant:
    def __init__(
        self,
        *,
        path_parmas: Optional[Dict[str, FieldAdapter]] = None,
        query_params: Optional[Dict[str, FieldAdapter]] = None,
        header_params: Optional[Dict[str, FieldAdapter]] = None,
        cookie_params: Optional[Dict[str, FieldAdapter]] = None,
        body_params: Optional[Dict[str, FieldAdapter]] = None,
    ):
        self.path_params = path_parmas or {}
        self.query_params = query_params or {}
        self.header_params = header_params or {}
        self.cookie_params = cookie_params or {}
        self.body_params = body_params or {}
