import json
import types
from collections import deque
from dataclasses import is_dataclass
from typing import (
    Any,
    Deque,
    FrozenSet,
    List,
    Mapping,
    Sequence,
    Set,
    Tuple,
    Union,
    get_args,
    get_origin,
)

from pydantic import BaseModel
from pydantic._internal._utils import lenient_issubclass as lenient_issubclass
from werkzeug.datastructures import FileStorage

UnionType = getattr(types, "UnionType", Union)


class ResponseEncoder(json.JSONEncoder):
    def default(self, o: Any) -> str:
        if isinstance(o, bytes):
            return o.decode()
        return super().encode(o)


sequence_annotation_to_type = {
    Sequence: list,
    List: list,
    list: list,
    Tuple: tuple,
    tuple: tuple,
    Set: set,
    set: set,
    FrozenSet: frozenset,
    frozenset: frozenset,
    Deque: deque,
    deque: deque,
}

sequence_types = tuple(sequence_annotation_to_type.keys())


def __is_union_type(annotation) -> bool:
    return annotation is Union or annotation is UnionType


def __annotation_is_sequence(annotation) -> bool:
    if lenient_issubclass(annotation, (str, bytes)):
        return False
    return lenient_issubclass(annotation, sequence_types)


def __annotation_is_complex(annotation) -> bool:
    return lenient_issubclass(
        annotation,
        (BaseModel, Mapping, FileStorage)
        or __annotation_is_sequence(annotation)
        or is_dataclass(annotation),
    )


def __any_of_annotation_is_complex(annotation) -> bool:
    origin = get_origin(annotation)
    if __is_union_type(origin):
        return any(__any_of_annotation_is_complex(arg) for arg in get_args(annotation))
    return (
        __annotation_is_complex(annotation)
        or __annotation_is_complex(origin)
        or hasattr(origin, "__pydantic_core_schema__")
        or hasattr(origin, "__get_pydantic_core_schema__")
    )


def __annotation_is_scalar(annotation) -> bool:
    return annotation is Ellipsis or not __any_of_annotation_is_complex(annotation)


def __any_of_annotation_is_sequence(annotation) -> bool:
    return __annotation_is_sequence(annotation) or __annotation_is_sequence(
        get_origin(annotation)
    )


def annotation_is_sequence(annotation: Any) -> bool:
    origin = get_origin(annotation)
    if __is_union_type(origin):
        at_least_one_sequence = False
        for arg in get_args(annotation):
            if annotation_is_sequence(arg):
                at_least_one_sequence = True
                continue
            elif not __annotation_is_scalar(arg):
                return False
        return at_least_one_sequence
    return __any_of_annotation_is_sequence(annotation) and all(
        __annotation_is_scalar(arg) for arg in get_args(annotation)
    )


def is_file_or_nonable_file_annotation(annotation: Any) -> bool:
    if lenient_issubclass(annotation, FileStorage):
        return True
    origin = get_origin(annotation)
    if origin is Union or origin is UnionType:
        for arg in get_args(annotation):
            if lenient_issubclass(arg, FileStorage):
                return True
    return False


def annotation_is_file_sequence(annotation: Any) -> bool:
    origin = get_origin(annotation)
    if origin is Union or origin is UnionType:
        at_least_one = False
        for arg in get_args(annotation):
            if annotation_is_file_sequence(arg):
                at_least_one = True
                continue
        return at_least_one
    return __any_of_annotation_is_sequence(annotation) and all(
        is_file_or_nonable_file_annotation(sub_annotation)
        for sub_annotation in get_args(annotation)
    )
