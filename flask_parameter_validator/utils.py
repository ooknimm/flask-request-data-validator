import json
from typing import Any


class ResponseEncoder(json.JSONEncoder):
    def default(self, o: Any) -> str:
        if isinstance(o, bytes):
            return o.decode()
        return super().encode(o)
