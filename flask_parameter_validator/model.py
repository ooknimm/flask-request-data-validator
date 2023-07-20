from typing import Dict, Optional

from flask_parameter_validator._params import Body, FieldAdapter, Header, Path, Query


class Dependant:
    def __init__(
        self,
        *,
        path_parmas: Optional[Dict[str, Path]] = None,
        query_params: Optional[Dict[str, Query]] = None,
        header_params: Optional[Dict[str, Header]] = None,
        cookie_params: Optional[Dict[str, FieldAdapter]] = None,
        body_params: Optional[Dict[str, Body]] = None,
    ):
        self.path_params = path_parmas or {}
        self.query_params = query_params or {}
        self.header_params = header_params or {}
        self.cookie_params = cookie_params or {}
        self.body_params = body_params or {}
